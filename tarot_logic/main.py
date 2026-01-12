import sys
from .card import Card, Suit, Rank
from .deck import Deck
from .player import Player
from .game_state import GameState
from .trick import Trick, format_card_display, display_trick_state, display_trick_final_state
from .bots import create_strategy, BotStrategy


class TarotGame:
    def __init__(self):
        self.deck = Deck()
        self.game_state = None
        self.human_player_index = 0
        self.taker_index = None
        self.dog = []
        self.discarded_cards = []
        self.current_trick = Trick()  # Use our new Trick class

        # Bot strategies for AI players
        self.bot_strategies: dict[str, BotStrategy] = {
            "IA1": create_strategy("bot-naive"),
            "IA2": create_strategy("bot-random"),
            "IA3": create_strategy("bot-naive"),
        }
        
    def start_new_game(self):
        """Start a new game of Tarot"""
        print("\n" + "="*50)
        print("NOUVELLE PARTIE DE TAROT")
        print("="*50)
        
        # Create players
        player_ids = ["Vous", "IA1", "IA2", "IA3"]
        self.game_state = GameState(player_ids)
        
        # Reset deck and shuffle
        self.deck = Deck()
        self.deck.shuffle()
        hands, self.dog = self.deck.deal(4)
        
        # Give cards to players
        for i, hand in enumerate(hands):
            self.game_state.players[i].add_cards_to_hand(hand)
        
        print(f"\nDistribution terminée. Chien: {len(self.dog)} cartes")
        
        # Display human hand
        self.display_human_hand()
        
        # Bidding phase
        self.bidding_phase()
        
        # If human took, handle dog and discard
        if self.taker_index == self.human_player_index:
            self.handle_dog_and_discard()
            self.display_human_hand()
        
        # Play the game
        self.play_game()
        
        # Show final results
        self.show_final_results()
    
    def display_human_hand(self):
        """Display the human player's hand organized by suits"""
        human = self.game_state.players[self.human_player_index]
        hand = human.hand
        
        # Organize cards by suit
        suits = {
            Suit.HEARTS: [],
            Suit.SPADES: [],
            Suit.DIAMONDS: [],
            Suit.CLUBS: [],
            Suit.TRUMP: [],
            Suit.EXCUSE: []
        }
        
        for card in hand:
            suits[card.suit].append(card)
        
        # Sort each suit by rank value
        for suit in suits:
            suits[suit].sort(key=lambda x: x.rank.value)
        
        print(f"\nVotre main ({len(hand)} cartes):")
        print("-" * 40)
        print(f"Coeur:   {self.format_cards_for_display(suits[Suit.HEARTS])}")
        print(f"Pique:   {self.format_cards_for_display(suits[Suit.SPADES])}")
        print(f"Carreau: {self.format_cards_for_display(suits[Suit.DIAMONDS])}")
        print(f"Trèfle:  {self.format_cards_for_display(suits[Suit.CLUBS])}")
        
        # Combine trump and excuse for atout line
        atout_cards = suits[Suit.TRUMP] + suits[Suit.EXCUSE]
        atout_cards.sort(key=lambda x: x.rank.value)
        print(f"Atout:   {self.format_cards_for_display(atout_cards)}")
        print("-" * 40)
    
    def format_cards_for_display(self, cards):
        """Format cards for display according to the specified format"""
        if not cards:
            return ""
        
        display_values = []
        for card in cards:
            if card.suit == Suit.EXCUSE:
                display_values.append("0")
            elif card.suit == Suit.TRUMP:
                # Display trump cards as 1, 2, 3... not 101, 102, 103...
                display_values.append(str(card.rank.value - 100))
            else:
                display_values.append(str(card.rank.value))
        
        return ", ".join(display_values)
    
    def bidding_phase(self):
        """Handle the bidding phase"""
        print("\n--- PHASE D'ENCHÈRES ---")
        
        # For now, only human can take (AI cannot in v0)
        while True:
            response = input("Voulez-vous prendre? (oui/non): ").strip().lower()
            
            if response in ["oui", "o", "yes", "y", "je prend", "prendre"]:
                self.taker_index = self.human_player_index
                print("Vous prenez!")
                break
            elif response in ["non", "n", "no", "passe"]:
                print("Vous passez.")
                print("Personne ne prend. Redistribution...")
                self.start_new_game()
                return
            elif response == "relaunch":
                print("Nouvelle partie!")
                self.start_new_game()
                return
            else:
                print("Répondez par 'oui' ou 'non'")
    
    def handle_dog_and_discard(self):
        """Handle taking the dog and discarding"""
        # Add dog to human hand
        human = self.game_state.players[self.human_player_index]
        
        print(f"\nLe chien contient: {', '.join([str(card) for card in self.dog])}")
        human.add_cards_to_hand(self.dog)
        
        dog_size = len(self.dog)
        print(f"\n--- PHASE D'ÉCART ---")
        print(f"Vous devez faire votre écart (choisir {dog_size} cartes à écarter):")
        print("Format: (co,1) pour As de Coeur, (pi,14) pour Roi de Pique, etc.")
        print("co=coeur, pi=pique, ca=carreau, tr=trèfle, at=atout")
        print("Pour l'excuse: (at,0)")
        print("Pour les atouts: (at,1) pour le 1 d'atout, (at,21) pour le 21 d'atout")
        
        self.display_human_hand()
        
        discarded_cards = []
        while len(discarded_cards) < dog_size:
            try:
                card_input = input(f"Carte {len(discarded_cards)+1}/{dog_size} à écarter: ").strip()
                
                if card_input.lower() == "relaunch":
                    print("Nouvelle partie!")
                    self.start_new_game()
                    return
                
                card = self.parse_card_input(card_input)
                
                if not human.has_card(card):
                    print("Vous n'avez pas cette carte!")
                    continue
                
                if card in discarded_cards:
                    print("Vous avez déjà écarté cette carte!")
                    continue
                
                discarded_cards.append(card)
                human.play_card(card)
                print(f"Carte écartée: {card}")
                
            except Exception as e:
                print(f"Format invalide: {e}")
                print("Exemple: (co,1) pour As de Coeur, (at,1) pour le 1 d'atout")
        
        # Store discarded cards (they go to the taker at the end)
        self.discarded_cards = discarded_cards
        print("Écart terminé!")
    
    def parse_card_input(self, input_str):
        """Parse card input in format (suit,rank)"""
        input_str = input_str.strip().strip("()")
        parts = input_str.split(",")
        
        if len(parts) != 2:
            raise ValueError("Format: (suit,rank)")
        
        suit_str = parts[0].strip()
        rank_str = parts[1].strip()
        
        # Parse suit
        suit_map = {
            "co": Suit.HEARTS,
            "pi": Suit.SPADES,
            "ca": Suit.DIAMONDS,
            "tr": Suit.CLUBS,
            "at": Suit.TRUMP
        }
        
        if suit_str not in suit_map:
            raise ValueError("Suit must be co, pi, ca, tr, or at")
        
        try:
            rank_value = int(rank_str)
        except ValueError:
            raise ValueError("Rank must be a number")
        
        # Special case for excuse
        if rank_value == 0:
            return Card(Suit.EXCUSE, Rank.EXCUSE)
        
        suit = suit_map[suit_str]
        
        # Parse rank based on suit
        if suit == Suit.TRUMP:
            if 1 <= rank_value <= 21:
                # User enters 1-21, but internally we need 101-121
                rank = Rank.from_int(rank_value, is_trump=True)
            else:
                raise ValueError("Trump cards must be 1-21 (or 0 for excuse)")
        else:
            if 1 <= rank_value <= 14:
                rank = Rank.from_int(rank_value, is_trump=False)
            else:
                raise ValueError("Regular cards must be 1-14")
        
        return Card(suit, rank)
    
    def play_game(self):
        """Main game loop"""
        print("\n" + "="*30)
        print("DÉBUT DE LA PARTIE!")
        print("="*30)
        
        trick_number = 1
        
        while not self.game_state.is_game_over():
            print(f"\n🃏 PLI {trick_number} 🃏")
            self.play_trick()
            trick_number += 1
    
    def play_trick(self):
        """Play one complete trick"""
        # Reset trick for new round
        self.current_trick.clear()
        
        # Play until all players have played
        while not self.current_trick.is_complete(4):
            current_player_index = self.game_state.current_player_index
            current_player = self.game_state.players[current_player_index]
            
            if current_player_index == self.human_player_index:
                self.human_play_turn()
            else:
                self.ai_play_turn(current_player_index)
        
        # Determine winner
        winner_index = self.current_trick.get_winner_index()
        winner = self.game_state.players[winner_index]
        
        # Give trick to winner
        winner.add_trick(self.current_trick.cards.copy())
        
        # Display final state
        display_trick_final_state(self.current_trick, self.game_state.players, winner_index)
        
        # Set next player to start (winner starts next trick)
        self.game_state.current_player_index = winner_index
    
    def display_current_trick_state(self):
        """Display the current state of the trick"""
        display_trick_state(self.current_trick, self.game_state.players)
    

    
    def human_play_turn(self):
        """Handle human player's turn"""
        print(f"\n🎯 C'est votre tour!")
        
        # Display current trick state
        self.display_current_trick_state()
        
        # Display hand
        self.display_human_hand()
        
        human = self.game_state.players[self.human_player_index]
        legal_moves = self.current_trick.get_legal_moves(human.hand)
        
        # Show legal moves if restricted
        if len(legal_moves) < len(human.hand):
            print("⚠️  Cartes légales seulement:")
            legal_display = [format_card_display(card) for card in legal_moves]
            print(f"   {', '.join(legal_display)}")
        
        while True:
            try:
                card_input = input("\nQuelle carte voulez-vous jouer? ").strip()
                
                if card_input.lower() == "relaunch":
                    print("Nouvelle partie!")
                    self.start_new_game()
                    return
                
                card = self.parse_card_input(card_input)
                
                if card not in legal_moves:
                    print("❌ Cette carte n'est pas légale dans cette situation!")
                    continue
                
                # Play the card
                human.play_card(card)
                self.current_trick.add_card(card, self.human_player_index)
                
                print(f"✅ Vous jouez: {card}")
                
                # Move to next player
                self.game_state.current_player_index = (self.game_state.current_player_index + 1) % 4
                break
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
                print("Exemple: (co,1) pour As de Coeur, (at,1) pour le 1 d'Atout")
    
    def ai_play_turn(self, ai_index):
        """Handle AI player's turn using strategy pattern."""
        ai_player = self.game_state.players[ai_index]
        legal_moves = self.current_trick.get_legal_moves(ai_player.hand)

        # Use strategy to choose card
        strategy = self.bot_strategies[ai_player.player_id]
        card_to_play = strategy.choose_card(
            hand=ai_player.hand,
            legal_moves=legal_moves,
            current_trick=self.current_trick
        )

        # Play the card
        ai_player.play_card(card_to_play)
        self.current_trick.add_card(card_to_play, ai_index)

        # Enhanced logging with strategy name
        strategy_name = strategy.get_strategy_name()
        print(f"🤖 {ai_player.player_id} ({strategy_name}) joue: {format_card_display(card_to_play)}")

        # Move to next player
        self.game_state.current_player_index = (self.game_state.current_player_index + 1) % 4
        
        # Brief pause for readability
        import time
        time.sleep(1)
    
    def _calculate_score(self, cards: list[Card]) -> tuple[float, int]:
        """Calcule le total des points et le nombre de Bouts (Oudlers) d'une liste de cartes."""
        total_points = sum(card.get_points() for card in cards)
        
        oudlers = [
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.TRUMP, Rank.TRUMP_1),
            Card(Suit.TRUMP, Rank.TRUMP_21)
        ]
        
        num_oudlers = sum(1 for card in cards if card in oudlers)
        
        return total_points, num_oudlers

    def show_final_results(self):
        """Affiche les résultats finaux de la partie avec le décompte des points."""
        print("\n" + "="*40)
        print("FIN DE LA PARTIE !")
        print("="*40)

        if self.taker_index is None:
            print("La partie s'est terminée sans preneur.")
            return

        # Le preneur et les défenseurs
        taker = self.game_state.players[self.taker_index]
        defenders = [p for i, p in enumerate(self.game_state.players) if i != self.taker_index]

        # Récupérer toutes les cartes remportées par le preneur (plis + écart)
        taker_cards = []
        for trick in taker.tricks_won:
            taker_cards.extend(trick)
        taker_cards.extend(self.discarded_cards)

        # Calculer le score du preneur
        taker_score, taker_oudlers = self._calculate_score(taker_cards)

        # Contrat à remplir en fonction du nombre de Bouts
        contracts = {
            0: 56,
            1: 51,
            2: 41,
            3: 36
        }
        required_score = contracts[taker_oudlers]

        print(f"Preneur : {taker.player_id}")
        print(f"Bouts possédés : {taker_oudlers}")
        print(f"Contrat à réaliser : {required_score} points")
        print(f"Score réalisé : {taker_score} points")
        print("-" * 20)

        # Déterminer le résultat
        if taker_score >= required_score:
            print("✅ Contrat REMPLI ! ✅")
            print(f"Le gagnant est : {taker.player_id}")
        else:
            difference = required_score - taker_score
            print(f"❌ Contrat CHUTÉ de {difference} points ! ❌")
            defender_names = ", ".join([p.player_id for p in defenders])
            print(f"Les gagnants sont (la défense) : {defender_names}")

        print("\n" + "="*40)
        print("\nTapez 'relaunch' pour une nouvelle partie ou Ctrl+C pour quitter.")


def main():
    """Main function to run the Tarot game"""
    print("🎴" * 20)
    print("    TAROT FRANÇAIS")
    print("🎴" * 20)
    print("\nBienvenue dans le jeu de Tarot!")
    print("Vous jouez contre 3 IA.")
    print("Tapez 'relaunch' à tout moment pour recommencer.")
    print("\nFormat des cartes: (suit,rank)")
    print("  • co=coeur, pi=pique, ca=carreau, tr=trèfle, at=atout")
    print("  • Exemples: (co,1)=As de Coeur, (at,1)=1 d'Atout, (at,0)=Excuse")
    
    game = TarotGame()
    
    while True:
        try:
            response = input("\nCommencer une partie? (oui/non): ").strip().lower()
            if response in ["non", "n", "no", "quit", "exit"]:
                break
            elif response in ["oui", "o", "yes", "y", ""]:
                game.start_new_game()
            else:
                print("Répondez par 'oui' ou 'non'")
                
        except KeyboardInterrupt:
            print("\n\nAu revoir! 👋")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}")
            response = input("Voulez-vous continuer? (oui/non): ")
            if response.lower() not in ["oui", "o", "yes", "y"]:
                break


if __name__ == "__main__":
    main()