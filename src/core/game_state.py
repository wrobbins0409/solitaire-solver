"""Game state representation for Solitaire."""
from ..memory.reader import card_rank, card_suit


class GameState:
    """Represents the current state of a Solitaire game."""

    def __init__(self, stock, waste, foundations, tableaus, stock_cycles=0):
        """
        Initialize a game state.

        Args:
            stock: Cards remaining in the stock pile
            waste: Cards in the waste pile
            foundations: Current top card rank for each foundation pile
            tableaus: Cards in tableau piles with face-up status
            stock_cycles: Number of times stock has been recycled
        """
        self.stock = stock
        self.waste = waste
        self.foundations = foundations
        self.tableaus = tableaus
        self.stock_cycles = stock_cycles
        self.foundation_count = sum(
            rank + 1 for rank in foundations if rank >= 0)

    def is_won(self):
        """Check if the game is won (all cards in foundations)."""
        return all(rank == 12 for rank in self.foundations)

    def clone(self):
        """Create a deep copy of the current state."""
        return GameState(
            stock=self.stock.copy(),
            waste=self.waste.copy(),
            foundations=self.foundations.copy(),
            tableaus=[pile.copy() for pile in self.tableaus],
            stock_cycles=self.stock_cycles
        )

    def available_moves(self):
        """Return all legal moves from current state in reader-compatible format."""
        moves = []

        # Waste to foundation or tableau
        if self.waste:
            top_card = self.waste[-1]
            if self.can_move_to_foundation(top_card):
                suit = card_suit(top_card)
                moves.append(["TALON", f"F{suit+1}"])
            for i, tableau in enumerate(self.tableaus):
                if self.can_move_to_tableau(top_card, tableau):
                    moves.append(["TALON", f"T{i+1}"])

        # Tableau to foundation
        for i, tableau in enumerate(self.tableaus):
            if tableau and tableau[-1][1]:  # Face up card
                top_card = tableau[-1][0]
                if self.can_move_to_foundation(top_card):
                    suit = card_suit(top_card)
                    moves.append([f"T{i+1}", f"F{suit+1}"])

        # Tableau to tableau (sequences)
        for src_idx, src_tableau in enumerate(self.tableaus):
            # Find first face-up card
            face_up_start = next((idx for idx, (card, face_up) in enumerate(
                src_tableau) if face_up), len(src_tableau))

            # Try moving sequences of different lengths
            for seq_start in range(face_up_start, len(src_tableau)):
                moving_sequence = src_tableau[seq_start:]
                for dest_idx, dest_tableau in enumerate(self.tableaus):
                    if src_idx != dest_idx and self.can_move_sequence(moving_sequence, dest_tableau):
                        cards_to_move = len(src_tableau) - seq_start
                        moves.append(
                            [f"T{src_idx+1}", str(cards_to_move-1), f"T{dest_idx+1}"])

        # Stock to waste or recycle
        if self.stock:
            moves.append(["DECK"])
        elif self.waste:
            moves.append(["DECK"])

        return moves

    def can_move_to_foundation(self, card_id):
        """
        Check if card can be moved to foundation pile.

        A card can move to foundation if it's one rank higher than current top card
        of the same suit.
        """
        suit = card_suit(card_id)
        rank = card_rank(card_id)
        return rank == (self.foundations[suit] + 1)

    def can_move_to_tableau(self, card_id, tableau):
        """
        Check if card can be moved to tableau pile.

        A card can move to tableau if:
        - It's a King moving to empty tableau
        - It's one rank lower and opposite color from tableau's top card
        """
        rank = card_rank(card_id)
        suit = card_suit(card_id)

        if not tableau:
            return rank == 12  # King can go to empty tableau

        top_card, is_face_up = tableau[-1]
        if not is_face_up:
            return False

        top_rank = card_rank(top_card)
        top_suit = card_suit(top_card)

        # Check if cards are opposite colors (clubs/spades are black)
        is_black = suit in [0, 3]
        top_is_black = top_suit in [0, 3]

        return (is_black != top_is_black) and (rank == top_rank - 1)

    def can_move_sequence(self, moving_sequence, tableau):
        """Check if sequence can be legally moved to tableau."""
        if not moving_sequence:
            return False
        moving_card = moving_sequence[0][0]
        return self.can_move_to_tableau(moving_card, tableau)

    def apply_move(self, move):
        """
        Apply a move and return the resulting new state.

        Does not modify the current state.
        """
        new_state = self.clone()

        # Extract action type from move
        action = move[0]

        # Handle the move based on the action type
        if action == "TALON" and len(move) == 2:
            # Waste to foundation or tableau
            destination = move[1]

            if destination.startswith("F"):  # To foundation
                if not new_state.waste:
                    return new_state  # No cards in waste
                card = new_state.waste.pop()
                suit = card_suit(card)
                new_state.foundations[suit] += 1

            elif destination.startswith("T"):  # To tableau
                if not new_state.waste:
                    return new_state  # No cards in waste
                card = new_state.waste.pop()
                tableau_idx = int(destination[1:]) - 1
                new_state.tableaus[tableau_idx].append((card, True))

        elif action.startswith("T") and len(move) == 2:
            # Tableau to foundation
            if not action.startswith("T") or not move[1].startswith("F"):
                return new_state  # Invalid move

            tableau_idx = int(action[1:]) - 1
            if not new_state.tableaus[tableau_idx]:
                return new_state  # Empty tableau

            card, _ = new_state.tableaus[tableau_idx].pop()
            suit = card_suit(card)
            new_state.foundations[suit] += 1

            # Flip next card if needed
            if new_state.tableaus[tableau_idx]:
                top_card, is_face_up = new_state.tableaus[tableau_idx][-1]
                if not is_face_up:
                    new_state.tableaus[tableau_idx][-1] = (top_card, True)

        elif action.startswith("T") and len(move) == 3:
            # Tableau to tableau with sequence
            from_idx = int(action[1:]) - 1
            cards_from_top = int(move[1])
            to_idx = int(move[2][1:]) - 1

            if not (0 <= from_idx < 7) or not (0 <= to_idx < 7) or from_idx == to_idx:
                return new_state  # Invalid indices

            src_tableau = new_state.tableaus[from_idx]
            if not src_tableau:
                return new_state  # Empty source tableau

            # Calculate the start index
            start_idx = max(0, len(src_tableau) - cards_from_top - 1)

            # Move the sequence
            sequence = src_tableau[start_idx:]
            del src_tableau[start_idx:]
            new_state.tableaus[to_idx].extend(sequence)

            # Flip next card if needed
            if new_state.tableaus[from_idx]:
                top_card, is_face_up = new_state.tableaus[from_idx][-1]
                if not is_face_up:
                    new_state.tableaus[from_idx][-1] = (top_card, True)

        elif action == "DECK":
            # Stock to waste or recycle
            if new_state.stock:
                card = new_state.stock.pop()
                new_state.waste.append(card)
            elif new_state.waste:
                # Reverse waste to stock
                new_state.stock = new_state.waste[::-1]
                new_state.waste.clear()
                new_state.stock_cycles += 1

        # Update foundation count
        new_state.foundation_count = sum(
            rank + 1 for rank in new_state.foundations if rank >= 0)
        return new_state

    def heuristic_score(self):
        """
        Calculate heuristic score for state evaluation.

        Higher scores are better. Factors considered:
        - Cards in foundation (highly valued)
        - Face-up cards in tableau (good)
        - Face-down cards (bad)
        - Stock cycles (very bad)
        - Cards in waste and stock (moderately bad)
        """
        score = 0
        # Foundation cards are highly valued
        score += sum((rank + 1) *
                     10000 for rank in self.foundations if rank >= 0)
        # Face up cards in tableau are good
        score += sum(200 for tableau in self.tableaus for _,
                     is_face_up in tableau if is_face_up)
        # Face down cards are bad
        score -= sum(1000 for tableau in self.tableaus for _,
                     is_face_up in tableau if not is_face_up)
        # Stock cycles are very bad
        score -= self.stock_cycles * 30000
        # Cards in waste and stock are moderately bad
        score -= len(self.waste) * 800
        score -= len(self.stock) * 200
        return score
