# CrowdMind Backend API v2

API FastAPI pour la simulation de sondages multi-agents avec LLM (Groq / Ollama).

> **CrowdMindAvis** simule des panels d'agents idéologiques virtuels qui répondent
> à des sondages (mode texte ou questionnaire) via un LLM. Le backend stocke les
> sondages, agents, réponses et agrégations dans Supabase et diffuse les résultats
> en temps réel via WebSocket.

## Prérequis

- Python 3.11+
- Compte Supabase (PostgreSQL)
- Groq API key **ou** Ollama local

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` à la racine de `backend/` :

```env
APP_NAME=CrowdMind API
ENV=dev
API_PREFIX=/api/v1

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_SCHEMA=public

CORS_ORIGINS=*
LOG_LEVEL=INFO

GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## Lancement

```bash
# Développement (avec reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Documentation API

- Swagger UI : `http://localhost:8000/api/v1/docs`
- ReDoc : `http://localhost:8000/api/v1/redoc`

## Endpoints principaux

### Health
- `GET /api/v1/health` — Status de l'API

### Surveys
- `POST /api/v1/surveys` — Créer un sondage (mode text ou questionnaire)
- `GET /api/v1/surveys` — Lister les sondages
- `GET /api/v1/surveys/{id}` — Détails d'un sondage
- `DELETE /api/v1/surveys/{id}` — Supprimer un sondage

### Survey sub-resources
- `GET /api/v1/surveys/{id}/agents` — Agents du sondage
- `GET /api/v1/surveys/{id}/questions` — Questions (mode questionnaire)
- `GET /api/v1/surveys/{id}/responses` — Réponses (mode text)
- `GET /api/v1/surveys/{id}/question-responses` — Réponses par question
- `POST /api/v1/surveys/{id}/aggregate` — Calculer les agrégations
- `GET /api/v1/surveys/{id}/aggregates` — Récupérer les agrégations

### WebSocket
- `WS /api/v1/ws/experiments/{experiment_id}` — Abonnement temps réel

## Base de données (Supabase)

| Table | Description |
|---|---|
| `users` | Utilisateurs (auth) |
| `surveys` | Sondages avec mode, statut, modèle LLM, paramètres |
| `agents` | Agents idéologiques (axes eco/open/trust, tempérament, background) |
| `survey_questions` | Questions du questionnaire (stance/likert/mcq) |
| `responses` | Réponses mode texte (stance, confidence, short_reason) |
| `survey_question_responses` | Réponses par question (answer, confidence) |
| `survey_aggregates` | Métriques agrégées (agree_pct, mean_confidence, …) |

## Tests

```bash
PYTHONPATH=. pytest app/tests/ -v
```

## Architecture

```
backend/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/                   # Config, logging, errors, dependencies
│   ├── api/v1/                 # Router et schemas Pydantic
│   ├── domain/                 # Entités métier et enums
│   ├── services/               # Logique métier (SurveyService)
│   ├── repositories/           # Accès données (Supabase)
│   ├── infrastructure/         # Clients DB et LLM (Groq, Ollama)
│   └── tests/                  # Tests pytest
├── requirements.txt
└── README.md
```
