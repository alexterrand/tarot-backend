from typing import List
from .card import Card, Suit
from .player import Player

class GameState:
    """
    Représente l'état d'une partie de Tarot.
    """
    
    def __init__(self, player_ids: list[str]):
        """
        Initialise une nouvelle partie de Tarot.
        
        Args:
            player_ids: Liste des identifiants des joueurs
        
        Raises:
            ValueError: Si le nombre de joueurs n'est pas valide
        """
        if len(player_ids) not in [3, 4, 5]:
            raise ValueError(f"Nombre de joueurs invalide: {len(player_ids)}. Doit être 3, 4 ou 5.")
        
        self.players: list[Player] = [Player(player_id) for player_id in player_ids]
        self.current_player_index: int = 0
        self.current_trick: list[Card] = []
        self.dog: list[Card] = []
        
        # Stocke les index des joueurs qui ont contribué au pli actuel
        self.trick_player_indices: list[int] = []
        
        # Joueur qui a commencé le pli actuel
        self.trick_starter_index: int = 0
    
    def play_card(self, player_index: int, card: Card) -> None:
        """
        Joue une carte pour un joueur.
        
        Args:
            player_index: Index du joueur qui joue la carte
            card: La carte à jouer
            
        Raises:
            ValueError: Si ce n'est pas le tour du joueur ou si la carte est invalide
        """
        if player_index != self.current_player_index:
            raise ValueError(f"Ce n'est pas le tour du joueur {player_index}")
        
        player = self.players[player_index]
        
        # Le joueur joue la carte
        played_card = player.play_card(card)
        
        # Ajout au pli courant
        self.current_trick.append(played_card)
        self.trick_player_indices.append(player_index)
        
        # Passer au joueur suivant
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Si tous les joueurs ont joué, terminer le pli
        if len(self.current_trick) == len(self.players):
            self._complete_trick()
    
    def _complete_trick(self) -> None:
        """
        Termine le pli actuel, détermine le gagnant et prépare le prochain pli.
        """
        from .rules import get_trick_winner  # Import ici pour éviter les imports circulaires
        
        # Déterminer le gagnant du pli
        winner_card_index = get_trick_winner(self.current_trick, Suit.TRUMP)
        winner_player_index = self.trick_player_indices[winner_card_index]
        
        # Donner le pli au gagnant
        winner = self.players[winner_player_index]
        winner.add_trick(self.current_trick.copy())
        
        # Réinitialiser pour le prochain pli
        self.current_trick = []
        self.trick_player_indices = []
        
        # Le gagnant commence le prochain pli
        self.current_player_index = winner_player_index
        self.trick_starter_index = winner_player_index
    
    def is_game_over(self) -> bool:
        """
        Vérifie si la partie est terminée (toutes les cartes jouées).
        
        Returns:
            True si la partie est terminée, False sinon
        """
        return all(player.get_card_count() == 0 for player in self.players)
    
    def get_current_player(self) -> Player:
        """
        Retourne le joueur dont c'est le tour.
        
        Returns:
            Le joueur courant
        """
        return self.players[self.current_player_index]
    
    def get_player_by_id(self, player_id: str) -> Player | None:
        """
        Récupère un joueur par son identifiant.
        
        Args:
            player_id: L'identifiant du joueur recherché
            
        Returns:
            Le joueur correspondant ou None s'il n'existe pas
        """
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None
    
    def count_points(self, cards: List[Card]) -> float:
        """Count the total points in a list of cards."""
        return sum(card.get_points() for card in cards)
    
    def count_oudlers(self, cards: List[Card]) -> int:
        """Count the number of oudlers in a list of cards."""
        oudlers = 0
        for card in cards:
            if card.suit == Suit.ATOUT and card.value in [0, 1, 21]:
                oudlers += 1
        return oudlers
    
    def get_points_needed(self, oudlers_count: int) -> float:
        """Get the points needed to win based on oudlers count."""
        thresholds = {
            0: 56,
            1: 51,
            2: 41,
            3: 36
        }
        return thresholds.get(oudlers_count, 56)
    
    def check_taker_victory(self) -> bool:
        """Check if the taker won the game."""
        # Assuming self.taker_cards contains the taker's won tricks
        taker_points = self.count_points(self.taker_cards)
        taker_oudlers = self.count_oudlers(self.taker_cards)
        points_needed = self.get_points_needed(taker_oudlers)
        
        return taker_points > points_needed