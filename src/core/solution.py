"""Solution representation and utilities."""


class SolutionState:
    """Represents a solution found by the solver."""

    def __init__(self, foundation_count=0, moves=None):
        """
        Initialize a solution state.

        Args:
            foundation_count: Number of cards placed in foundations
            moves: List of moves to reach this state
        """
        self.foundation_count = foundation_count
        self.moves = moves or []


def prioritize_moves(moves):
    """
    Sort moves by priority (best moves first).

    Args:
        moves: List of available moves

    Returns:
        Sorted list with highest priority moves first
    """
    # Priority values for different move types
    PRIORITIES = {
        "F": 1000000,  # Foundation moves (highest priority)
        "T": 500000,   # Tableau moves
        "DECK": 1000   # Deck/stock moves (lowest priority)
    }

    def get_move_priority(move):
        """Calculate priority for a single move."""
        # Default low priority
        priority = 0

        if not move or len(move) < 1:
            return priority

        action = move[0]

        # TALON moves
        if action == "TALON" and len(move) >= 2:
            destination = move[1]
            if destination.startswith("F"):
                # Highest priority - waste to foundation
                return PRIORITIES["F"]
            elif destination.startswith("T"):
                # Lower than tableau to foundation
                return PRIORITIES["T"] - 100000

        # TABLEAU moves
        elif action.startswith("T"):
            if len(move) == 2 and move[1].startswith("F"):
                # Tableau to foundation (very high)
                return PRIORITIES["F"] - 50000
            elif len(move) == 3 and move[2].startswith("T"):
                return PRIORITIES["T"]  # Tableau to tableau

        # DECK moves
        elif action == "DECK":
            return PRIORITIES["DECK"]

        return priority

    # Sort moves by priority (highest first)
    moves_with_priority = [(get_move_priority(move), move) for move in moves]
    moves_with_priority.sort(reverse=True)
    return [move for _, move in moves_with_priority]


def describe_move(move):
    """
    Convert move to human-readable description.

    Args:
        move: Move in internal format

    Returns:
        String description of the move
    """
    if not move or len(move) < 1:
        return "Invalid move"

    action = move[0]

    # TALON moves
    if action == "TALON" and len(move) >= 2:
        destination = move[1]
        if destination.startswith("F"):
            return f"Move card from Waste to Foundation {destination[1:]}"
        elif destination.startswith("T"):
            return f"Move card from Waste to Tableau {destination[1:]}"

    # TABLEAU moves
    elif action.startswith("T") and len(move) >= 2:
        source = action
        if len(move) == 2 and move[1].startswith("F"):
            return f"Move top card from Tableau {source[1:]} to Foundation {move[1][1:]}"
        elif len(move) == 3 and move[2].startswith("T"):
            cards_count = int(move[1]) + 1  # Cards from top
            return f"Move {cards_count} cards from Tableau {source[1:]} to Tableau {move[2][1:]}"

    # DECK moves
    elif action == "DECK":
        return "Draw card from Stock or recycle Waste"

    return f"Unknown move: {' '.join(str(x) for x in move)}"
