from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any

from app.models.game import (
    GameCreateRequest, 
    GamePublicState, 
    PlayerHandModel, 
    PlayCardRequest,
    GameCreatedResponse
)
from app.services.game_service import GameService


# Service singleton
game_service = GameService()

# Créer le routeur
router = APIRouter()


@router.post("/games", response_model=GameCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_game(request: GameCreateRequest) -> GameCreatedResponse:
    """
    Crée une nouvelle partie de Tarot.
    """
    game_id = game_service.create_game(
        num_players=request.num_players,
        human_player_id=request.human_player_id
    )
    
    return GameCreatedResponse(
        game_id=game_id,
        human_player_id=request.human_player_id
    )


@router.get("/games/{game_id}", response_model=GamePublicState)
async def get_game_state(game_id: str) -> GamePublicState:
    """
    Récupère l'état public d'une partie.
    """
    game_state = game_service.get_game_state(game_id)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partie {game_id} non trouvée"
        )
    
    return game_state


@router.get("/games/{game_id}/players/{player_id}/hand", response_model=PlayerHandModel)
async def get_player_hand(game_id: str, player_id: str) -> PlayerHandModel:
    """
    Récupère la main d'un joueur.
    """
    hand = game_service.get_player_hand(game_id, player_id)
    if not hand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partie {game_id} ou joueur {player_id} non trouvé"
        )
    
    return hand


@router.post("/games/{game_id}/players/{player_id}/play", status_code=status.HTTP_200_OK)
async def play_card(
    game_id: str, 
    player_id: str, 
    play_request: PlayCardRequest
) -> Dict[str, Any]:
    """
    Joue une carte pour un joueur.
    """
    success, message = game_service.play_card(
        game_id=game_id,
        player_id=player_id,
        card_model=play_request.card
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Récupérer l'état mis à jour
    game_state = game_service.get_game_state(game_id)
    
    return {
        "message": message,
        "game_state": game_state
    }