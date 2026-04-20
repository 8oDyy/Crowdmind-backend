# CrowdMind Backend

Plateforme FastAPI d'orchestration de simulations de sondages multi-agents, avec calcul heuristique déporté sur Raspberry Pi et persistance dans Supabase.

---

## Aperçu

CrowdMind permet de simuler des sondages auprès d'une population d'agents synthétiques. Chaque agent possède un profil démographique et psychologique généré de façon déterministe à partir d'une graine (seed), ce qui garantit la reproductibilité des simulations.

Le backend FastAPI orchestre l'ensemble du flux : création du sondage, génération locale des profils d'agents, délégation des calculs de réponses à un Raspberry Pi externe, puis persistance des résultats et agrégats dans Supabase (PostgreSQL managé).

Le moteur de calcul (heuristique) tourne sur un Raspberry Pi physique plutôt que sur le serveur principal. Ce choix permet de séparer la logique d'inférence des agents — potentiellement intensive — de l'API REST, sans exposer le Pi sur Internet grâce à un tunnel WebSocket inverse.

---

## Architecture

### Schéma du flux

```
Frontend
   |
   | HTTPS / WSS
   v
Backend FastAPI  <------>  Supabase (PostgreSQL)
   ^
   |  WebSocket inverse (wss://api.crowdmind.fr/api/v1/ws/pi-worker)
   |
Raspberry Pi
(moteur heuristique)
```

Le Pi initie la connexion vers le backend — et non l'inverse. Cela évite d'avoir à exposer le Pi sur Internet.

### Arborescence du repo

```
.
├── Dockerfile                    # Image Python 3.13-slim, lance uvicorn
├── docker-compose.prod.yml       # Stack prod (api_prod + Redis)
├── docker-compose.staging.yml    # Stack staging (api_staging + Redis)
├── docker-compose.nginx.yml      # Reverse proxy TLS commun
├── nginx.conf                    # Vhosts prod/staging, proxy /api/ et WS
├── infra/
│   └── bootstrap.sh              # Crée le network docker crowdmind_net
├── DATABASE.md                   # Schéma BDD Supabase détaillé
└── backend/
    ├── app/
    │   ├── api/v1/
    │   │   ├── endpoints/        # Routeurs FastAPI
    │   │   └── schemas/          # DTOs Pydantic
    │   ├── core/
    │   │   ├── dependencies.py   # Injection de dépendances
    │   │   └── errors.py         # Hiérarchie AppError
    │   ├── domain/
    │   │   ├── entities/         # Dataclasses du domaine
    │   │   └── enums/
    │   ├── infrastructure/
    │   │   ├── db/               # Client Supabase
    │   │   └── pi/               # PiClient, PiWsManager, générateur d'agents
    │   ├── repositories/         # Un fichier par table Supabase
    │   ├── services/             # Logique métier
    │   └── tests/                # Tests avec fakes injectés
    ├── pyproject.toml
    └── README.md                 # Documentation détaillée de l'API
```

---

## Communication avec le Pi

Le Pi est le seul composant autorisé à initier la connexion WebSocket. Il se connecte sur :

```
wss://<backend>/api/v1/ws/pi-worker
```

Chaque appel du backend vers le Pi est corrélé par un `task_id` UUID : le backend envoie un message JSON avec ce `task_id`, le Pi effectue le calcul et répond avec le même identifiant. `PiWsManager` gère cette corrélation et expose `call_sync` pour les endpoints synchrones.

Si aucun Pi n'est connecté au moment d'une requête, `PiClient` lève immédiatement `PiClientError` — il n'existe pas de fallback HTTP.

**Authentification (optionnelle)** : configurer `PI_TOKEN` dans l'environnement. Le Pi doit transmettre ce token soit en query string (`?token=<valeur>`), soit dans le header `Authorization: Bearer <valeur>`.

---

## Démarrage rapide

### Prérequis

- Python 3.11+ (3.13 recommandé, utilisé en CI et Docker)
- Docker + Docker Compose
- Un projet Supabase (URL + clé de service)
- Un Raspberry Pi avec le moteur heuristique prêt à se connecter

### Variables d'environnement

Créer un fichier `backend/.env` :

```env
APP_NAME=CrowdMind API
ENV=dev
API_PREFIX=/api/v1

# Supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
SUPABASE_SCHEMA=public

# Raspberry Pi
PI_TIMEOUT=30.0
PI_TOKEN=                       # optionnel, vide = auth désactivée

# Divers
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

### Installation et lancement

```bash
# Depuis backend/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Lancer l'API en mode développement (avec rechargement automatique)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API est alors accessible sur `http://localhost:8000/api/v1/docs`.

---

## Tests et qualité

```bash
# Depuis backend/

# Lancer tous les tests
PYTHONPATH=. pytest app/tests/ -v

# Un seul test
PYTHONPATH=. pytest app/tests/test_surveys.py::test_xxx -v

# Avec rapport de couverture (seuil CI : 40 %)
PYTHONPATH=. pytest app/tests/ --cov=app --cov-report=term-missing --cov-fail-under=40

# Lint (depuis la racine du repo)
ruff check backend/

# Vérification du format
ruff format --check backend/
```

Les tests n'accèdent jamais à Supabase ni au vrai Pi : des `Fake*Repository` et un `FakePiClient` déterministe sont injectés via `app.dependency_overrides`.

---

## Déploiement

### Première mise en place (réseau Docker)

Sur le serveur, avant toute chose :

```bash
./infra/bootstrap.sh
```

Ce script crée le network Docker externe `crowdmind_net` partagé entre les containers API et Nginx.

### CI/CD

La chaîne CI/CD est entièrement automatisée via GitHub Actions :

| Etape | Fichier | Déclencheur |
|-------|---------|-------------|
| CI | `.github/workflows/ci.yml` | Push sur n'importe quelle branche |
| CD | `.github/workflows/cd.yml` | Succès du CI (`workflow_run`) |

**CI** : Python 3.13, `ruff check`, `ruff format --check`, `pytest` avec couverture >= 40 %, puis build et push de l'image Docker sur GHCR (`ghcr.io/8odyy/crowdmind-backend-api:<tag>`).

**CD** : copie du compose file et de `bootstrap.sh` sur le serveur via SCP, puis SSH pour `docker compose pull && up -d --force-recreate`, healthcheck (30 tentatives), prune des images obsolètes, et rechargement de la configuration Nginx.

### Environnements

| Branche | Image | Container | URL |
|---------|-------|-----------|-----|
| `dev` | `:dev` | `api_staging` | `https://staging-api.crowdmind.fr/api/v1/docs` |
| `main` | `:latest` | `api_prod` | `https://api.crowdmind.fr/api/v1/docs` |

Nginx (`docker-compose.nginx.yml`) tourne dans un container séparé sur le même network `crowdmind_net` et termine le TLS pour les deux environnements.

---

## Documentation additionnelle

- `backend/README.md` — documentation détaillée de l'API : endpoints, schémas de requêtes/réponses, flux d'un sondage, gestion d'erreurs
- `DATABASE.md` — schéma complet de la base de données Supabase : tables, colonnes, relations et contraintes
