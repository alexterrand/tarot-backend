import uuid

from tarot_logic.deck import Deck
from tarot_logic.game_state import GameState
from tarot_logic.card import Card, Suit, Rank
from tarot_logic.rules import get_legal_moves

from app.models.game import CardModel, PlayerModel, GamePublicState, PlayerHandModel
from app.services.game_logger_service import game_logger_service


class GameService:
    """
    Service qui gère les parties de Tarot.
    """
    
    def __init__(self):
        """Initialise le service avec un dictionnaire vide de parties."""
        self.games: dict[str, GameState] = {}
        self.human_players: dict[str, dict[str, str]] = {}  # game_id -> {player_id -> human_id}
    
    def create_game(self, num_players: int, human_player_id: str = "player_1") -> str:
        """
        Crée une nouvelle partie de Tarot.
        
        Args:
            num_players: Nombre de joueurs (3-5)
            human_player_id: ID du joueur humain
            
        Returns:
            ID unique de la partie créée
        """
        # Générer un ID unique pour la partie
        game_id = str(uuid.uuid4())[:8]
        
        # Créer les IDs de joueurs
        player_ids = [f"player_{i+1}" for i in range(num_players)]
        
        # Créer l'état de jeu
        game_state = GameState(player_ids)
        
        # Créer et mélanger le jeu de cartes
        deck = Deck()
        deck.shuffle()
        
        # Distribuer les cartes
        hands, dog = deck.deal(num_players)
        
        # Assigner les mains aux joueurs
        for i, player in enumerate(game_state.players):
            player.add_cards_to_hand(hands[i])
        
        # Stocker le chien
        game_state.dog = dog
        
        # Stocker l'état de jeu
        self.games[game_id] = game_state

        # Enregistrer le joueur humain
        self.human_players[game_id] = {human_player_id: human_player_id}

        print(f"Nouvelle partie créée: {game_id}")
        print(f"Joueur humain: {human_player_id}")

        # Start Supabase logging
        initial_hands = {player.player_id: list(player.hand) for player in game_state.players}
        game_logger_service.start_game_logging(game_id, game_state, initial_hands)

        return game_id
    
    def get_game_state(self, game_id: str) -> GamePublicState | None:
        """
        Récupère l'état public d'une partie.
        
        Args:
            game_id: ID de la partie
            
        Returns:
            État public de la partie ou None si la partie n'existe pas
        """
        game_state = self.games.get(game_id)
        if not game_state:
            return None
        
        # Convertir l'état du jeu en modèle public
        players = []
        for i, player in enumerate(game_state.players):
            is_human = player.player_id in self.human_players.get(game_id, {})
            players.append(
                PlayerModel(
                    id=player.player_id,
                    card_count=player.get_card_count(),
                    is_current=(i == game_state.current_player_index),
                    is_human=is_human,
                    tricks_won=len(player.tricks_won)
                )
            )
        
        # Convertir le pli courant
        current_trick = []
        for card in game_state.current_trick:
            current_trick.append(self._convert_card_to_model(card))
        
        # Créer l'état public
        return GamePublicState(
            game_id=game_id,
            players=players,
            current_trick=current_trick,
            current_player_id=game_state.get_current_player().player_id,
            is_game_over=game_state.is_game_over()
        )
    
    def get_player_hand(self, game_id: str, player_id: str) -> PlayerHandModel | None:
        """
        Récupère la main d'un joueur.
        
        Args:
            game_id: ID de la partie
            player_id: ID du joueur
            
        Returns:
            Main du joueur ou None si la partie ou le joueur n'existe pas
        """
        game_state = self.games.get(game_id)
        if not game_state:
            return None
        
        player = game_state.get_player_by_id(player_id)
        if not player:
            return None
        
        # Convertir les cartes de la main en modèles
        cards = [self._convert_card_to_model(card) for card in player.hand]
        
        return PlayerHandModel(
            player_id=player_id,
            cards=cards
        )
    
    def get_legal_moves(self, game_id: str, player_id: str) -> list[CardModel]:
        """
        Récupère les coups légaux pour un joueur.
        
        Args:
            game_id: ID de la partie
            player_id: ID du joueur
            
        Returns:
            Liste des coups légaux (cartes jouables)
        """
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        
        player = game_state.get_player_by_id(player_id)
        if not player:
            return []
        
        # Récupérer les coups légaux
        legal_moves = get_legal_moves(player.hand, game_state.current_trick)
        
        # Convertir en modèles de cartes
        return [self._convert_card_to_model(card) for card in legal_moves]
    
    def play_card(self, game_id: str, player_id: str, card_model: CardModel) -> tuple[bool, str]:
        """
        Joue une carte pour un joueur.
        
        Args:
            game_id: ID de la partie
            player_id: ID du joueur
            card_model: Modèle de la carte à jouer
            
        Returns:
            Tuple (succès, message)
        """
        game_state = self.games.get(game_id)
        if not game_state:
            return False, "Partie non trouvée"
        
        # Vérifier que c'est le tour du joueur
        current_player = game_state.get_current_player()
        if current_player.player_id != player_id:
            return False, "Ce n'est pas votre tour"
        
        # Convertir le modèle de carte en carte du jeu
        card = self._convert_model_to_card(card_model)
        if not card:
            return False, "Carte invalide"
        
        # Simplification: vérifier que le coup est légal
        legal_moves = get_legal_moves(current_player.hand, game_state.current_trick)
        if card not in legal_moves:
            return False, "Ce coup n'est pas légal"
        
        # Jouer la carte
        try:
            # Ajoutons des logs explicites
            print(f"Joueur {player_id} joue la carte {card}")
            print(f"Pli avant: {game_state.current_trick}")

            # Log card play BEFORE playing (capture state)
            hand_before = list(current_player.hand)
            trick_state_before = list(game_state.current_trick)
            position_in_trick = len(trick_state_before)

            game_logger_service.log_card_played(
                game_id=game_id,
                player_id=player_id,
                card=card,
                hand_before=hand_before,
                legal_moves=legal_moves,
                trick_state_before=trick_state_before,
                position_in_trick=position_in_trick,
                strategy_name="human",  # Human player
            )

            # Capture trick data BEFORE playing (for logging if trick completes)
            old_trick_size = len(game_state.current_trick)
            trick_cards_before_play = list(game_state.current_trick)
            trick_player_indices_before_play = list(game_state.trick_player_indices)
            current_player_index_before_play = game_state.current_player_index

            # Play the card
            game_state.play_card(game_state.current_player_index, card)
            new_trick_size = len(game_state.current_trick)
            
            print(f"Pli après: {game_state.current_trick}")
            print(f"Taille du pli: {old_trick_size} -> {new_trick_size}")
            print(f"Tour du joueur: {game_state.get_current_player().player_id}")

            # Si un pli complet vient d'être joué, le pli courant sera vide
            pli_complete = new_trick_size == 0 and old_trick_size > 0
            print(f"Pli complet? {pli_complete}")

            # Log trick completion
            if pli_complete:
                # Reconstruct full trick (add the card that was just played)
                full_trick_cards = trick_cards_before_play + [card]
                full_trick_player_indices = trick_player_indices_before_play + [current_player_index_before_play]
                winner_player_id = game_state.get_current_player().player_id  # Winner starts next trick

                game_logger_service.log_trick_completed(
                    game_id=game_id,
                    trick_cards=full_trick_cards,
                    trick_player_indices=full_trick_player_indices,
                    winner_player_id=winner_player_id,
                    game_state=game_state,
                )
            
            # Modification de la condition pour que les IA jouent:
            # Faire jouer les IA quand ce n'est pas le tour d'un joueur humain
            current_player_id = game_state.get_current_player().player_id
            is_human_turn = current_player_id in self.human_players.get(game_id, {})

            # Check if game ended
            if game_state.is_game_over():
                print("Partie terminée!")
                game_logger_service.end_game_logging(game_id, game_state)
            elif not is_human_turn:
                print("C'est au tour des IA de jouer")
                self._play_ai_turns(game_id)

            return True, "Carte jouée avec succès"
        except ValueError as e:
            return False, str(e)
    
    def _play_ai_turns(self, game_id: str) -> None:
        """
        Fait jouer les tours des joueurs IA jusqu'à ce que ce soit à nouveau le tour d'un joueur humain.
        
        Args:
            game_id: ID de la partie
        """
        print(f"Début des tours IA pour le jeu {game_id}")
        print(f"Joueurs humains: {self.human_players.get(game_id, {})}")
        
        game_state = self.games.get(game_id)
        if not game_state or game_state.is_game_over():
            print("Fin prématurée: jeu terminé ou non trouvé")
            return
        
        # Jouer tant que c'est le tour d'un joueur IA
        while not game_state.is_game_over():
            current_player = game_state.get_current_player()
            current_player_id = current_player.player_id
            
            print(f"Tour actuel: joueur {current_player_id}")
            
            # Si c'est un joueur humain, on s'arrête
            if current_player_id in self.human_players.get(game_id, {}):
                print(f"Arrêt des tours IA: tour du joueur humain {current_player_id}")
                break
            
            # Sinon, on fait jouer l'IA
            legal_moves = get_legal_moves(current_player.hand, game_state.current_trick)
            print(f"Coups légaux pour {current_player_id}: {len(legal_moves)} cartes")

            if not legal_moves:
                print(f"Pas de coup légal pour {current_player_id}")
                break  # Ne devrait pas arriver en théorie

            # Stratégie simple: jouer la première carte légale
            card_to_play = legal_moves[0]
            print(f"L'IA {current_player_id} joue {card_to_play}")

            # Log AI card play BEFORE playing
            hand_before = list(current_player.hand)
            trick_state_before = list(game_state.current_trick)
            position_in_trick = len(trick_state_before)

            game_logger_service.log_card_played(
                game_id=game_id,
                player_id=current_player_id,
                card=card_to_play,
                hand_before=hand_before,
                legal_moves=legal_moves,
                trick_state_before=trick_state_before,
                position_in_trick=position_in_trick,
                strategy_name="bot-random",  # V1 AI is random (first legal move)
            )

            # Capture trick data BEFORE playing
            old_trick_size = len(game_state.current_trick)
            trick_cards_before_play = list(game_state.current_trick)
            trick_player_indices_before_play = list(game_state.trick_player_indices)
            current_player_index_before_play = game_state.current_player_index

            # Play the card
            game_state.play_card(game_state.current_player_index, card_to_play)
            new_trick_size = len(game_state.current_trick)
            
            print(f"Pli après jeu de l'IA: {game_state.current_trick}")
            print(f"Taille du pli: {old_trick_size} -> {new_trick_size}")

            # Check trick completion and log
            pli_complete = new_trick_size == 0 and old_trick_size > 0
            if pli_complete:
                print("Pli complet, l'IA continue à jouer si c'est son tour")

                # Reconstruct full trick and log
                full_trick_cards = trick_cards_before_play + [card_to_play]
                full_trick_player_indices = trick_player_indices_before_play + [current_player_index_before_play]
                winner_player_id = game_state.get_current_player().player_id

                game_logger_service.log_trick_completed(
                    game_id=game_id,
                    trick_cards=full_trick_cards,
                    trick_player_indices=full_trick_player_indices,
                    winner_player_id=winner_player_id,
                    game_state=game_state,
                )

            # Check if game ended
            if game_state.is_game_over():
                print("Partie terminée (IA)")
                game_logger_service.end_game_logging(game_id, game_state)
                break
    
    def _convert_card_to_model(self, card: Card) -> CardModel:
        """
        Convertit une carte du jeu en modèle pour l'API.
        
        Args:
            card: Carte du jeu
            
        Returns:
            Modèle de carte pour l'API
        """
        return CardModel(
            suit=card.suit.name,
            rank=card.rank.get_value(),
            display_name=str(card)
        )
    
    def _convert_model_to_card(self, card_model: CardModel) -> Card | None:
        """
        Convertit un modèle de carte en carte du jeu.
        
        Args:
            card_model: Modèle de carte
            
        Returns:
            Carte du jeu ou None si la conversion échoue
        """
        try:
            # Convertir la couleur
            suit = getattr(Suit, card_model.suit)
            
            # Convertir le rang
            is_trump = (suit == Suit.TRUMP)
            rank = Rank.from_int(card_model.rank, is_trump=is_trump)
            
            return Card(suit=suit, rank=rank)
        except (AttributeError, ValueError):
            return None