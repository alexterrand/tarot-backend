from pydantic import BaseModel, Field
from enum import Enum


class SuitEnum(str, Enum):
    CLUBS = "CLUBS"
    DIAMONDS = "DIAMONDS"
    HEARTS = "HEARTS"
    SPADES = "SPADES"
    TRUMP = "TRUMP"
    EXCUSE = "EXCUSE"


class CardModel(BaseModel):
    """Représentation d'une carte pour l'API."""
    suit: SuitEnum
    rank: int
    display_name: str = Field(..., description="Nom d'affichage de la carte, ex: 'Roi de Coeur'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "suit": "HEARTS",
                "rank": 14,
                "display_name": "Roi de Coeur"
            }
        }


class PlayerModel(BaseModel):
    """Modèle d'un joueur visible publiquement."""
    id: str
    card_count: int
    is_current: bool
    is_human: bool = True
    tricks_won: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "player_1",
                "card_count": 18,
                "is_current": True,
                "is_human": True,
                "tricks_won": 3
            }
        }


class PlayerHandModel(BaseModel):
    """Modèle représentant la main d'un joueur."""
    player_id: str
    cards: list[CardModel]
    
    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "player_1",
                "cards": [
                    {"suit": "HEARTS", "rank": 14, "display_name": "Roi de Coeur"},
                    {"suit": "TRUMP", "rank": 1, "display_name": "Petit"}
                ]
            }
        }


class PlayCardRequest(BaseModel):
    """Modèle pour jouer une carte."""
    card: CardModel
    
    class Config:
        json_schema_extra = {
            "example": {
                "card": {"suit": "HEARTS", "rank": 14, "display_name": "Roi de Coeur"}
            }
        }


class GameCreateRequest(BaseModel):
    """Paramètres pour créer une partie."""
    num_players: int = Field(..., ge=3, le=5, description="Nombre de joueurs (3-5)")
    human_player_id: str = Field("player_1", description="ID du joueur humain")
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_players": 4,
                "human_player_id": "player_1"
            }
        }


class GamePublicState(BaseModel):
    """État du jeu visible par tous."""
    game_id: str
    players: list[PlayerModel]
    current_trick: list[CardModel] = []
    current_player_id: str
    is_game_over: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "game_123",
                "players": [
                    {"id": "player_1", "card_count": 18, "is_current": True, "is_human": True, "tricks_won": 3},
                    {"id": "player_2", "card_count": 18, "is_current": False, "is_human": False, "tricks_won": 2}
                ],
                "current_trick": [
                    {"suit": "HEARTS", "rank": 10, "display_name": "10 de Coeur"}
                ],
                "current_player_id": "player_1",
                "is_game_over": False
            }
        }


class GameCreatedResponse(BaseModel):
    """Réponse après la création d'une partie."""
    game_id: str
    human_player_id: str
    message: str = "Game created successfully"
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "game_123",
                "human_player_id": "player_1",
                "message": "Game created successfully"
            }
        }