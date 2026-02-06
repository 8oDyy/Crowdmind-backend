from fastapi.testclient import TestClient


def test_create_model(client: TestClient) -> None:
    response = client.post(
        "/api/v1/models",
        json={
            "name": "emotion-classifier",
            "framework": "tflite",
            "description": "Emotion classification model",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "emotion-classifier"
    assert data["framework"] == "tflite"
    assert data["description"] == "Emotion classification model"
    assert "id" in data
    assert "created_at" in data


def test_create_model_version(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "upload-test", "framework": "tflite"},
    )
    assert create_response.status_code == 201
    model_id = create_response.json()["id"]

    fake_tflite_content = b"fake tflite model content for testing"
    upload_response = client.post(
        f"/api/v1/models/{model_id}/versions?version=1.0",
        files={"file": ("model.tflite", fake_tflite_content, "application/octet-stream")},
    )
    assert upload_response.status_code == 201
    data = upload_response.json()
    assert data["model_id"] == model_id
    assert data["version"] == "1.0"
    assert data["size_kb"] == len(fake_tflite_content) // 1024
    assert "checksum" in data
    assert "file_path" in data


def test_get_model(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "get-test-model", "framework": "tflite"},
    )
    model_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/models/{model_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == model_id
    assert data["name"] == "get-test-model"
    assert data["framework"] == "tflite"


def test_get_model_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/models/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_models(client: TestClient) -> None:
    client.post(
        "/api/v1/models",
        json={"name": "model-1", "framework": "tflite"},
    )
    client.post(
        "/api/v1/models",
        json={"name": "model-2", "framework": "edge_impulse"},
    )

    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_version_download_url(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "download-test", "framework": "tflite"},
    )
    model_id = create_response.json()["id"]

    fake_content = b"model bytes"
    version_response = client.post(
        f"/api/v1/models/{model_id}/versions?version=1.0",
        files={"file": ("model.tflite", fake_content, "application/octet-stream")},
    )
    version_id = version_response.json()["id"]

    download_response = client.get(
        f"/api/v1/models/versions/{version_id}/download",
        params={"expires": 7200},
    )
    assert download_response.status_code == 200
    data = download_response.json()
    assert "url" in data
    assert "https://" in data["url"]
