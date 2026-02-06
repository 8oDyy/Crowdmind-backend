from fastapi.testclient import TestClient


def test_create_model(client: TestClient) -> None:
    response = client.post(
        "/api/v1/models",
        json={
            "name": "emotion-classifier",
            "version": "1.0.0",
            "target_device": "esp32",
            "labels": ["happy", "sad", "neutral"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "emotion-classifier"
    assert data["version"] == "1.0.0"
    assert data["target_device"] == "esp32"
    assert data["labels"] == ["happy", "sad", "neutral"]
    assert "id" in data
    assert data["storage_path"] is None
    assert data["checksum"] is None


def test_upload_model_file(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "upload-test", "version": "1.0"},
    )
    assert create_response.status_code == 201
    model_id = create_response.json()["id"]

    fake_tflite_content = b"fake tflite model content for testing"
    upload_response = client.post(
        f"/api/v1/models/{model_id}/upload",
        files={"file": ("model.tflite", fake_tflite_content, "application/octet-stream")},
    )
    assert upload_response.status_code == 200
    data = upload_response.json()
    assert data["model_id"] == model_id
    assert data["size"] == len(fake_tflite_content)
    assert "checksum" in data
    assert "storage_path" in data


def test_get_model(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "get-test-model", "version": "2.0"},
    )
    model_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/models/{model_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == model_id
    assert data["name"] == "get-test-model"


def test_get_model_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/models/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_download_url(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/models",
        json={"name": "download-test", "version": "1.0"},
    )
    model_id = create_response.json()["id"]

    fake_content = b"model bytes"
    client.post(
        f"/api/v1/models/{model_id}/upload",
        files={"file": ("model.tflite", fake_content, "application/octet-stream")},
    )

    download_response = client.get(
        f"/api/v1/models/{model_id}/download",
        params={"expires": 7200},
    )
    assert download_response.status_code == 200
    data = download_response.json()
    assert "url" in data
    assert "https://" in data["url"]
