from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router 

app = FastAPI(
    title="Tarot Game API",
    description="API for the Tarot card game",
    version="0.1.0",
)
app.include_router(router)

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # A remplacer par les domaines autorisés en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    Point d'entrée simple pour vérifier que l'API est en cours d'exécution.
    """
    return {"message": "Tarot API is running"}
