# N-BaIoT Botnet Detector API

## Project Overview
This project is a RESTful API designed to detect botnet attacks using machine learning. It specifically utilizes a **LightGBM** model trained on the N-BaIoT dataset. The application is built with **FastAPI** and includes **OpenTelemetry** integration for comprehensive tracing and logging.

While the project includes a PyTorch model definition (`app/model_definition.py`), the current active application (`app/main.py`) relies on the LightGBM model.

## Technologies
*   **Language:** Python 3.12
*   **Web Framework:** FastAPI, Uvicorn
*   **Machine Learning:** LightGBM, Scikit-learn (RobustScaler), Pandas, NumPy
*   **Observability:** OpenTelemetry (OTLP exporters for traces and logs)
*   **Containerization:** Docker (Multi-stage builds)
*   **Orchestration:** Kubernetes (Kustomize)

## Project Structure
*   `app/`: Main application source code.
    *   `main.py`: Application entry point and API route definitions.
    *   `model_definition.py`: PyTorch model architecture (currently unused by `main.py`).
    *   `saved_assets/`: Directory containing trained models (`.joblib`, `.pth`), scalers, and feature lists.
*   `k8s/`: Kubernetes manifests organized for Kustomize (base/overlays).
*   `notebooks/`: Jupyter notebooks used for data analysis and model training (`lightgbm.ipynb`, `main.ipynb`).
*   `Dockerfile`: Multi-stage Docker build definition.
*   `requirements.txt`: Python dependencies.

## Building and Running

### Local Development
1.  **Environment Setup:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
2.  **Run Application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    *   Access Swagger UI at `http://localhost:8000/docs`.

### Docker
1.  **Build Image:**
    ```bash
    docker build -t nbiot-detector .
    ```
2.  **Run Container:**
    ```bash
    docker run -p 8000:8000 nbiot-detector
    ```

### Kubernetes
The project uses Kustomize for deployment management.
1.  **Deploy to Production (Overlay):**
    ```bash
    kubectl apply -k k8s/overlays/prod
    ```

## Testing
The project uses `pytest` for testing.
```bash
pytest
```

## Configuration
The application uses environment variables for OpenTelemetry configuration:
*   `OTEL_SERVICE_NAME`: Service name (default: `nbiot-detector-api`)
*   `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`: OTLP Trace endpoint (default: `http://localhost:4318/v1/traces`)
*   `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`: OTLP Log endpoint (default: `http://localhost:4318/v1/logs`)

## Development Conventions
*   **ML Assets:** Models and scalers are loaded at startup via the FastAPI `lifespan` handler.
*   **Observability:** Traces and logs are automatically instrumented for FastAPI and standard Python logging.
