from enum import Enum
from dataclasses import dataclass, field


class Suit(Enum):
    """
    Représente les couleurs des cartes au Tarot.
    """

    CLUBS = "Trèfle"  # Trèfle
    DIAMONDS = "Carreau"  # Carreau
    HEARTS = "Coeur"  # Coeur
    SPADES = "Pique"  # Pique
    TRUMP = "Atout"  # Atout
    EXCUSE = "Excuse"  # Excuse (techniquement pas une couleur mais facilite la logique)


class Rank(Enum):
    """
    Représente les valeurs des cartes au Tarot.
    Pour les couleurs (CLUBS, DIAMONDS, HEARTS, SPADES):
    - ACE (1), 2-10, JACK (Valet), KNIGHT (Cavalier), QUEEN (Dame), KING (Roi)
    Pour les atouts:
    - TRUMP_1 à TRUMP_21 pour les atouts numérotés
    Pour l'excuse:
    - EXCUSE
    """

    # Valeurs pour les couleurs
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    KNIGHT = 12
    QUEEN = 13
    KING = 14

    # Valeurs pour les atouts (1-21)
    TRUMP_1 = 101
    TRUMP_2 = 102
    TRUMP_3 = 103
    TRUMP_4 = 104
    TRUMP_5 = 105
    TRUMP_6 = 106
    TRUMP_7 = 107
    TRUMP_8 = 108
    TRUMP_9 = 109
    TRUMP_10 = 110
    TRUMP_11 = 111
    TRUMP_12 = 112
    TRUMP_13 = 113
    TRUMP_14 = 114
    TRUMP_15 = 115
    TRUMP_16 = 116
    TRUMP_17 = 117
    TRUMP_18 = 118
    TRUMP_19 = 119
    TRUMP_20 = 120
    TRUMP_21 = 121

    # Pour l'excuse
    EXCUSE = 0

    def get_value(self) -> int:
        """
        Retourne la valeur numérique pour la comparaison de cartes.
        """
        if self.value == 0:  # EXCUSE
            return 0
        if isinstance(self.value, int) and self.value < 100:  # Couleurs
            return self.value
        if isinstance(self.value, int) and self.value >= 100:  # Atouts
            return self.value - 100
        return 0


# Dictionnaires pour la conversion valeur -> Rank (optimisation)
_STANDARD_RANKS: dict[int, Rank] = {}
_TRUMP_RANKS: dict[int, Rank] = {}

# Initialisation immédiate des dictionnaires
for rank in Rank:
    value = rank.value
    if isinstance(value, int):
        if value < 100:  # Cartes normales
            _STANDARD_RANKS[value] = rank
        elif 100 <= value <= 121:  # Atouts
            _TRUMP_RANKS[value - 100] = rank


def rank_from_int(value: int, is_trump: bool = False) -> Rank:
    """
    Crée un Rank à partir d'une valeur entière.

    Args:
        value: La valeur numérique
        is_trump: Indique si c'est un atout

    Returns:
        Une instance de Rank correspondante
    """
    # Cas spécial: l'excuse
    if value == 0:
        return Rank.EXCUSE

    # Recherche dans le dictionnaire approprié
    if is_trump:
        if value in _TRUMP_RANKS:
            return _TRUMP_RANKS[value]
    else:
        if value in _STANDARD_RANKS:
            return _STANDARD_RANKS[value]

    # Si on arrive ici, la valeur est invalide
    raise ValueError(f"Valeur invalide: {value} (is_trump={is_trump})")


# Attacher la fonction comme méthode de classe à Rank pour compatibilité API
setattr(Rank, "from_int", staticmethod(rank_from_int))


@dataclass
class Card:
    """
    Représente une carte du jeu de Tarot.
    """

    suit: Suit
    rank: Rank
    _rank_value: int = field(init=False, repr=False)  # Valeur précalculée

    def __post_init__(self):
        """
        Vérifie la cohérence entre suit et rank et pré-calcule la valeur de rang.
        """
        # Vérifie que l'excuse a bien le rang EXCUSE
        if self.suit == Suit.EXCUSE and self.rank != Rank.EXCUSE:
            raise ValueError("L'Excuse doit avoir le rang EXCUSE")

        # Vérifie que les atouts ont bien des rangs d'atouts
        if self.suit == Suit.TRUMP and not (100 <= self.rank.value <= 121):
            raise ValueError(f"Les atouts doivent avoir un rang entre 1 et 21, pas {self.rank}")

        # Vérifie que les couleurs ont bien des rangs de couleurs
        if self.suit in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            if not (1 <= self.rank.value <= 14):
                raise ValueError(f"Les cartes de couleur doivent avoir un rang entre 1 et 14, pas {self.rank}")

        # Précalculer la valeur de rang
        self._rank_value = self.rank.get_value()

    def __lt__(self, other: "Card") -> bool:
        """
        Compare deux cartes pour déterminer laquelle est inférieure.
        Utilisée pour trier les cartes.
        """
        if not isinstance(other, Card):
            return NotImplemented

        # L'excuse est toujours considérée comme la carte la plus faible
        if self.suit == Suit.EXCUSE:
            return True
        if other.suit == Suit.EXCUSE:
            return False

        # Si les deux cartes sont de la même couleur, on compare leur rang
        if self.suit == other.suit:
            return self._rank_value < other._rank_value

        # Les atouts sont supérieurs aux cartes de couleur
        if self.suit == Suit.TRUMP:
            return False
        if other.suit == Suit.TRUMP:
            return True

        # Pour les couleurs différentes, on trie par couleur
        return self.suit.value < other.suit.value

    def __eq__(self, other: object) -> bool:
        """
        Vérifie si deux cartes sont égales.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

    def __str__(self) -> str:
        """
        Retourne une représentation textuelle de la carte.
        """
        if self.suit == Suit.EXCUSE:
            return "Excuse"
        if self.suit == Suit.TRUMP:
            return f"Atout {self._rank_value}"

        # Pour les cartes de couleur
        rank_names = {Rank.ACE: "As", Rank.JACK: "Valet", Rank.KNIGHT: "Cavalier", Rank.QUEEN: "Dame", Rank.KING: "Roi"}

        if self.rank in rank_names:
            return f"{rank_names[self.rank]} de {self.suit.value}"
        return f"{self._rank_value} de {self.suit.value}"
