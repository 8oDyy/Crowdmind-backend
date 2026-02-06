from fastapi.testclient import TestClient


def test_create_dataset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets",
        json={
            "name": "test-dataset",
            "dataset_type": "synthetic",
            "created_by": "user-123",
            "description": "Test dataset",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-dataset"
    assert data["dataset_type"] == "synthetic"
    assert data["created_by"] == "user-123"
    assert "id" in data
    assert "created_at" in data


def test_get_dataset(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/datasets",
        json={
            "name": "get-test",
            "dataset_type": "scraped",
            "created_by": "user-456",
        },
    )
    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == dataset_id
    assert data["name"] == "get-test"
    assert data["dataset_type"] == "scraped"


def test_get_dataset_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_datasets(client: TestClient) -> None:
    client.post(
        "/api/v1/datasets",
        json={"name": "dataset-1", "dataset_type": "synthetic", "created_by": "user-1"},
    )
    client.post(
        "/api/v1/datasets",
        json={"name": "dataset-2", "dataset_type": "mixed", "created_by": "user-2"},
    )

    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
