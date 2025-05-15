from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
import joblib
import numpy as np
import pandas as pd
import io # For reading file in memory
import os
import torch


# Import the model class from model_definition.py
from model_definition import MLPDetector

# --- Configuration (must match training for architecture) ---
# These define the architecture of the loaded model
# Ensure these match the hyperparameters used when `best_nbiot_multi_device_detector.pth` was saved
INPUT_SIZE = 115
HIDDEN_SIZE_1 = 128
HIDDEN_SIZE_2 = 64
OUTPUT_SIZE = 1
DROPOUT_RATE = 0.3 # This was the rate used during training for the saved model

# Paths to saved assets (relative to main.py location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "saved_assets", "best_nbiot_detector.pth")
SCALER_PATH = os.path.join(BASE_DIR, "saved_assets", "nbiot_multi_device_scaler.gz")


app = FastAPI(
    title="N-BaIoT Botnet Detector API",
    description="API for detecting botnet attacks in IoT network traffic using a pre-trained MLP model.",
    version="1.0.0"
)

# Global variables for loaded model, scaler, and device
model: MLPDetector = None
scaler: joblib.numpy_pickle.NumpyPickler = None # More specific type hint if known, or just object
device: torch.device = None

# Pydantic model for input data validation
class NetworkFeaturesInput(BaseModel):
    features: List[float]

    class Config:
        json_schema_extra = {
            "example": {
                "features": [0.1] * INPUT_SIZE # Example with 115 features
            }
        }

class PredictionResponse(BaseModel):
    prediction_label: int
    status: str
    probability_attack: float


@app.on_event("startup")
async def load_assets():
    """
    Load the PyTorch model and the scikit-learn scaler on application startup.
    """
    global model, scaler, device

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load Scaler
    if not os.path.exists(SCALER_PATH):
        print(f"ERROR: Scaler file not found at {SCALER_PATH}")
        raise RuntimeError(f"Scaler file not found at {SCALER_PATH}")
    try:
        scaler = joblib.load(SCALER_PATH)
        print("Scaler loaded successfully.")
    except Exception as e:
        print(f"Error loading scaler: {e}")
        raise RuntimeError(f"Error loading scaler: {e}")

    # Load Model
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found at {MODEL_PATH}")
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    try:
        model = MLPDetector(INPUT_SIZE, HIDDEN_SIZE_1, HIDDEN_SIZE_2, OUTPUT_SIZE, DROPOUT_RATE)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()  # Set model to evaluation mode
        print("PyTorch model loaded successfully and set to evaluation mode.")
    except Exception as e:
        print(f"Error loading PyTorch model: {e}")
        raise RuntimeError(f"Error loading PyTorch model: {e}")

@app.post("/predict/", summary="Predict Botnet Attack")
async def predict_botnet(data: NetworkFeaturesInput):
    """
    Predicts if network traffic features indicate a botnet attack.

    - **features**: A list of 115 numerical network features.
    """
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model or scaler not loaded. Check server logs.")

    if len(data.features) != INPUT_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid number of features. Expected {INPUT_SIZE}, got {len(data.features)}"
        )

    try:
        # 1. Convert to NumPy array and reshape for scaler
        features_np = np.array(data.features).reshape(1, -1)

        # 2. Scale features using the loaded scaler
        scaled_features_np = scaler.transform(features_np)

        # 3. Convert to PyTorch tensor
        features_tensor = torch.tensor(scaled_features_np, dtype=torch.float32).to(device)

        # 4. Make prediction
        with torch.no_grad(): # Disable gradient calculations for inference
            output_logit = model(features_tensor)
            probability_attack = torch.sigmoid(output_logit).item() # Probability of being an attack (class 1)

        prediction_label = 1 if probability_attack > 0.5 else 0
        status_message = "Attack" if prediction_label == 1 else "Benign"

        return {
            "prediction_label": prediction_label,
            "status": status_message,
            "probability_attack": probability_attack
        }
    except Exception as e:
        print(f"Prediction error: {e}") # Log the error for server-side debugging
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict_batch/", response_model=List[PredictionResponse], summary="Predict Batch from CSV File")
async def predict_batch_from_csv(file: UploadFile = File(..., description="CSV file containing rows of 115 features per instance.")):
    if model is None or scaler is None:
        # This check is fine before the main try block
        raise HTTPException(status_code=503, detail="Model or scaler not loaded.")

    if not file.filename.endswith(".csv"):
        # This validation is also fine here
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        contents = await file.read()
        
        try:
            df = pd.read_csv(io.BytesIO(contents), header=None)
        except pd.errors.EmptyDataError:
            # Specific error for empty CSV
            raise HTTPException(status_code=400, detail="CSV file is empty.")
        except pd.errors.ParserError:
            # Specific error for CSV parsing issues
            raise HTTPException(status_code=400, detail="Error parsing CSV file. Ensure it's valid CSV with numerical data.")

        if df.shape[1] != INPUT_SIZE:
            # Specific error for wrong number of columns
            raise HTTPException(
                status_code=400,
                detail=f"CSV file has incorrect number of columns. Expected {INPUT_SIZE}, got {df.shape[1]}."
            )

        try:
            # Attempt to convert to NumPy array and then to float.
            # This is where non-numeric data would cause a ValueError.
            features_np_batch = df.values.astype(float)
        except ValueError:
            # Specific error for non-numeric data in CSV
            raise HTTPException(status_code=400, detail="CSV contains non-numeric data where numbers are expected.")

        # --- Core ML Processing ---
        # This part can also have its own try-except for unexpected ML errors,
        # though often, issues here might still be server-side (500).
        scaled_features_np_batch = scaler.transform(features_np_batch)
        features_tensor_batch = torch.tensor(scaled_features_np_batch, dtype=torch.float32).to(device)

        predictions_list = []
        with torch.no_grad():
            output_logits_batch = model(features_tensor_batch)
            probabilities_attack_batch = torch.sigmoid(output_logits_batch)

            for i in range(len(probabilities_attack_batch)):
                prob_attack = probabilities_attack_batch[i].item()
                label = 1 if prob_attack > 0.5 else 0
                status = "Attack" if label == 1 else "Benign"
                predictions_list.append(
                    PredictionResponse(
                        prediction_label=label,
                        status=status,
                        probability_attack=prob_attack
                    )
                )
        return predictions_list

    except HTTPException as http_exc:
        # If any of the above raised an HTTPException, re-raise it so FastAPI handles it correctly.
        raise http_exc
    except Exception as e:
        # Catch any other truly unexpected errors during the process.
        print(f"Unexpected batch prediction error (generic catch): {e}") # Log this for server debugging
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred during batch processing: {str(e)}")
    finally:
        if file and hasattr(file, 'close') and callable(file.close): # Check if file was defined and has close method
            await file.close()

@app.get("/", summary="Root Endpoint")
async def read_root():
    """
    Provides a welcome message for the API.
    """
    return {"message": "N-BaIoT Botnet Detection API. Navigate to /docs for API documentation."}

# To run this application:
# 1. Navigate to the 'nbiot_api/app/' directory in your terminal.
# 2. Run: uvicorn main:app --reload