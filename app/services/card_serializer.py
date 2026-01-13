"""Card serialization utilities for database storage.

Provides functions to convert Card objects to/from string format for JSONB storage.
Format: "(suit_code,rank_value)" - e.g., "(co,14)" for King of Hearts
"""

from tarot_logic.card import Card, Rank, Suit


# Suit code mappings
SUIT_TO_CODE = {
    Suit.HEARTS: "co",      # Coeur
    Suit.SPADES: "pi",      # Pique
    Suit.DIAMONDS: "ca",    # Carreau
    Suit.CLUBS: "tr",       # Trèfle
    Suit.TRUMP: "at",       # Atout
    Suit.EXCUSE: "ex",      # Excuse
}

CODE_TO_SUIT = {v: k for k, v in SUIT_TO_CODE.items()}


def card_to_str(card: Card) -> str:
    """Serialize a Card to string format.

    Args:
        card: Card object to serialize

    Returns:
        String in format "(suit_code,rank_value)"
        Examples: "(co,14)" for King of Hearts, "(at,21)" for Trump 21

    Examples:
        >>> card_to_str(Card(Suit.HEARTS, Rank.KING))
        "(co,14)"
        >>> card_to_str(Card(Suit.TRUMP, Rank.TRUMP_21))
        "(at,121)"
    """
    suit_code = SUIT_TO_CODE[card.suit]
    rank_value = card.rank.get_value()
    return f"({suit_code},{rank_value})"


def cards_to_list(cards: list[Card]) -> list[str]:
    """Serialize a list of Cards to list of strings.

    Args:
        cards: List of Card objects

    Returns:
        List of serialized card strings

    Examples:
        >>> cards_to_list([Card(Suit.HEARTS, Rank.ACE), Card(Suit.TRUMP, Rank.TRUMP_1)])
        ["(co,1)", "(at,101)"]
    """
    return [card_to_str(card) for card in cards]


def str_to_card(card_str: str) -> Card:
    """Deserialize a string to Card object.

    Args:
        card_str: String in format "(suit_code,rank_value)"

    Returns:
        Card object

    Raises:
        ValueError: If string format is invalid

    Examples:
        >>> str_to_card("(co,14)")
        Card(Suit.HEARTS, Rank.KING)
    """
    # Remove parentheses and split
    if not card_str.startswith("(") or not card_str.endswith(")"):
        raise ValueError(f"Invalid card string format: {card_str}")

    content = card_str[1:-1]
    parts = content.split(",")

    if len(parts) != 2:
        raise ValueError(f"Invalid card string format: {card_str}")

    suit_code, rank_value_str = parts

    # Convert suit code to Suit
    if suit_code not in CODE_TO_SUIT:
        raise ValueError(f"Unknown suit code: {suit_code}")
    suit = CODE_TO_SUIT[suit_code]

    # Convert rank value to Rank
    try:
        rank_value = int(rank_value_str)
    except ValueError:
        raise ValueError(f"Invalid rank value: {rank_value_str}")

    # Find matching Rank enum
    for rank in Rank:
        if rank.get_value() == rank_value:
            return Card(suit, rank)

    raise ValueError(f"No rank found for value: {rank_value}")


def list_to_cards(card_strings: list[str]) -> list[Card]:
    """Deserialize a list of strings to list of Cards.

    Args:
        card_strings: List of serialized card strings

    Returns:
        List of Card objects

    Examples:
        >>> list_to_cards(["(co,1)", "(at,101)"])
        [Card(Suit.HEARTS, Rank.ACE), Card(Suit.TRUMP, Rank.TRUMP_1)]
    """
    return [str_to_card(card_str) for card_str in card_strings]
