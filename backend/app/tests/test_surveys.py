"""Tests for the /surveys endpoints."""
API = "/api/v1/surveys"


class TestCreateSurvey:
    def test_create_text_survey(self, client):
        resp = client.post(API, json={
            "title": "Test nucléaire",
            "mode": "text",
            "input_text": "Le nucléaire est indispensable",
            "n_agents": 10,
            "seed": 42,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test nucléaire"
        assert data["mode"] == "text"
        assert data["status"] == "pending"
        assert data["n_agents"] == 10
        assert data["id"]

    def test_create_questionnaire_survey(self, client):
        resp = client.post(API, json={
            "title": "Questionnaire climat",
            "mode": "questionnaire",
            "n_agents": 5,
            "questions": [
                {"question_id": "q1", "type": "stance", "text": "Le climat se réchauffe"},
                {"question_id": "q2", "type": "likert", "text": "Importance du recyclage", "scale": [1, 2, 3, 4, 5]},
                {"question_id": "q3", "type": "mcq", "text": "Énergie préférée", "choices": ["Solaire", "Éolien", "Nucléaire"]},
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["mode"] == "questionnaire"

    def test_invalid_mode_rejected(self, client):
        resp = client.post(API, json={
            "title": "Bad",
            "mode": "invalid",
        })
        assert resp.status_code == 422

    def test_missing_title_rejected(self, client):
        resp = client.post(API, json={"mode": "text"})
        assert resp.status_code == 422


class TestListSurveys:
    def test_empty_list(self, client):
        resp = client.get(API)
        assert resp.status_code == 200
        data = resp.json()
        assert data["surveys"] == []
        assert data["count"] == 0

    def test_list_after_create(self, client):
        client.post(API, json={"title": "S1", "mode": "text", "input_text": "test"})
        client.post(API, json={"title": "S2", "mode": "text", "input_text": "test2"})
        resp = client.get(API)
        assert resp.status_code == 200
        assert resp.json()["count"] == 2


class TestGetSurvey:
    def test_get_existing(self, client):
        create = client.post(API, json={"title": "Get me", "mode": "text"})
        sid = create.json()["id"]
        resp = client.get(f"{API}/{sid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get me"

    def test_get_not_found(self, client):
        resp = client.get(f"{API}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestDeleteSurvey:
    def test_delete(self, client):
        create = client.post(API, json={"title": "Delete me", "mode": "text"})
        sid = create.json()["id"]
        resp = client.delete(f"{API}/{sid}")
        assert resp.status_code == 204


class TestSurveyAgents:
    def test_agents_empty_initially(self, client):
        create = client.post(API, json={"title": "No agents", "mode": "text"})
        sid = create.json()["id"]
        resp = client.get(f"{API}/{sid}/agents")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestSurveyResponses:
    def test_responses_empty_initially(self, client):
        create = client.post(API, json={"title": "No resp", "mode": "text"})
        sid = create.json()["id"]
        resp = client.get(f"{API}/{sid}/responses")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestSurveyAggregates:
    def test_aggregates_empty(self, client):
        create = client.post(API, json={"title": "No agg", "mode": "text"})
        sid = create.json()["id"]
        resp = client.get(f"{API}/{sid}/aggregates")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
