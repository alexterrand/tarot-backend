from typing import List, Optional
from .card import Card

class Player:
    """
    Représente un joueur dans une partie de Tarot.
    """
    
    def __init__(self, player_id: str):
        """
        Initialise un joueur avec un identifiant unique.
        
        Args:
            player_id: Identifiant unique du joueur
        """
        self.player_id = player_id
        self.hand: List[Card] = []
        self.tricks_won: List[List[Card]] = []
    
    def add_cards_to_hand(self, cards: List[Card]) -> None:
        """
        Ajoute des cartes à la main du joueur.
        
        Args:
            cards: Liste des cartes à ajouter
        """
        self.hand.extend(cards)
        # Trier les cartes pour une meilleure organisation
        self.hand.sort()
    
    def play_card(self, card: Card) -> Card:
        """
        Joue une carte de la main du joueur.
        
        Args:
            card: La carte à jouer
            
        Returns:
            La carte jouée
            
        Raises:
            ValueError: Si la carte n'est pas dans la main du joueur
        """
        try:
            self.hand.remove(card)
            return card
        except ValueError:
            raise ValueError(f"La carte {card} n'est pas dans la main du joueur {self.player_id}")
        
    def add_trick(self, trick: List[Card]) -> None:
        """
        Ajoute un pli remporté au joueur.
        
        Args:
            trick: Liste des cartes du pli remporté
        """
        self.tricks_won.append(trick)
    
    def get_card_count(self) -> int:
        """
        Retourne le nombre de cartes dans la main du joueur.
        
        Returns:
            Nombre de cartes
        """
        return len(self.hand)
    
    def has_card(self, card: Card) -> bool:
        """
        Vérifie si le joueur possède une carte spécifique.
        
        Args:
            card: La carte à vérifier
            
        Returns:
            True si la carte est dans la main du joueur, False sinon
        """
        return card in self.hand