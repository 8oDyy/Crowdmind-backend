from fastapi.testclient import TestClient


def test_create_dataset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets",
        json={
            "name": "test-dataset",
            "version": "1.0",
            "labels": ["positive", "negative"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-dataset"
    assert data["version"] == "1.0"
    assert data["labels"] == ["positive", "negative"]
    assert "id" in data
    assert "created_at" in data


def test_generate_rows(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/datasets",
        json={"name": "gen-dataset", "labels": ["a", "b", "c"]},
    )
    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    gen_response = client.post(
        f"/api/v1/datasets/{dataset_id}/generate",
        params={"n": 10, "seed": 42},
    )
    assert gen_response.status_code == 200
    data = gen_response.json()
    assert data["inserted"] == 10


def test_get_dataset(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/datasets",
        json={"name": "get-test", "version": "2.0"},
    )
    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == dataset_id
    assert data["name"] == "get-test"
    assert data["version"] == "2.0"


def test_get_dataset_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_export_dataset_jsonl(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/datasets",
        json={"name": "export-test", "labels": ["x", "y"]},
    )
    dataset_id = create_response.json()["id"]

    client.post(f"/api/v1/datasets/{dataset_id}/generate", params={"n": 5, "seed": 1})

    export_response = client.get(
        f"/api/v1/datasets/{dataset_id}/export",
        params={"format": "jsonl"},
    )
    assert export_response.status_code == 200
    assert "application/x-ndjson" in export_response.headers["content-type"]
