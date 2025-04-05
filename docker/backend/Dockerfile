FROM python:3.9-slim

WORKDIR /app

# Installer uv
RUN pip install uv

# Copier les fichiers de dépendances
COPY backend/pyproject.toml .

# Créer un environnement virtuel et installer les dépendances
RUN uv venv .venv \
    && . .venv/bin/activate \
    && uv pip install -e .

# Copier le code de l'application
COPY backend/app ./app
COPY backend/tarot_logic ./tarot_logic

# Exposer le port
EXPOSE 8000

# Lancer l'application
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
