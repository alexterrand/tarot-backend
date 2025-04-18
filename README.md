# Tarot Game MVP

Les partie backend python et fastAPI d'un jeu de Tarot traditionnel français.

## Structure du projet

- `backend/` : API FastAPI et logique de jeu Python
  - `app/` : Code source de l'API
  - `tarot_logic/` : Module Python indépendant contenant les règles du jeu
  - `tests/` : Tests unitaires et d'intégration
- `docker/` : Configuration Docker pour déploiement

## Prérequis

- Python 3.9+
- uv (pour la gestion des packages Python)
- Docker et Docker Compose (pour le déploiement)

## Installation et mise en route

### Backend

```bash
cd backend
uv venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
uv pip install -e .
uv pip install -e ".[dev]"  # Pour installer les dépendances de développement

# Lancer les tests
pytest

# Vérifier le style du code
ruff check .
ruff format .

# Lancer l'API
uvicorn app.main:app --reload
```

### Docker

```bash
cd docker
docker-compose up --build
```

## Développement et contribution

1. Créez une branche à partir de `main`
2. Apportez vos modifications
3. Vérifiez que les tests passent avec `pytest`
4. Formatez votre code avec `ruff format .`
5. Soumettez une pull request

## Licence

MIT
