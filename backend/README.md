# CrowdMind Backend API

API FastAPI pour la gestion de modèles ML, datasets synthétiques et expériences.

> **Note** : Cette API ne fait **pas** d'entraînement ML. Elle sert de hub pour :
> - Génférer et stocker des datasets synthétiques
> - Recevoir des modèles `.tflite` entraînés externement
> - Servir les modèles via URL signée
> - Gérer des expériences et diffuser les réactions en temps réel (WebSocket)

## Prérequis

- Python 3.11+
- Compte Supabase (PostgreSQL + Storage)

## Installation

```bash
cd backend
pip install -e ".[dev]"
```

## Configuration

Créer un fichier `.env` à la racine de `backend/` :

```env
APP_NAME=CrowdMind API
ENV=dev
API_PREFIX=/api/v1

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_SCHEMA=public
SUPABASE_STORAGE_BUCKET=models

MAX_UPLOAD_MB=20
CORS_ORIGINS=*
LOG_LEVEL=INFO
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
- `GET /api/v1/health` - Status de l'API

### Datasets
- `POST /api/v1/datasets` - Créer un dataset
- `POST /api/v1/datasets/{id}/generate?n=100&seed=42` - Générer des données synthétiques
- `GET /api/v1/datasets/{id}/export?format=jsonl|csv` - Exporter le dataset

### Models
- `POST /api/v1/models` - Créer les métadonnées d'un modèle
- `POST /api/v1/models/{id}/upload` - Upload fichier `.tflite`
- `GET /api/v1/models/{id}` - Récupérer un modèle
- `GET /api/v1/models/{id}/download?expires=3600` - URL signée de téléchargement

### Agents
- `POST /api/v1/agents` - Créer un agent
- `POST /api/v1/agents/{id}/assign-model/{model_id}` - Assigner un modèle

### Experiments
- `POST /api/v1/experiments` - Créer une expérience
- `POST /api/v1/experiments/{id}/start` - Démarrer
- `POST /api/v1/experiments/{id}/stop` - Arrêter

### Reactions
- `POST /api/v1/reactions` - Créer une réaction (broadcast WebSocket)
- `GET /api/v1/experiments/{id}/reactions` - Lister les réactions

### WebSocket
- `WS /api/v1/ws/experiments/{experiment_id}` - Abonnement temps réel

## Tests

```bash
pytest
```

## Architecture

```
backend/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/                   # Config, logging, errors, dependencies
│   ├── api/v1/                 # Routers et schemas Pydantic
│   ├── domain/                 # Entités métier et enums
│   ├── services/               # Logique métier
│   ├── repositories/           # Accès données (Supabase)
│   ├── infrastructure/         # Clients DB/Storage/Cache
│   └── tests/                  # Tests pytest
├── pyproject.toml
└── README.md
```

## Notes

- L'entraînement ML est fait par un programme Python externe
- L'API reçoit les modèles `.tflite` déjà entraînés
- Le stockage utilise Supabase Storage (swappable vers S3)
