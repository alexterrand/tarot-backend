from .card import Card, Suit
from typing import List, Optional


class Trick:
    """
    Represents a single trick in the Tarot game.
    """
    
    def __init__(self):
        self.cards: List[Card] = []
        self.player_indices: List[int] = []
        self.starter_index: int = 0
    
    def add_card(self, card: Card, player_index: int) -> None:
        """Add a card to the trick."""
        self.cards.append(card)
        self.player_indices.append(player_index)
        
        # Set starter if this is the first card
        if len(self.cards) == 1:
            self.starter_index = player_index
    
    def is_complete(self, num_players: int) -> bool:
        """Check if the trick is complete."""
        return len(self.cards) == num_players
    
    def is_empty(self) -> bool:
        """Check if the trick is empty."""
        return len(self.cards) == 0
    
    def get_asked_suit(self) -> Optional[Suit]:
        """
        Determine the asked suit for this trick.
        Returns None if trick is empty.
        """
        if self.is_empty():
            return None
        
        # If first card is excuse, look at second card
        if self.cards[0].suit == Suit.EXCUSE:
            if len(self.cards) > 1:
                return self.cards[1].suit
            else:
                return None  # Only excuse played so far
        
        return self.cards[0].suit
    
    def get_highest_trump(self) -> Optional[Card]:
        """Get the highest trump card played in this trick."""
        trump_cards = [card for card in self.cards if card.suit == Suit.TRUMP]
        if not trump_cards:
            return None
        
        return max(trump_cards, key=lambda x: x.rank.get_value())
    
    def has_trump(self) -> bool:
        """Check if any trump cards have been played."""
        return any(card.suit == Suit.TRUMP for card in self.cards)
    
    def get_winner_index(self) -> int:
        """
        Determine the winner of this trick.
        Returns the index in the original player list.
        """
        if self.is_empty():
            raise ValueError("Cannot determine winner of empty trick")
        
        # Ignore excuse cards for winner determination
        non_excuse_cards = [(i, card) for i, card in enumerate(self.cards) if card.suit != Suit.EXCUSE]
        
        # If all cards are excuses (extremely rare), first player wins
        if not non_excuse_cards:
            return self.player_indices[0]
        
        # Determine asked suit (from first non-excuse card)
        asked_suit = non_excuse_cards[0][1].suit
        
        # Filter cards by type
        asked_suit_cards = [(i, card) for i, card in non_excuse_cards if card.suit == asked_suit]
        trump_cards = [(i, card) for i, card in non_excuse_cards if card.suit == Suit.TRUMP]
        
        # If there are trumps, highest trump wins
        if trump_cards:
            winner_card_index = max(trump_cards, key=lambda x: x[1].rank.get_value())[0]
            return self.player_indices[winner_card_index]
        
        # Otherwise, highest card of asked suit wins
        if asked_suit_cards:
            winner_card_index = max(asked_suit_cards, key=lambda x: x[1].rank.get_value())[0]
            return self.player_indices[winner_card_index]
        
        # If no one followed suit and no trumps (all discarded), first non-excuse wins
        return self.player_indices[non_excuse_cards[0][0]]
    
    def clear(self) -> None:
        """Clear the trick for the next round."""
        self.cards.clear()
        self.player_indices.clear()
        self.starter_index = 0
    
    def get_legal_moves(self, player_hand: List[Card]) -> List[Card]:
        """
        Determine legal moves for a player given the current trick state.
        """
        # If hand is empty, no moves possible
        if not player_hand:
            return []
        
        # If trick is empty, any card can be played
        if self.is_empty():
            return player_hand.copy()
        
        # Excuse can ALWAYS be played
        excuse_cards = [card for card in player_hand if card.suit == Suit.EXCUSE]
        
        # Get the asked suit
        asked_suit = self.get_asked_suit()
        
        # If no asked suit yet (only excuse(s) played), any card can be played
        if asked_suit is None:
            return player_hand.copy()
        
        # Cards of the asked suit
        same_suit_cards = [card for card in player_hand if card.suit == asked_suit]
        
        # If player has cards of asked suit, they must play one (or excuse)
        if same_suit_cards:
            return same_suit_cards + excuse_cards
        
        # If asked suit is not trump and player has no cards of asked suit
        if asked_suit != Suit.TRUMP:
            trump_cards = [card for card in player_hand if card.suit == Suit.TRUMP]
            
            # If player has trumps, they must play trump (unless they play excuse)
            if trump_cards:
                highest_trump_in_trick = self.get_highest_trump()
                
                # If a trump has been played, must play higher if possible
                if highest_trump_in_trick:
                    minimum_trump_value = highest_trump_in_trick.rank.get_value()
                    higher_trumps = [card for card in trump_cards 
                                   if card.rank.get_value() > minimum_trump_value]
                    
                    # If has higher trumps, must play one (or excuse)
                    if higher_trumps:
                        return higher_trumps + excuse_cards
                    
                    # If no higher trumps, can play any trump or excuse
                    return trump_cards + excuse_cards
                
                # No trump played yet, any trump or excuse can be played
                return trump_cards + excuse_cards
        
        # Can discard anything (including excuse)
        return player_hand.copy()


def format_card_display(card: Card) -> str:
    """Convert card to display format like (co,1)"""
    if card.suit == Suit.EXCUSE:
        return "(at,0)"
    elif card.suit == Suit.TRUMP:
        # Display trump cards as 1, 2, 3... not 101, 102, 103...
        return f"(at,{card.rank.value - 100})"
    else:
        suit_map = {
            Suit.HEARTS: "co",
            Suit.SPADES: "pi", 
            Suit.DIAMONDS: "ca",
            Suit.CLUBS: "tr"
        }
        return f"({suit_map[card.suit]},{card.rank.value})"


def display_trick_state(trick: Trick, players: List) -> None:
    """Display the current state of the trick."""
    if trick.is_empty():
        print("Début du pli")
        return
    
    print("\nÉtat actuel du pli:")
    for i, card in enumerate(trick.cards):
        player_index = trick.player_indices[i]
        player = players[player_index]
        print(f"  {player.player_id}: {format_card_display(card)}")


def display_trick_final_state(trick: Trick, players: List, winner_index: int) -> None:
    """Display the final state of the trick with winner."""
    print("\nÉtat final du pli:")
    for i, card in enumerate(trick.cards):
        player_index = trick.player_indices[i]
        player = players[player_index]
        print(f"  {player.player_id}: {format_card_display(card)}")
    
    winner = players[winner_index]
    print(f"\n🏆 {winner.player_id} remporte le pli!")
    print("-" * 40)