la /gi# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Préférences de collaboration

- Pour les tâches qui peuvent être parallélisées ou déléguées (recherche dans le repo, gros refactors, multi-fichiers indépendants), privilégier les **sous-agents en Sonnet** (`subagent_type: general-purpose` ou `Explore`, `model: sonnet`) plutôt que tout faire dans la conversation principale. Les petites modifs locales restent en direct.

## Commandes courantes

Toutes les commandes se lancent depuis `backend/`.

```bash
# Développement local (avec reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lint + format (obligatoire pour la CI)
ruff check backend/          # lancé depuis la racine du repo
ruff format --check backend/

# Tests
PYTHONPATH=. pytest app/tests/ -v
PYTHONPATH=. pytest app/tests/test_surveys.py::test_xxx -v   # un seul test
PYTHONPATH=. pytest app/tests/ --cov=app --cov-report=term-missing --cov-fail-under=40
```

La CI (`.github/workflows/ci.yml`) utilise **Python 3.13** et exige `ruff check` + `ruff format --check` + coverage ≥ 40 % avant de push l'image Docker sur GHCR.

## Architecture

API FastAPI qui orchestre des simulations de sondages multi-agents. Les calculs (agents + réponses) sont délégués à un **Raspberry Pi** externe exécutant un moteur heuristique ; le backend stocke tout dans Supabase.

### Flux d'un sondage (`POST /api/v1/surveys`)

`create_survey` (endpoint sync) → `SurveyService.create_survey` (insère en BDD, status `pending`, crée les `survey_questions` si mode `questionnaire`) → `SurveyService.run_survey` :

1. `mark_running`
2. `agent_generator.generate_agents(n, seed)` — reproduit **localement** les mêmes profils que le Pi pour le même seed, puis les persiste pour avoir leur UUID (le Pi renvoie des indices `agent_id: int`, on les remap vers les UUID Supabase via `agent_uuid_map`).
3. `PiClient.survey_text` ou `survey_questions`
4. Stockage des réponses (`responses` ou `survey_question_responses`) et des agrégats renvoyés par le Pi
5. `mark_completed` avec `elapsed_seconds`

`POST /surveys/{id}/aggregate` recalcule les agrégats côté backend à partir des réponses BDD (utile si le Pi n'en a pas renvoyé ou pour rafraîchir) — `SurveyService._compute_text_aggregation` / `_compute_question_aggregation`.

### Couches (séparées strictement, DI via `core/dependencies.py`)

- `api/v1/endpoints/` — routeurs FastAPI, ne contiennent que du mapping schema ⇄ service
- `api/v1/schemas/` — Pydantic (DTO)
- `services/` — logique métier (`SurveyService`, `RealtimeService`)
- `repositories/` — un fichier par table Supabase, renvoie des entités du domaine
- `domain/entities/` — dataclasses du domaine ; `domain/enums/` — enums
- `infrastructure/db/supabase_client.py` — wrapper Supabase
- `infrastructure/pi/` — client Pi + générateur d'agents local
- `infrastructure/llm/` — clients Groq / Ollama (présents mais pas branchés dans le flux sondage actuel, qui est 100 % `heuristic`)

### Communication avec le Pi (important)

**Un seul chemin : WebSocket inverse.** Le Pi se connecte à `/api/v1/ws/pi-worker` (endpoint `websocket.py` → `PiWsManager`). `PiClient` route tout via `PiWsManager.call_sync` ; si aucun Pi n'est connecté, `PiClient` lève immédiatement `PiClientError` (pas de fallback HTTP).

- Corrélation requête ↔ réponse via un `task_id` UUID côté `PiWsManager`.
- `PiWsManager.set_loop(asyncio.get_running_loop())` est appelé dans le `lifespan` de `main.py` — **ne pas retirer**, sinon `call_sync` (utilisé depuis les endpoints sync) ne peut pas soumettre à la boucle asyncio.
- Auth optionnelle via `PI_TOKEN` (query `?token=` ou header `Authorization: Bearer`).

### Temps réel client

`/api/v1/ws/experiments/{experiment_id}` (`RealtimeService`) — canal séparé du WS Pi, pour que le frontend suive l'avancement d'un sondage. Support ping/pong JSON.

### Gestion d'erreurs

Hiérarchie `AppError` dans `core/errors.py` (`NotFoundError` → 404, `PiError`/`StorageError` → 502, etc.). Les handlers sont enregistrés dans `main.create_app` ; lever ces exceptions depuis services/repos plutôt que des `HTTPException` directes.

### Tests

`conftest.py` fournit des `Fake*Repository` en mémoire et un `FakePiClient` déterministe, injectés via `app.dependency_overrides`. Les tests ne touchent **jamais** Supabase ni le vrai Pi — pour ajouter un test, override les dépendances pertinentes de `core/dependencies.py`.

## Déploiement

- Dockerfile à la racine du repo (pas dans `backend/`) ; le build copie `backend/` dans `/app` et lance `uvicorn app.main:app`.
- Push sur `dev` → image `ghcr.io/.../crowdmind-backend-api:dev` → CD déploie avec `docker-compose.staging.yml` (container `api_staging`).
- Push sur `main` → tag `latest` → `docker-compose.prod.yml` (container `api_prod`).
- Le CD (`cd.yml`) SCP le compose file puis SSH `docker compose pull && up -d --force-recreate` et reload nginx (`docker exec crowdmind_nginx nginx -s reload`).
- Nginx (`nginx.conf`) termine le TLS et proxy `/api/` + WebSocket `/api/v1/ws/` vers le container.

## Gotchas

- L'index `agent_id: int` renvoyé par le Pi n'est **pas** l'UUID Supabase — toujours passer par `agent_uuid_map` construit dans `run_survey`.
- Le payload `questions` envoyé au Pi exclut les champs `None` (voir `run_survey`, mode questionnaire) — le moteur du Pi refuse les clés nulles.
- Seed identique côté backend et Pi = profils d'agents identiques ; changer le générateur local (`infrastructure/pi/agent_generator.py`) casse cette garantie.
- Python requis : **3.11+** (`pyproject.toml`), CI en 3.13, Dockerfile en 3.13-slim.
