# CrowdMind Backend API v2

API FastAPI pour la simulation de sondages multi-agents avec moteur heuristique (Raspberry Pi).

> **CrowdMind** simule des panels d'agents idéologiques virtuels qui répondent
> à des sondages (mode texte ou questionnaire) via un **moteur heuristique** tournant
> sur un Raspberry Pi. Le backend orchestre le flux : création du sondage → appel au Pi
> → stockage des agents, réponses et agrégations dans Supabase → diffusion temps réel
> via WebSocket.

## Prérequis

- Python 3.11+
- Compte Supabase (PostgreSQL)
- Raspberry Pi qui se connecte au backend via WebSocket inverse (`/api/v1/ws/pi-worker`)

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

PI_TIMEOUT=30.0
PI_TOKEN=
```

> **Important** : le Pi se connecte au backend via WebSocket inverse
> (`wss://<backend>/api/v1/ws/pi-worker`). Si `PI_TOKEN` est défini, le Pi doit
> fournir le même token (query `?token=...` ou header `Authorization: Bearer`).

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

Vérifier que l'API et le Raspberry Pi fonctionnent.

```
GET /api/v1/health
```

**Réponse** :
```json
{ "status": "ok", "pi_status": "ok" }
```

> Si le Pi est injoignable, `pi_status` sera `"unreachable"` (l'API elle-même reste `"ok"`).

---

### 2. Créer un sondage

Crée un sondage **et exécute la simulation complètement** (appel au Pi, stockage des agents, réponses et agrégats). Le sondage retourné a directement le statut `completed`.

Deux modes possibles :

- **`text`** — On donne un texte/sujet aux agents, chacun répond avec une position (agree/disagree/mixed), un score de confiance et une raison.
- **`questionnaire`** — On définit des questions typées (stance, likert, mcq) et chaque agent répond à chaque question.

```
POST /api/v1/surveys
```

#### Mode `text` (sujet libre)

Le moteur heuristique du Pi génère des agents virtuels avec des profils idéologiques variés, puis chaque agent analyse le texte et donne sa position.

```json
{
  "title": "Avis sur le revenu universel",
  "mode": "text",
  "input_text": "Le revenu universel de base devrait être instauré en France pour garantir un minimum vital à chaque citoyen, indépendamment de son statut professionnel.",
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
  "status": "completed",
  "model": "heuristic",
  "n_agents": 100,
  "seed": 42,
  "parameters": {},
  "created_by": null,
  "elapsed_seconds": 0.342,
  "started_at": "2026-03-10T09:00:00Z",
  "completed_at": "2026-03-10T09:00:00Z",
  "created_at": "2026-03-10T09:00:00Z"
}
```

> Le `model` est automatiquement défini à `"heuristic"`. Les agents, réponses et agrégats sont
> déjà stockés en BDD à ce stade — pas besoin de lancer le calcul séparément.

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
| `eco` | Axe économique (-1 = gauche redistributive, +1 = droite marché) |
| `open` | Ouverture culturelle (-1 = conservateur, +1 = progressiste) |
| `trust` | Confiance dans les institutions (0 = méfiant, 1 = confiant) |
| `temperament` | Tempérament (0 = calme/réfléchi, 1 = impulsif/tranché) |
| `age` | Âge (18–85) |
| `education` | `sans_diplome`, `brevet`, `bac`, `bac+2`, `bac+3`, `bac+5`, `doctorat` |
| `urban_rural` | `rural`, `periurbain`, `ville_moyenne`, `grande_ville`, `metropole` |
| `classe_sociale` | `populaire`, `moyenne_inferieure`, `moyenne`, `moyenne_superieure`, `aisee` |
| `background` | Description narrative du profil (1-2 phrases) |

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
| `raw_llm_output` | `null` (moteur heuristique, pas de LLM) |
| `is_fallback` | `false` (toujours fiable avec le moteur heuristique) |

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
1. POST /surveys                → Crée le sondage + appelle le Pi + stocke tout (status: completed)
   ├─ Création en BDD (pending)
   ├─ Passage en running
   ├─ Génération des agents localement (même seed = mêmes profils que le Pi)
   ├─ Appel HTTP au Pi (/api/survey/text ou /api/survey/questions)
   ├─ Stockage agents, réponses et agrégats en BDD
   └─ Passage en completed avec elapsed_seconds
2. GET /surveys/{id}            → Vérifier le statut et les détails
3. GET /surveys/{id}/agents     → Voir les profils des agents
4. GET /surveys/{id}/responses  → Voir les réponses individuelles (mode text)
5. GET /surveys/{id}/question-responses → Voir les réponses par question (mode questionnaire)
6. GET /surveys/{id}/aggregates → Lire les résultats agrégés
```

> **Temps de réponse** : le Pi répond en < 200ms pour 100 agents × 5 questions.
> Le goulot d'étranglement est le réseau + les écritures BDD, pas le calcul.

---

## Base de données (Supabase)

| Table | Description |
|---|---|
| `users` | Utilisateurs (auth) |
| `surveys` | Sondages avec mode, statut, modèle (`heuristic`), paramètres |
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
│   ├── infrastructure/         # Clients DB, LLM (Groq, Ollama) et Pi heuristique
│   │   ├── db/                 # Client Supabase
│   │   ├── llm/                # Clients Groq et Ollama
│   │   └── pi/                 # Client HTTP Pi + génération d'agents locale
│   └── tests/                  # Tests pytest
├── requirements.txt
└── README.md
```
