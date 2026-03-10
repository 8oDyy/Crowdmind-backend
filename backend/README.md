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

## Documentation interactive

- **Swagger UI** : `https://staging-api.crowdmind.fr/api/v1/docs`
- **ReDoc** : `https://staging-api.crowdmind.fr/api/v1/redoc`

---

## Guide des Endpoints

> **Base URL** : `https://staging-api.crowdmind.fr/api/v1`

### 1. Health Check

Vérifier que l'API fonctionne.

```
GET /api/v1/health
```

**Réponse** :
```json
{ "status": "ok" }
```

---

### 2. Créer un sondage

Crée un sondage et configure la simulation. Deux modes possibles :

- **`text`** — On donne un texte/sujet aux agents, chacun répond avec une position (agree/disagree/mixed), un score de confiance et une raison.
- **`questionnaire`** — On définit des questions typées (stance, likert, mcq) et chaque agent répond à chaque question.

```
POST /api/v1/surveys
```

#### Mode `text` (sujet libre)

L'IA génère des agents virtuels avec des profils idéologiques variés, puis chaque agent lit le texte et donne sa position.

```json
{
  "title": "Avis sur le revenu universel",
  "mode": "text",
  "input_text": "Le revenu universel de base devrait être instauré en France pour garantir un minimum vital à chaque citoyen, indépendamment de son statut professionnel.",
  "model": "llama-3.3-70b-versatile",
  "n_agents": 100,
  "seed": 42,
  "parameters": {}
}
```

#### Mode `questionnaire` (questions structurées)

On définit des questions précises avec leur type. Chaque agent répond à toutes les questions.

```json
{
  "title": "Enquête sur l'éducation en France",
  "mode": "questionnaire",
  "model": "llama-3.3-70b-versatile",
  "n_agents": 50,
  "seed": 42,
  "questions": [
    {
      "question_id": "q1",
      "type": "stance",
      "text": "L'école publique française offre une éducation de qualité à tous les élèves."
    },
    {
      "question_id": "q2",
      "type": "likert",
      "text": "À quel point êtes-vous satisfait du système éducatif français ?",
      "scale": [1, 2, 3, 4, 5]
    },
    {
      "question_id": "q3",
      "type": "mcq",
      "text": "Quelle réforme prioritaire pour l'éducation ?",
      "choices": ["Plus de moyens", "Réforme des programmes", "Formation des enseignants", "Numérique à l'école"]
    }
  ]
}
```

**Types de questions** :
| Type | Description | Réponses possibles |
|------|-------------|-------------------|
| `stance` | Position sur une affirmation | `agree`, `disagree`, `mixed` |
| `likert` | Échelle numérique | Valeur dans `scale` (ex: 1 à 5) |
| `mcq` | Choix multiple | Une valeur parmi `choices` |

**Réponse** (les deux modes) :
```json
{
  "id": "uuid-du-sondage",
  "title": "Avis sur le revenu universel",
  "mode": "text",
  "input_text": "Le revenu universel ...",
  "status": "pending",
  "model": "llama-3.3-70b-versatile",
  "n_agents": 100,
  "seed": 42,
  "parameters": {},
  "created_by": null,
  "elapsed_seconds": null,
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-03-10T09:00:00Z"
}
```

**Statuts possibles du sondage** : `pending` → `running` → `completed` (ou `failed`)

---

### 3. Lister les sondages

```
GET /api/v1/surveys?limit=100&offset=0
```

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `limit` | int | 100 | Nombre max de résultats (1–1000) |
| `offset` | int | 0 | Décalage pour la pagination |

**Réponse** :
```json
{
  "surveys": [ ... ],
  "count": 12
}
```

---

### 4. Détails d'un sondage

```
GET /api/v1/surveys/{survey_id}
```

Retourne le sondage complet avec son statut, sa durée d'exécution, etc.

---

### 5. Supprimer un sondage

```
DELETE /api/v1/surveys/{survey_id}
```

Supprime le sondage **et toutes ses données** (agents, réponses, agrégations) grâce aux cascades en base.

**Réponse** : `204 No Content`

---

### 6. Récupérer les agents d'un sondage

Les agents sont des profils virtuels générés par l'IA avec des caractéristiques socio-idéologiques.

```
GET /api/v1/surveys/{survey_id}/agents
```

**Réponse** :
```json
{
  "agents": [
    {
      "id": "uuid",
      "survey_id": "uuid",
      "agent_index": 0,
      "eco": 0.7,
      "open": 0.3,
      "trust": 0.5,
      "temperament": 0.6,
      "age": 34,
      "education": "master",
      "urban_rural": "urban",
      "classe_sociale": "moyenne",
      "background": "Ingénieur dans le secteur privé, sensible aux questions écologiques...",
      "created_at": "2026-03-10T09:00:00Z"
    }
  ],
  "count": 100
}
```

**Profil d'un agent** :
| Champ | Description |
|-------|-------------|
| `eco` | Axe économique (0 = gauche, 1 = droite) |
| `open` | Ouverture culturelle (0 = conservateur, 1 = progressiste) |
| `trust` | Confiance dans les institutions (0 = méfiant, 1 = confiant) |
| `temperament` | Tempérament (0 = prudent, 1 = impulsif) |
| `age` | Âge de l'agent |
| `education` | Niveau d'éducation |
| `urban_rural` | Milieu de vie (urban / rural) |
| `classe_sociale` | Classe sociale |
| `background` | Description narrative du profil |

---

### 7. Récupérer les questions (mode questionnaire)

```
GET /api/v1/surveys/{survey_id}/questions
```

**Réponse** :
```json
[
  {
    "id": "uuid",
    "survey_id": "uuid",
    "question_index": 0,
    "question_id": "q1",
    "type": "stance",
    "text": "L'école publique française offre une éducation de qualité.",
    "choices": null,
    "scale": null
  }
]
```

---

### 8. Récupérer les réponses (mode text)

Chaque agent donne sa position sur le texte soumis.

```
GET /api/v1/surveys/{survey_id}/responses?limit=1000&offset=0
```

**Réponse** :
```json
{
  "responses": [
    {
      "id": "uuid",
      "survey_id": "uuid",
      "agent_id": "uuid",
      "stance": "agree",
      "confidence": 0.85,
      "short_reason": "Le revenu universel permettrait de réduire la précarité...",
      "raw_llm_output": "...",
      "is_fallback": false,
      "created_at": "2026-03-10T09:01:00Z"
    }
  ],
  "count": 100
}
```

| Champ | Description |
|-------|-------------|
| `stance` | Position de l'agent : `agree`, `disagree` ou `mixed` |
| `confidence` | Score de confiance (0.0 à 1.0) |
| `short_reason` | Raison courte expliquant la position (max 180 car.) |
| `raw_llm_output` | Réponse brute du LLM |
| `is_fallback` | `true` si le parsing LLM a échoué et qu'on a utilisé un fallback |

---

### 9. Récupérer les réponses par question (mode questionnaire)

```
GET /api/v1/surveys/{survey_id}/question-responses
```

**Réponse** :
```json
{
  "responses": [
    {
      "id": "uuid",
      "survey_id": "uuid",
      "agent_id": "uuid",
      "question_id": "q1",
      "answer": "agree",
      "confidence": 0.9,
      "short_reason": "L'école publique est accessible à tous...",
      "raw_llm_output": "...",
      "is_fallback": false,
      "created_at": "2026-03-10T09:01:00Z"
    }
  ],
  "count": 150
}
```

---

### 10. Calculer les agrégations

Lance le calcul des statistiques agrégées pour un sondage. Supprime les anciennes agrégations et les recalcule.

```
POST /api/v1/surveys/{survey_id}/aggregate
```

**Mode text** — Produit une seule agrégation globale :
```json
{
  "aggregates": [
    {
      "id": "uuid",
      "survey_id": "uuid",
      "question_id": null,
      "aggregation": {
        "total": 100,
        "agree_count": 62,
        "disagree_count": 28,
        "mixed_count": 10,
        "agree_pct": 62.0,
        "disagree_pct": 28.0,
        "mixed_pct": 10.0,
        "mean_confidence": 0.782,
        "fallback_count": 3,
        "top_reasons": [
          {
            "stance": "agree",
            "confidence": 0.95,
            "reason": "Le revenu universel est un filet de sécurité indispensable..."
          }
        ]
      },
      "computed_at": "2026-03-10T09:02:00Z"
    }
  ],
  "count": 1
}
```

**Mode questionnaire** — Produit une agrégation par question :
- **stance** : `agree_pct`, `disagree_pct`, `mixed_pct`
- **likert** : `mean_value` (moyenne des réponses numériques)
- **mcq** : `distribution` (pourcentage pour chaque choix)

---

### 11. Récupérer les agrégations existantes

```
GET /api/v1/surveys/{survey_id}/aggregates
```

Retourne les agrégations déjà calculées sans les recalculer.

---

### 12. WebSocket — Suivi en temps réel

Se connecter pour recevoir les mises à jour en temps réel pendant l'exécution d'un sondage.

```
WS wss://staging-api.crowdmind.fr/api/v1/ws/experiments/{experiment_id}
```

**Ping/Pong** :
```json
// Envoi
{"type": "ping"}
// Réception
{"type": "pong"}
```

---

## Workflow complet

Voici le cycle de vie d'un sondage :

```
1. POST /surveys         → Créer le sondage (status: pending)
2. [Backend interne]     → Générer les agents IA
3. [Backend interne]     → Chaque agent répond via le LLM (status: running)
4. [Backend interne]     → Stocker les réponses (status: completed)
5. GET /surveys/{id}     → Vérifier le statut
6. GET /surveys/{id}/agents    → Voir les profils des agents
7. GET /surveys/{id}/responses → Voir les réponses individuelles
8. POST /surveys/{id}/aggregate → Calculer les stats
9. GET /surveys/{id}/aggregates → Lire les résultats agrégés
```

---

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
