# N-BaIoT Botnet Detector API

[![Python 3.14.3](https://img.shields.io/badge/python-3.14.3-blue.svg)](https://www.python.org/downloads/release/python-3143/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## Project Overview
This project is a RESTful API designed to detect botnet attacks using machine learning. It specifically utilizes a **LightGBM** model trained on the N-BaIoT dataset. The application is built with **FastAPI** and includes **OpenTelemetry** integration for comprehensive tracing and logging.

While the project includes a PyTorch model definition (`app/model_definition.py`), the current active application (`app/main.py`) relies on the LightGBM model.

## Technologies
*   **Language:** Python 3.14.3
*   **Web Framework:** FastAPI, Uvicorn
*   **Machine Learning:** LightGBM, Scikit-learn (RobustScaler), Pandas, NumPy
*   **Observability:** OpenTelemetry (OTLP exporters for traces and logs)
*   **Containerization:** Docker (Multi-stage builds)
*   **Orchestration:** Kubernetes (Kustomize)
*   **CI/CD:** GitHub Actions

## CI/CD Pipeline (GitHub Actions)
The project utilizes GitHub Actions for continuous integration and continuous deployment:
*   **Build & Push:** (`build_scan_push.yaml`) Builds the Docker image, scans it, and pushes it to the registry.
*   **GitOps Release:** (`release-gitops.yaml`) Updates Kubernetes manifests for deployment.
*   **Testing:** (`unit-test.yaml`) Runs the `pytest` test suite.
*   **Security:** Regular scans using Snyk (`synk-sca-scan.yaml`), Semgrep (`semgrep.yaml`), Gitleaks (`gitleaks.yaml`), and Kubesec (`kubesec.yaml`).

## Building and Running

### Local Development
1.  **Environment Setup (Conda - Recommended for Windows/Python 3.14+):**
    ```bash
    conda env create -f environment.yaml
    conda activate nbiot-detector
    ```

    *Alternative (Standard venv):*
    ```bash
    python -m venv venv
    # Linux/MacOS
    source venv/bin/activate
    # Windows
    venv\Scripts\activate
    
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
