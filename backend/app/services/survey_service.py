from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.domain.entities.survey import Survey
from app.domain.entities.survey_aggregate import SurveyAggregate
from app.repositories.agent_repo import AgentRepository
from app.repositories.response_repo import ResponseRepository
from app.repositories.survey_aggregate_repo import SurveyAggregateRepository
from app.repositories.survey_question_repo import SurveyQuestionRepository
from app.repositories.survey_question_response_repo import SurveyQuestionResponseRepository
from app.repositories.survey_repo import SurveyRepository

logger = get_logger(__name__)


class SurveyService:
    def __init__(
        self,
        survey_repo: SurveyRepository,
        agent_repo: AgentRepository,
        response_repo: ResponseRepository,
        aggregate_repo: SurveyAggregateRepository,
        question_repo: SurveyQuestionRepository,
        question_response_repo: SurveyQuestionResponseRepository,
    ):
        self._surveys = survey_repo
        self._agents = agent_repo
        self._responses = response_repo
        self._aggregates = aggregate_repo
        self._questions = question_repo
        self._question_responses = question_response_repo

    # ── CRUD ─────────────────────────────────────────────

    def create_survey(
        self,
        title: str,
        mode: str,
        input_text: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        n_agents: int = 100,
        seed: int = 42,
        parameters: dict[str, Any] | None = None,
        created_by: str | None = None,
        questions: list[dict[str, Any]] | None = None,
    ) -> Survey:
        survey = self._surveys.create_survey(
            title=title,
            mode=mode,
            input_text=input_text,
            model=model,
            n_agents=n_agents,
            seed=seed,
            parameters=parameters,
            created_by=created_by,
        )
        if questions and mode == "questionnaire":
            q_rows = []
            for idx, q in enumerate(questions):
                q_rows.append({
                    "survey_id": survey.id,
                    "question_index": idx,
                    "question_id": q.get("question_id", f"q{idx}"),
                    "type": q["type"],
                    "text": q["text"],
                    "choices": q.get("choices"),
                    "scale": q.get("scale"),
                })
            self._questions.create_questions_batch(q_rows)
        logger.info(f"Survey created: {survey.id} ({survey.mode})")
        return survey

    def get_survey(self, survey_id: str) -> Survey:
        return self._surveys.get_survey(survey_id)

    def list_surveys(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
    ) -> list[Survey]:
        return self._surveys.list_surveys(
            limit=limit, offset=offset, created_by=created_by,
        )

    def delete_survey(self, survey_id: str) -> None:
        self._surveys.delete_survey(survey_id)
        logger.info(f"Survey deleted: {survey_id}")

    # ── Status transitions ───────────────────────────────

    def mark_running(self, survey_id: str) -> Survey:
        return self._surveys.update_survey(survey_id, {
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        })

    def mark_completed(
        self,
        survey_id: str,
        elapsed_seconds: float,
    ) -> Survey:
        return self._surveys.update_survey(survey_id, {
            "status": "completed",
            "elapsed_seconds": elapsed_seconds,
            "completed_at": datetime.utcnow().isoformat(),
        })

    def mark_failed(self, survey_id: str) -> Survey:
        return self._surveys.update_survey(survey_id, {
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
        })

    # ── Agents ───────────────────────────────────────────

    def store_agents(
        self, survey_id: str, agents_data: list[dict[str, Any]]
    ) -> int:
        for a in agents_data:
            a["survey_id"] = survey_id
        self._agents.create_agents_batch(agents_data)
        return len(agents_data)

    def get_agents(self, survey_id: str) -> list:
        return self._agents.list_agents_by_survey(survey_id)

    # ── Responses (mode text) ────────────────────────────

    def store_responses(
        self, survey_id: str, responses: list[dict[str, Any]]
    ) -> int:
        for r in responses:
            r["survey_id"] = survey_id
        self._responses.create_responses_batch(responses)
        return len(responses)

    def get_responses(self, survey_id: str) -> list:
        return self._responses.list_responses_by_survey(survey_id)

    # ── Responses (mode questionnaire) ───────────────────

    def store_question_responses(
        self, survey_id: str, rows: list[dict[str, Any]]
    ) -> int:
        for r in rows:
            r["survey_id"] = survey_id
        self._question_responses.create_batch(rows)
        return len(rows)

    def get_question_responses(self, survey_id: str) -> list:
        return self._question_responses.list_by_survey(survey_id)

    def get_questions(self, survey_id: str) -> list:
        return self._questions.list_by_survey(survey_id)

    # ── Aggregation ──────────────────────────────────────

    def compute_and_store_aggregates(self, survey_id: str) -> list[SurveyAggregate]:
        survey = self._surveys.get_survey(survey_id)
        # Delete old aggregates
        self._aggregates.delete_by_survey(survey_id)

        results: list[SurveyAggregate] = []

        if survey.mode == "text":
            responses = self._responses.list_responses_by_survey(survey_id)
            agg = self._compute_text_aggregation(responses)
            result = self._aggregates.upsert_aggregate(
                survey_id=survey_id, aggregation=agg, question_id=None,
            )
            results.append(result)
        else:
            questions = self._questions.list_by_survey(survey_id)
            for q in questions:
                q_responses = self._question_responses.list_by_survey_and_question(
                    survey_id, q.question_id,
                )
                agg = self._compute_question_aggregation(q.type, q_responses)
                result = self._aggregates.upsert_aggregate(
                    survey_id=survey_id,
                    aggregation=agg,
                    question_id=q.question_id,
                )
                results.append(result)

        logger.info(f"Aggregates computed for survey {survey_id}: {len(results)} group(s)")
        return results

    def get_aggregates(self, survey_id: str) -> list[SurveyAggregate]:
        return self._aggregates.get_aggregates(survey_id)

    # ── Private helpers ──────────────────────────────────

    @staticmethod
    def _compute_text_aggregation(responses: list) -> dict[str, Any]:
        total = len(responses)
        if total == 0:
            return {"total": 0, "agree_pct": 0, "disagree_pct": 0, "mixed_pct": 0, "mean_confidence": 0}

        agree = sum(1 for r in responses if r.stance == "agree")
        disagree = sum(1 for r in responses if r.stance == "disagree")
        mixed = sum(1 for r in responses if r.stance == "mixed")
        mean_conf = sum(r.confidence for r in responses) / total
        fallback_count = sum(1 for r in responses if r.is_fallback)

        top_reasons = []
        for r in sorted(responses, key=lambda x: x.confidence, reverse=True)[:10]:
            if r.short_reason:
                top_reasons.append({
                    "stance": r.stance,
                    "confidence": round(r.confidence, 3),
                    "reason": r.short_reason,
                })

        return {
            "total": total,
            "agree_count": agree,
            "disagree_count": disagree,
            "mixed_count": mixed,
            "agree_pct": round(agree / total * 100, 1),
            "disagree_pct": round(disagree / total * 100, 1),
            "mixed_pct": round(mixed / total * 100, 1),
            "mean_confidence": round(mean_conf, 3),
            "fallback_count": fallback_count,
            "top_reasons": top_reasons,
        }

    @staticmethod
    def _compute_question_aggregation(q_type: str, responses: list) -> dict[str, Any]:
        total = len(responses)
        if total == 0:
            return {"total": 0, "type": q_type}

        mean_conf = sum(r.confidence for r in responses) / total

        if q_type == "stance":
            agree = sum(1 for r in responses if r.answer == "agree")
            disagree = sum(1 for r in responses if r.answer == "disagree")
            mixed = sum(1 for r in responses if r.answer == "mixed")
            return {
                "total": total,
                "type": q_type,
                "agree_pct": round(agree / total * 100, 1),
                "disagree_pct": round(disagree / total * 100, 1),
                "mixed_pct": round(mixed / total * 100, 1),
                "mean_confidence": round(mean_conf, 3),
            }
        elif q_type == "likert":
            values = []
            for r in responses:
                try:
                    values.append(float(r.answer))
                except (ValueError, TypeError):
                    pass
            mean_val = sum(values) / len(values) if values else 0
            return {
                "total": total,
                "type": q_type,
                "mean_value": round(mean_val, 2),
                "mean_confidence": round(mean_conf, 3),
            }
        else:  # mcq
            counts: dict[str, int] = {}
            for r in responses:
                counts[r.answer] = counts.get(r.answer, 0) + 1
            distribution = {k: round(v / total * 100, 1) for k, v in counts.items()}
            return {
                "total": total,
                "type": q_type,
                "distribution": distribution,
                "mean_confidence": round(mean_conf, 3),
            }
