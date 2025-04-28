"""Display functions for visualizing Solitaire game state."""
from . import reader

# This function is specifically for printing to console, so I'm removing it completely as it consists entirely of print statements
# def print_game_state(game_state):
#    """Print game state to console."""
#    ...


def format_game_state(game_state):
    """
    Format game state into a string representation for display.

    Args:
        game_state: Dictionary containing the complete game state

    Returns:
        String with formatted representation of the game state
    """
    output = []

    # Check for errors in the game state
    error_msg = game_state.get("error")
    if error_msg and "handle" not in error_msg.lower() and "process" not in error_msg.lower():
        output.append(f"Error reading game state: {error_msg}")

    piles = game_state.get("piles")
    if not isinstance(piles, list):
        output.append("Piles data missing or invalid.")
        return "\n".join(output)

    output.append("===== SOLITAIRE GAME STATE =====")
    reader.assign_pile_names(game_state)

    # Format stock and waste piles
    for pile_idx in [0, 1]:  # Deck & Talon
        if pile_idx < len(piles):
            pile = piles[pile_idx]
            if not isinstance(pile, dict):
                output.append(f"Pile {pile_idx} invalid.")
                continue

            pile_name = pile.get('name', '?')
            card_count = pile.get('count', '?')
            pile_desc = f"{pile_name:5} [{card_count:2} cards]: "
            cards = pile.get("cards")

            if cards is None and pile.get('address', 0) != 0:
                pile_desc += "Read Error"
            elif card_count > 0 and isinstance(cards, list) and cards:
                if pile_idx == 1:  # Waste
                    top_card = cards[-1]
                    if top_card.get("face_up"):
                        pile_desc += f"Top: {top_card.get('desc', 'Error')}"
                    else:
                        pile_desc += "Top: Face Down"
                elif pile_idx == 0:  # Stock
                    pile_desc += f"{card_count} cards face down"
            else:
                pile_desc += "Empty"

            output.append(pile_desc)
        else:
            output.append(f"Pile {pile_idx} data missing.")

    output.append("")

    # Format foundation piles
    output.append("FOUNDATIONS:")
    foundation_line = ""
    for pile_idx in range(2, 6):
        if pile_idx < len(piles):
            pile = piles[pile_idx]
            if not isinstance(pile, dict):
                foundation_line += f"[{pile_idx}? Inv] "
                continue

            pile_name = pile.get('name', '?')
            foundation_line += f"{pile_name:3}: "
            cards = pile.get("cards")
            card_count = pile.get("count", 0)

            if cards is None and pile.get('address', 0) != 0:
                foundation_line += "[Error]     "
            elif card_count > 0 and isinstance(cards, list) and cards:
                top_card = cards[-1]
                card_desc = top_card.get('desc', 'Error')
                foundation_line += f"[{card_desc:13}] ({card_count:2})  "
            else:
                foundation_line += "[Empty]      "
    output.append(foundation_line)

    output.append("")

    # Format tableau piles
    output.append("TABLEAUS:")

    # Find the maximum length of any tableau
    max_tableau_length = 0
    for pile_idx in range(6, 13):
        if pile_idx < len(piles) and isinstance(piles[pile_idx], dict):
            max_tableau_length = max(
                max_tableau_length, piles[pile_idx].get("count", 0))

    # Create header with pile names
    header = "     "  # Indent for row numbers
    name_width = 18
    for pile_idx in range(6, 13):
        if pile_idx < len(piles) and isinstance(piles[pile_idx], dict):
            pile_name = piles[pile_idx].get('name', '?')
        else:
            pile_name = f'[{pile_idx}? Inv]'
        header += f"{pile_name:^{name_width}}"
    output.append(header)
    output.append("     " + "-" * (name_width * 7))  # Separator line

    if max_tableau_length == 0:
        output.append("     (All Tableaus Empty or Unread)")
        return "\n".join(output)

    # Create a row for each card position in the tableaus
    for row_idx in range(max_tableau_length):
        row_line = f"{row_idx+1:3d}: "  # Row number
        for pile_idx in range(6, 13):
            cell = ""
            if pile_idx < len(piles) and isinstance(piles[pile_idx], dict):
                pile = piles[pile_idx]
                cards = pile.get("cards")
                card_count = pile.get("count", 0)

                if cards is None and pile.get('address', 0) != 0:
                    cell = "[Error]"
                elif row_idx < card_count and isinstance(cards, list) and len(cards) > row_idx and cards[row_idx]:
                    card = cards[row_idx]
                    # * for face up, # for face down
                    face_indicator = "*" if card.get("face_up") else "#"
                    cell = f"{face_indicator}{card.get('desc', 'Error')}"
                elif row_idx < card_count:
                    cell = "[Miss]"  # Missing card data
            else:
                cell = "[NoPile]"  # Missing pile data

            row_line += f"{cell:^{name_width}}"
        output.append(row_line)

    output.append("     " + "-" * (name_width * 7))  # Bottom separator
    return "\n".join(output)
