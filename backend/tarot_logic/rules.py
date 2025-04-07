from .card import Card, Suit

def get_legal_moves(player_hand: list[Card], current_trick: list[Card], trump_suit: Suit = Suit.TRUMP) -> list[Card]:
    """
    Détermine les coups légaux pour un joueur dans une situation donnée.
    
    Args:
        player_hand: La main du joueur
        current_trick: Le pli en cours
        trump_suit: La couleur d'atout (par défaut Suit.TRUMP)
    
    Returns:
        Liste des cartes que le joueur peut légalement jouer
    """
    # Si la main est vide, pas de coups possibles
    if not player_hand:
        return []
    
    # Si c'est le début du pli, le joueur peut jouer n'importe quelle carte
    if not current_trick:
        return player_hand.copy()
    
    # Si la première carte jouée est l'excuse
    if current_trick[0].suit == Suit.EXCUSE:
        if len(current_trick) == 1:
            return player_hand.copy()  # Si l'excuse est la seule carte, on peut jouer n'importe quoi
        else:
            asked_suit = current_trick[1].suit  # Sinon, la couleur demandée est celle de la deuxième carte
    else:
        # Déterminer la couleur demandée (la couleur de la première carte jouée)
        asked_suit = current_trick[0].suit
    
    # Liste des cartes que le joueur a dans la couleur demandée
    same_suit_cards = [card for card in player_hand if card.suit == asked_suit]
    
    # Si le joueur a des cartes de la couleur demandée, il doit en jouer une
    if same_suit_cards:
        return same_suit_cards
    
    # Si la couleur demandée n'est pas de l'atout et que le joueur a des atouts
    if asked_suit != trump_suit:
        trump_cards = [card for card in player_hand if card.suit == trump_suit]
        
        # Vérifier si quelqu'un a déjà joué de l'atout dans ce pli
        highest_trump_in_trick = None
        for card in current_trick:
            if card.suit == trump_suit:
                if highest_trump_in_trick is None or card.rank.get_value() > highest_trump_in_trick.rank.get_value():
                    highest_trump_in_trick = card
        
        # Si un atout a déjà été joué, le joueur doit jouer un atout supérieur s'il en a
        if highest_trump_in_trick and trump_cards:
            higher_trumps = [card for card in trump_cards if card.rank.get_value() > highest_trump_in_trick.rank.get_value()]
            if higher_trumps:
                return higher_trumps
        
        # Si le joueur a des atouts (et soit aucun atout n'a été joué, soit il n'a pas d'atouts supérieurs)
        if trump_cards:
            return trump_cards
    
    # Sinon, le joueur peut jouer n'importe quelle carte (défausse)
    return player_hand.copy()

def get_trick_winner(trick: list[Card], trump_suit: Suit = Suit.TRUMP) -> int:
    """
    Détermine l'index du joueur qui remporte le pli.
    
    Args:
        trick: Liste des cartes jouées dans le pli
        trump_suit: La couleur d'atout
    
    Returns:
        Index (dans la liste trick) de la carte gagnante
    
    Raises:
        ValueError: Si le pli est vide
    """
    if not trick:
        raise ValueError("Le pli est vide")
    
    # Ignorer l'Excuse pour la détermination du gagnant
    non_excuse_cards = [(i, card) for i, card in enumerate(trick) if card.suit != Suit.EXCUSE]
    
    # Si toutes les cartes sont des Excuses (cas extrêmement rare), la première gagne
    if not non_excuse_cards:
        return 0
    
    # Déterminer la couleur demandée (première carte non-Excuse)
    asked_suit = non_excuse_cards[0][1].suit
    
    # Filtrer les cartes de la couleur demandée et les atouts
    asked_suit_cards = [(i, card) for i, card in non_excuse_cards if card.suit == asked_suit]
    trump_cards = [(i, card) for i, card in non_excuse_cards if card.suit == trump_suit]
    
    # S'il y a des atouts, l'atout le plus fort gagne
    if trump_cards:
        return max(trump_cards, key=lambda x: x[1].rank.get_value())[0]
    
    # Sinon, la carte la plus forte de la couleur demandée gagne
    if asked_suit_cards:
        return max(asked_suit_cards, key=lambda x: x[1].rank.get_value())[0]
    
    # Si ni atouts ni couleur demandée (tous se sont défaussés), la première carte non-Excuse gagne
    return non_excuse_cards[0][0]