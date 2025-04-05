import pytest
from tarot_logic.card import Card, Suit, Rank, _STANDARD_RANKS, _TRUMP_RANKS


class TestCard:
    def test_card_creation(self):
        """Test de la création de cartes valides."""
        # Carte couleur
        card = Card(suit=Suit.HEARTS, rank=Rank.KING)
        assert card.suit == Suit.HEARTS
        assert card.rank == Rank.KING
        assert card._rank_value == 14

        # Atout
        trump = Card(suit=Suit.TRUMP, rank=Rank.TRUMP_5)
        assert trump.suit == Suit.TRUMP
        assert trump.rank == Rank.TRUMP_5
        assert trump._rank_value == 5

        # Excuse
        excuse = Card(suit=Suit.EXCUSE, rank=Rank.EXCUSE)
        assert excuse.suit == Suit.EXCUSE
        assert excuse.rank == Rank.EXCUSE
        assert excuse._rank_value == 0

    def test_invalid_card_creation(self):
        """Test des erreurs lors de la création de cartes invalides."""
        # Excuse avec un mauvais rang
        with pytest.raises(ValueError):
            Card(suit=Suit.EXCUSE, rank=Rank.ACE)

        # Atout avec un rang de couleur
        with pytest.raises(ValueError):
            Card(suit=Suit.TRUMP, rank=Rank.KING)

        # Couleur avec un rang d'atout
        with pytest.raises(ValueError):
            Card(suit=Suit.CLUBS, rank=Rank.TRUMP_10)

    def test_card_comparison(self):
        """Test de la comparaison entre cartes."""
        # L'excuse est toujours inférieure
        excuse = Card(suit=Suit.EXCUSE, rank=Rank.EXCUSE)
        hearts_ace = Card(suit=Suit.HEARTS, rank=Rank.ACE)
        assert excuse < hearts_ace

        # Comparaison entre cartes de même couleur
        hearts_7 = Card(suit=Suit.HEARTS, rank=Rank.SEVEN)
        hearts_king = Card(suit=Suit.HEARTS, rank=Rank.KING)
        assert hearts_7 < hearts_king

        # Un atout est supérieur à une carte de couleur
        trump_1 = Card(suit=Suit.TRUMP, rank=Rank.TRUMP_1)
        assert hearts_king < trump_1

        # Comparaison entre atouts
        trump_5 = Card(suit=Suit.TRUMP, rank=Rank.TRUMP_5)
        trump_10 = Card(suit=Suit.TRUMP, rank=Rank.TRUMP_10)
        assert trump_5 < trump_10

    def test_card_equality(self):
        """Test de l'égalité entre cartes."""
        card1 = Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN)
        card2 = Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN)
        card3 = Card(suit=Suit.DIAMONDS, rank=Rank.KING)

        assert card1 == card2
        assert card1 != card3

    def test_string_representation(self):
        """Test de la représentation textuelle des cartes."""
        # Cartes de couleur
        assert str(Card(suit=Suit.HEARTS, rank=Rank.ACE)) == "As de Coeur"
        assert str(Card(suit=Suit.CLUBS, rank=Rank.SEVEN)) == "7 de Trèfle"
        assert str(Card(suit=Suit.SPADES, rank=Rank.KING)) == "Roi de Pique"

        # Atouts
        assert str(Card(suit=Suit.TRUMP, rank=Rank.TRUMP_1)) == "Atout 1"
        assert str(Card(suit=Suit.TRUMP, rank=Rank.TRUMP_21)) == "Atout 21"

        # Excuse
        assert str(Card(suit=Suit.EXCUSE, rank=Rank.EXCUSE)) == "Excuse"

    def test_rank_from_int(self):
        """Test de la création d'un rang à partir d'un entier."""
        assert Rank.from_int(1) == Rank.ACE
        assert Rank.from_int(10) == Rank.TEN
        assert Rank.from_int(14) == Rank.KING

        assert Rank.from_int(5, is_trump=True) == Rank.TRUMP_5
        assert Rank.from_int(21, is_trump=True) == Rank.TRUMP_21

        assert Rank.from_int(0) == Rank.EXCUSE

        with pytest.raises(ValueError):
            Rank.from_int(30)

    def test_conversion_dictionaries(self):
        """Test des dictionnaires de conversion."""
        # Vérifier la taille des dictionnaires
        assert len(_STANDARD_RANKS) == 15  # 1-14 pour les couleurs
        assert len(_TRUMP_RANKS) == 21  # 1-21 pour les atouts

        # Vérifier quelques valeurs spécifiques
        assert _STANDARD_RANKS[1] == Rank.ACE
        assert _STANDARD_RANKS[14] == Rank.KING
        assert _TRUMP_RANKS[1] == Rank.TRUMP_1
        assert _TRUMP_RANKS[21] == Rank.TRUMP_21
