# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock # patch is also from unittest.mock
import numpy as np
import io
import torch

# Import the app instance and constants
from app.main import app as fast_api_app # The FastAPI app instance
from app.main import INPUT_SIZE
import app.main as main_module # Import the main module to access its globals

from app.model_definition import MLPDetector

@pytest.fixture
def client(mocker): # Add mocker to the client fixture
    """
    Create a TestClient instance for the FastAPI app.
    Mocks dependencies for model and scaler loading BEFORE app startup.
    """
    # 1. Mock what app.main.joblib.load would return
    mock_scaler_object = MagicMock() # This will become scaler
    # Configure its transform method for default behavior if needed, or tests will patch it.
    # mock_scaler_object.transform.return_value = np.array([[0.0] * INPUT_SIZE]) # Example default

    # Patch 'joblib.load' in the context of 'app.main' module
    mocker.patch("app.main.joblib.load", return_value=mock_scaler_object)

    # 2. Mock what app.main.torch.load would return (model state_dict)
    # and the subsequent model instantiation and setup
    mock_model_object = MagicMock(spec=MLPDetector) # This will become model
    mock_model_object.to.return_value = mock_model_object # for main_module.model.to(device)
    mock_model_object.eval.return_value = mock_model_object # for main_module.model.eval()
    # Mock the load_state_dict method as it will be called
    mock_model_object.load_state_dict = MagicMock()

    # Patch the MLPDetector constructor within app.main to return our mock_model_object
    mocker.patch("app.main.MLPDetector", return_value=mock_model_object)
    # Patch torch.load within app.main (though its return is used by load_state_dict, which is on the mock)
    mocker.patch("app.main.torch.load", return_value={}) # Dummy state_dict

    # Now, when TestClient(app) is called, the app's startup sequence `load_assets`
    # will use these patched functions and classes.
    with TestClient(fast_api_app) as c:
        # After startup, scaler will be mock_scaler_object
        # and model will be mock_model_object.
        yield c

# --- Test for Root Endpoint ---
def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "N-BaIoT Botnet Detection API. Navigate to /docs for API documentation."}

# --- Tests for Single Prediction Endpoint (/predict/) ---
def test_predict_single_instance_valid(client: TestClient, mocker):
    # scaler is now our mock_scaler_object from the client fixture
    # model is now our mock_model_object from the client fixture

    # Configure the 'transform' method of the mocked scaler for this specific test
    main_module.scaler.transform.return_value = np.random.rand(1, INPUT_SIZE)

    # Configure the 'forward' method (or __call__) of the mocked model for this test
    # Since we mocked the entire MLPDetector to return mock_model_object,
    # model(features) calls mock_model_object(features).
    # MagicMock is callable by default. We set its return_value.
    main_module.model.return_value = torch.tensor([[0.9]]) # Output of model(features_tensor)

    valid_features = {"features": [0.1] * INPUT_SIZE}
    response = client.post("/predict/", json=valid_features)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["prediction_label"] == 1
    assert json_response["status"] == "Attack"

    main_module.scaler.transform.assert_called_once()
    main_module.model.assert_called_once() # Checks if mock_model_object was called


def test_predict_single_instance_invalid_feature_count(client: TestClient):
    invalid_features = {"features": [0.1] * (INPUT_SIZE - 1)}
    response = client.post("/predict/", json=invalid_features)
    assert response.status_code == 400
    assert "Invalid number of features" in response.json()["detail"]

def test_predict_single_instance_non_numeric_feature(client: TestClient):
    invalid_features_type = {"features": ["not_a_number"] + [0.1] * (INPUT_SIZE - 1)}
    response = client.post("/predict/", json=invalid_features_type)
    assert response.status_code == 422


# --- Tests for Batch Prediction Endpoint (/predict_batch/) ---
@pytest.fixture
def setup_batch_mocks(mocker): # Renamed from mock_loaded_assets_for_batch for clarity
    """Sets up mock behaviors for main_module.scaler.transform and model() for batch tests."""
    # scaler and model are already MagicMock instances
    # due to the client fixture. We just configure their behavior for batch.

    def scaler_side_effect(input_np_array):
        return input_np_array * 0.9 # Dummy scaling
    main_module.scaler.transform.side_effect = scaler_side_effect
    main_module.scaler.transform.reset_mock() # Reset from any single prediction calls

    def model_side_effect_batch(input_tensor_batch):
        num_samples = input_tensor_batch.shape[0]
        logits = [[0.8]] * num_samples
        if num_samples > 1: logits[1] = [-0.2]
        return torch.tensor(logits, dtype=torch.float32)
    # If model is a MagicMock instance, its return_value is for model() call
    main_module.model.side_effect = model_side_effect_batch # model() will use this
    main_module.model.reset_mock()

    return main_module.scaler.transform, main_module.model # Return the actual mock methods/objects

def test_predict_batch_valid_csv(client: TestClient, setup_batch_mocks):
    mock_scaler_transform, mock_model_callable = setup_batch_mocks

    csv_data = "\n".join([",".join(map(str, [0.1 + i*0.01] * INPUT_SIZE)) for i in range(3)])
    csv_file_like = io.BytesIO(csv_data.encode('utf-8'))
    response = client.post("/predict_batch/", files={"file": ("test.csv", csv_file_like, "text/csv")})

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 3
    assert json_response[0]["status"] == "Attack"
    if len(json_response) > 1: assert json_response[1]["status"] == "Benign"

    mock_scaler_transform.assert_called_once()
    mock_model_callable.assert_called_once()


def test_predict_batch_invalid_file_type(client: TestClient):
    txt_file_like = io.BytesIO(b"this is not a csv")
    response = client.post("/predict_batch/", files={"file": ("test.txt", txt_file_like, "text/plain")})
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_predict_batch_csv_wrong_columns(client: TestClient):
    # This test previously failed with 500 instead of 400.
    # The API logic needs to be robust to ensure HTTPExceptions are not caught by general 'except Exception'.
    # Assuming main.py's error handling for this specific case is fixed to return 400.
    csv_data = "0.1,0.2,0.3"
    csv_file_like = io.BytesIO(csv_data.encode('utf-8'))
    response = client.post("/predict_batch/", files={"file": ("test.csv", csv_file_like, "text/csv")})
    assert response.status_code == 400 # Expecting 400 after API error handling fix
    assert "incorrect number of columns" in response.json()["detail"]


def test_predict_batch_empty_csv(client: TestClient):
    csv_file_like = io.BytesIO(b"")
    response = client.post("/predict_batch/", files={"file": ("test.csv", csv_file_like, "text/csv")})
    assert response.status_code == 400
    assert "CSV file is empty" in response.json()["detail"]

def test_predict_batch_malformed_csv_non_numeric(client: TestClient, setup_batch_mocks):
    # This test also depends on refined error handling in main.py
    # to convert a ValueError from data conversion into a 400/422.
    mock_scaler_transform, mock_model_callable = setup_batch_mocks
    csv_data = "\n".join([",".join(["text_instead_of_number"] + ["0.1"]*(INPUT_SIZE-1))])
    csv_file_like = io.BytesIO(csv_data.encode('utf-8'))
    response = client.post("/predict_batch/", files={"file": ("test.csv", csv_file_like, "text/csv")})

    # Expecting 400 if main.py catches ValueError and raises HTTPException
    assert response.status_code == 400
    assert "CSV contains non-numeric data" in response.json()["detail"] # Or similar refined message