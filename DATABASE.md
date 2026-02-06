# CrowdMind - Documentation Base de Données

## Vue d'ensemble

Base de données PostgreSQL hébergée sur **Supabase** pour la plateforme CrowdMind. Elle gère les utilisateurs, les modèles ML, les agents IA, les expériences et les déploiements sur appareils.

---

## Diagramme des relations

```
┌─────────────┐       ┌──────────────┐       ┌────────────────────┐
│   users     │       │  ml_models   │       │  ml_model_versions │
│─────────────│       │──────────────│       │────────────────────│
│ id (PK)     │       │ id (PK)      │◄──────│ model_id (FK)      │
│ email       │       │ name         │       │ id (PK)            │
│ role        │       │ framework    │       │ version            │
│ created_at  │       │ description  │       │ file_path          │
└──────┬──────┘       │ created_at   │       │ checksum           │
       │              └──────────────┘       │ size_kb            │
       │                                     └─────────┬──────────┘
       │                                               │
       ▼                                               │
┌─────────────────┐                                    │
│  experiments    │                                    │
│─────────────────│       ┌───────────────────────┐    │
│ id (PK)         │◄──────│  experiment_agents    │    │
│ title           │       │───────────────────────│    │
│ description     │       │ experiment_id (PK,FK) │    │
│ message         │       │ agent_id (PK,FK)      │────┼───┐
│ mode            │       │ model_version_id (FK) │◄───┘   │
│ parameters      │       └───────────────────────┘        │
│ created_by (FK) │                                        │
│ created_at      │                                        │
└────────┬────────┘                                        │
         │                                                 │
         ▼                                                 │
┌─────────────────────┐    ┌─────────────────┐            │
│  agent_reactions    │    │     agents      │◄───────────┘
│─────────────────────│    │─────────────────│
│ id (PK)             │    │ id (PK)         │
│ experiment_id (FK)  │    │ label           │
│ agent_id (FK)       │────│ demographics    │
│ reaction            │    │ traits          │
│ emotion             │    │ created_at      │
│ score               │    └────────┬────────┘
│ raw_data            │             │
│ created_at          │             │
└─────────────────────┘             │
                                    ▼
┌─────────────────────┐    ┌─────────────────────┐
│ experiment_metrics  │    │    agent_models     │
│─────────────────────│    │─────────────────────│
│ experiment_id (PK)  │    │ id (PK)             │
│ metrics             │    │ agent_id (FK)       │
│ computed_at         │    │ model_version_id(FK)│
└─────────────────────┘    │ assigned_at         │
                           └─────────────────────┘

┌─────────────┐       ┌──────────────────────┐
│   devices   │       │  device_deployments  │
│─────────────│       │──────────────────────│
│ id (PK)     │◄──────│ device_id (PK,FK)    │
│ serial_num  │       │ deployed_at (PK)     │
│ status      │       │ agent_id (FK)        │
│ last_seen   │       │ model_version_id(FK) │
└─────────────┘       └──────────────────────┘
```

---

## Tables

### 1. `users`

Gestion des utilisateurs de la plateforme.

| Colonne      | Type         | Contraintes                  | Description                    |
|--------------|--------------|------------------------------|--------------------------------|
| `id`         | `uuid`       | PK, default `gen_random_uuid()` | Identifiant unique          |
| `email`      | `text`       | NOT NULL, UNIQUE             | Adresse email                  |
| `role`       | `text`       | NOT NULL                     | Rôle utilisateur               |
| `created_at` | `timestamptz`| NOT NULL, default `now()`    | Date de création               |

---

### 2. `ml_models`

Catalogue des modèles de machine learning.

| Colonne       | Type         | Contraintes                  | Description                    |
|---------------|--------------|------------------------------|--------------------------------|
| `id`          | `uuid`       | PK, default `gen_random_uuid()` | Identifiant unique          |
| `name`        | `text`       | NOT NULL                     | Nom du modèle                  |
| `framework`   | `text`       | NOT NULL, CHECK              | Framework utilisé              |
| `description` | `text`       | -                            | Description du modèle          |
| `created_at`  | `timestamptz`| NOT NULL, default `now()`    | Date de création               |

**Contrainte CHECK** : `framework` ∈ `{'edge_impulse', 'tflite', 'custom_mlp'}`

---

### 3. `ml_model_versions`

Versions des modèles ML avec stockage sur Supabase Storage.

| Colonne      | Type         | Contraintes                     | Description                    |
|--------------|--------------|---------------------------------|--------------------------------|
| `id`         | `uuid`       | PK, default `gen_random_uuid()` | Identifiant unique             |
| `model_id`   | `uuid`       | FK → `ml_models(id)` ON DELETE CASCADE | Référence au modèle    |
| `version`    | `text`       | NOT NULL                        | Numéro de version              |
| `file_path`  | `text`       | NOT NULL                        | Chemin Supabase Storage        |
| `checksum`   | `text`       | NOT NULL                        | Hash SHA256 du fichier         |
| `size_kb`    | `integer`    | NOT NULL                        | Taille en Ko                   |
| `created_at` | `timestamptz`| NOT NULL, default `now()`       | Date de création               |

**Contrainte UNIQUE** : `(model_id, version)`

**Index** : `idx_ml_model_versions_model_id` sur `model_id`

---

### 4. `agents`

Agents IA avec leurs caractéristiques démographiques et traits de personnalité.

| Colonne        | Type         | Contraintes                  | Description                    |
|----------------|--------------|------------------------------|--------------------------------|
| `id`           | `uuid`       | PK, default `gen_random_uuid()` | Identifiant unique          |
| `label`        | `text`       | NOT NULL                     | Libellé de l'agent             |
| `demographics` | `jsonb`      | -                            | Données démographiques (JSON)  |
| `traits`       | `jsonb`      | -                            | Traits de personnalité (JSON)  |
| `created_at`   | `timestamptz`| NOT NULL, default `now()`    | Date de création               |

---

### 5. `agent_models`

Association agents ↔ versions de modèles (historique des assignations).

| Colonne            | Type         | Contraintes                        | Description                    |
|--------------------|--------------|------------------------------------|--------------------------------|
| `id`               | `uuid`       | PK, default `gen_random_uuid()`    | Identifiant unique             |
| `agent_id`         | `uuid`       | FK → `agents(id)` ON DELETE CASCADE | Référence à l'agent          |
| `model_version_id` | `uuid`       | FK → `ml_model_versions(id)` ON DELETE RESTRICT | Version du modèle |
| `assigned_at`      | `timestamptz`| NOT NULL, default `now()`          | Date d'assignation             |

**Index** :
- `idx_agent_models_agent_id` sur `agent_id`
- `idx_agent_models_model_version_id` sur `model_version_id`
- `idx_agent_models_agent_assigned_at` sur `(agent_id, assigned_at)`

---

### 6. `experiments`

Expériences de simulation avec population d'agents.

| Colonne       | Type         | Contraintes                        | Description                    |
|---------------|--------------|------------------------------------|--------------------------------|
| `id`          | `uuid`       | PK, default `gen_random_uuid()`    | Identifiant unique             |
| `title`       | `text`       | NOT NULL                           | Titre de l'expérience          |
| `description` | `text`       | -                                  | Description                    |
| `message`     | `text`       | NOT NULL                           | Message/stimulus de l'expérience |
| `mode`        | `text`       | NOT NULL, CHECK                    | Mode d'expérience              |
| `parameters`  | `jsonb`      | -                                  | Paramètres additionnels (JSON) |
| `created_by`  | `uuid`       | FK → `users(id)` ON DELETE RESTRICT | Créateur de l'expérience     |
| `created_at`  | `timestamptz`| NOT NULL, default `now()`          | Date de création               |

**Contrainte CHECK** : `mode` ∈ `{'polling', 'ab_test', 'free'}`

**Index** :
- `idx_experiments_created_by` sur `created_by`
- `idx_experiments_created_at` sur `created_at`

---

### 7. `experiment_agents`

Population d'agents participant à une expérience (avec version du modèle figée).

| Colonne            | Type   | Contraintes                              | Description                    |
|--------------------|--------|------------------------------------------|--------------------------------|
| `experiment_id`    | `uuid` | PK, FK → `experiments(id)` ON DELETE CASCADE | Référence à l'expérience   |
| `agent_id`         | `uuid` | PK, FK → `agents(id)` ON DELETE CASCADE  | Référence à l'agent            |
| `model_version_id` | `uuid` | FK → `ml_model_versions(id)` ON DELETE RESTRICT | Version figée du modèle |

**Clé primaire** : `(experiment_id, agent_id)`

**Index** :
- `idx_experiment_agents_agent_id` sur `agent_id`
- `idx_experiment_agents_model_version_id` sur `model_version_id`

---

### 8. `agent_reactions`

Réactions des agents lors des expériences.

| Colonne         | Type         | Contraintes                        | Description                    |
|-----------------|--------------|------------------------------------|--------------------------------|
| `id`            | `uuid`       | PK, default `gen_random_uuid()`    | Identifiant unique             |
| `experiment_id` | `uuid`       | FK → `experiments(id)` ON DELETE CASCADE | Référence à l'expérience |
| `agent_id`      | `uuid`       | FK → `agents(id)` ON DELETE CASCADE | Référence à l'agent           |
| `reaction`      | `text`       | NOT NULL                           | Type de réaction               |
| `emotion`       | `text`       | NOT NULL                           | Émotion détectée               |
| `score`         | `numeric`    | -                                  | Score numérique                |
| `raw_data`      | `jsonb`      | -                                  | Données brutes (JSON)          |
| `created_at`    | `timestamptz`| NOT NULL, default `now()`          | Date de création               |

**Valeurs attendues** :
- `reaction` : `accept`, `reject`, `doubt`
- `emotion` : `joy`, `anger`, `fear`, `neutral`

**Index** :
- `idx_agent_reactions_experiment_id` sur `experiment_id`
- `idx_agent_reactions_agent_id` sur `agent_id`
- `idx_agent_reactions_experiment_created_at` sur `(experiment_id, created_at)`

---

### 9. `experiment_metrics`

Métriques agrégées calculées pour chaque expérience.

| Colonne         | Type         | Contraintes                        | Description                    |
|-----------------|--------------|------------------------------------|--------------------------------|
| `experiment_id` | `uuid`       | PK, FK → `experiments(id)` ON DELETE CASCADE | Référence à l'expérience |
| `metrics`       | `jsonb`      | NOT NULL                           | Métriques calculées (JSON)     |
| `computed_at`   | `timestamptz`| NOT NULL, default `now()`          | Date de calcul                 |

---

### 10. `devices`

Appareils physiques pour le déploiement des modèles.

| Colonne         | Type         | Contraintes                  | Description                    |
|-----------------|--------------|------------------------------|--------------------------------|
| `id`            | `uuid`       | PK, default `gen_random_uuid()` | Identifiant unique          |
| `serial_number` | `text`       | NOT NULL, UNIQUE             | Numéro de série                |
| `status`        | `text`       | NOT NULL, CHECK              | Statut de l'appareil           |
| `last_seen`     | `timestamptz`| -                            | Dernière connexion             |

**Contrainte CHECK** : `status` ∈ `{'online', 'offline'}`

---

### 11. `device_deployments`

Historique des déploiements sur les appareils.

| Colonne            | Type         | Contraintes                              | Description                    |
|--------------------|--------------|------------------------------------------|--------------------------------|
| `device_id`        | `uuid`       | PK, FK → `devices(id)` ON DELETE CASCADE | Référence à l'appareil         |
| `deployed_at`      | `timestamptz`| PK, NOT NULL, default `now()`            | Date de déploiement            |
| `agent_id`         | `uuid`       | FK → `agents(id)` ON DELETE RESTRICT     | Agent déployé                  |
| `model_version_id` | `uuid`       | FK → `ml_model_versions(id)` ON DELETE RESTRICT | Version du modèle      |

**Clé primaire** : `(device_id, deployed_at)`

**Index** :
- `idx_device_deployments_agent_id` sur `agent_id`
- `idx_device_deployments_model_version_id` sur `model_version_id`

---

## Extensions PostgreSQL

| Extension   | Description                              |
|-------------|------------------------------------------|
| `pgcrypto`  | Génération d'UUID avec `gen_random_uuid()` |

---

## Règles de suppression (ON DELETE)

| Relation                          | Comportement       | Explication                                      |
|-----------------------------------|--------------------|--------------------------------------------------|
| `ml_model_versions` → `ml_models` | CASCADE            | Suppression du modèle = suppression des versions |
| `agent_models` → `agents`         | CASCADE            | Suppression de l'agent = suppression des assignations |
| `agent_models` → `ml_model_versions` | RESTRICT        | Impossible de supprimer une version utilisée     |
| `experiments` → `users`           | RESTRICT           | Impossible de supprimer un utilisateur avec expériences |
| `experiment_agents` → `experiments` | CASCADE          | Suppression de l'expérience = suppression des participants |
| `experiment_agents` → `agents`    | CASCADE            | Suppression de l'agent = retrait des expériences |
| `experiment_agents` → `ml_model_versions` | RESTRICT   | Impossible de supprimer une version utilisée     |
| `agent_reactions` → `experiments` | CASCADE            | Suppression de l'expérience = suppression des réactions |
| `agent_reactions` → `agents`      | CASCADE            | Suppression de l'agent = suppression des réactions |
| `experiment_metrics` → `experiments` | CASCADE         | Suppression de l'expérience = suppression des métriques |
| `device_deployments` → `devices`  | CASCADE            | Suppression de l'appareil = suppression de l'historique |
| `device_deployments` → `agents`   | RESTRICT           | Impossible de supprimer un agent déployé         |
| `device_deployments` → `ml_model_versions` | RESTRICT  | Impossible de supprimer une version déployée     |

---

## Cas d'usage typiques

### Créer une expérience avec des agents
```sql
-- 1. Créer l'expérience
INSERT INTO experiments (title, message, mode, created_by)
VALUES ('Test campagne A', 'Nouveau produit X', 'polling', '<user_id>');

-- 2. Associer des agents avec leur version de modèle actuelle
INSERT INTO experiment_agents (experiment_id, agent_id, model_version_id)
SELECT '<exp_id>', am.agent_id, am.model_version_id
FROM agent_models am
WHERE am.agent_id IN ('<agent1>', '<agent2>');
```

### Récupérer les résultats d'une expérience
```sql
SELECT 
  a.label,
  ar.reaction,
  ar.emotion,
  ar.score
FROM agent_reactions ar
JOIN agents a ON a.id = ar.agent_id
WHERE ar.experiment_id = '<exp_id>'
ORDER BY ar.created_at;
```

### Historique des déploiements d'un appareil
```sql
SELECT 
  dd.deployed_at,
  a.label AS agent,
  mv.version,
  m.name AS model
FROM device_deployments dd
JOIN agents a ON a.id = dd.agent_id
JOIN ml_model_versions mv ON mv.id = dd.model_version_id
JOIN ml_models m ON m.id = mv.model_id
WHERE dd.device_id = '<device_id>'
ORDER BY dd.deployed_at DESC;
```
