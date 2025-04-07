import random
from .card import Card, Suit, Rank

class Deck:
    """
    Représente un jeu de 78 cartes de Tarot.
    """
    
    def __init__(self):
        """
        Initialise un jeu de Tarot complet et ordonné.
        """
        self.cards: list[Card] = []
        
        # Ajouter les cartes de couleur (56 cartes)
        for suit in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            for rank in [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, 
                         Rank.SIX, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
                         Rank.JACK, Rank.KNIGHT, Rank.QUEEN, Rank.KING]:
                self.cards.append(Card(suit=suit, rank=rank))
        
        # Ajouter les atouts (21 cartes)
        for i in range(1, 22):
            rank = Rank.from_int(i, is_trump=True)
            self.cards.append(Card(suit=Suit.TRUMP, rank=rank))
        
        # Ajouter l'excuse (1 carte)
        self.cards.append(Card(suit=Suit.EXCUSE, rank=Rank.EXCUSE))
    
    def shuffle(self) -> None:
        """
        Mélange le jeu de cartes.
        """
        random.shuffle(self.cards)
    
    def deal(self, num_players: int) -> tuple[list[list[Card]], list[Card]]:
        """
        Distribue les cartes aux joueurs trois par trois et forme le chien.
        
        Args:
            num_players: Nombre de joueurs (3, 4 ou 5)
            
        Returns:
            Tuple contenant la liste des mains des joueurs et le chien
            
        Raises:
            ValueError: Si le nombre de joueurs n'est pas valide
        """
        if num_players not in [3, 4, 5]:
            raise ValueError(f"Nombre de joueurs invalide: {num_players}. Doit être 3, 4 ou 5.")
        
        # Taille du chien selon le nombre de joueurs
        dog_sizes = {3: 6, 4: 6, 5: 3}
        dog_size = dog_sizes[num_players]
        
        # Initialiser les mains des joueurs
        hands = [[] for _ in range(num_players)]
        
        # Mettre 3 cartes aléatoirement dans le chien
        cards_copy = self.cards.copy()
        random.shuffle(cards_copy)  # Shuffle a copy to select random cards for the dog
        
        # Sélectionner des cartes pour le chien
        dog = []
        for _ in range(dog_size):
            card_index = random.randrange(len(cards_copy))
            dog.append(cards_copy.pop(card_index))
        
        # Retirer les cartes du chien du jeu principal
        remaining_cards = [card for card in self.cards if card not in dog]
        
        # Distribution 3 par 3
        current_player = 0
        while remaining_cards:
            # Prendre 3 cartes ou moins si fin du paquet
            cards_to_deal = min(3, len(remaining_cards))
            
            # Donner les cartes au joueur courant
            for _ in range(cards_to_deal):
                hands[current_player].append(remaining_cards.pop(0))
            
            # Passer au joueur suivant
            current_player = (current_player + 1) % num_players
            
            # Si plus de cartes, sortir de la boucle
            if not remaining_cards:
                break
        
        return hands, dog
    
    def collect_from_tricks(self, tricks: list[list[Card]], dog: list[Card]) -> None:
        """
        Récupère les cartes à partir des plis et du chien, sans mélanger.
        
        Args:
            tricks: Liste des plis (chaque pli est une liste de cartes)
            dog: Les cartes du chien
        """
        # Vider le jeu actuel
        self.cards = []
        
        # Ajouter chaque pli dans l'ordre
        for trick in tricks:
            self.cards.extend(trick)
        
        # Ajouter le chien à la fin
        self.cards.extend(dog)
    
    def reset_without_shuffle(self) -> None:
        """
        Réinitialise le jeu sans mélanger (utilisé quand personne ne prend).
        """
        # Ne fait rien, puisque les cartes restent dans le même ordre
        pass
    
    def __len__(self) -> int:
        """
        Retourne le nombre de cartes dans le paquet.
        """
        return len(self.cards)