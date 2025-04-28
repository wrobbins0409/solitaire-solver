"""A* solver for Solitaire."""
import heapq
import time
import keyboard
from ..memory.reader import card_rank
from .game_state import GameState
from .solution import SolutionState, prioritize_moves, describe_move


def solve(initial_state, max_iterations=100000, heuristic_weight=1.0, progress_callback=None):
    """
    Solve a Solitaire game using A* search algorithm.

    Args:
        initial_state: Initial game state
        max_iterations: Maximum number of states to explore
        heuristic_weight: Weight for heuristic function
        progress_callback: Optional function to report progress

    Returns:
        SolutionState object with best solution found
    """
    heap = []
    counter = 0  # Tie-breaker for same priority states
    visited = set()
    initial_cost = 0

    # Priority queue entry: (priority, counter, cost, state, path)
    heapq.heappush(heap, (initial_cost - heuristic_weight * initial_state.heuristic_score(),
                          counter, initial_cost, initial_state, []))

    best_solution = SolutionState()
    best_winning_solution = None  # Track best complete solution
    iterations = 0
    status_info = {"message": "Starting search...", "stopped_by_user": False}

    while heap and iterations < max_iterations:
        # Check for keyboard interrupt
        if keyboard.is_pressed('q'):
            status_info["message"] = "Search stopped by user."
            status_info["stopped_by_user"] = True
            if progress_callback:
                progress_callback(iterations, max_iterations,
                                  best_solution, best_winning_solution, status_info)
            break

        # Report progress periodically
        if progress_callback and iterations % 100 == 0:
            progress_callback(iterations, max_iterations,
                              best_solution, best_winning_solution, status_info)

        # Get next state with lowest priority
        _, _, cost_so_far, state, path = heapq.heappop(heap)

        # Create a hashable representation of the state for visited set
        state_key = (
            tuple(state.stock),
            tuple(state.waste),
            tuple(state.foundations),
            tuple(tuple((card, face_up) for card, face_up in tableau)
                  for tableau in state.tableaus),
            state.stock_cycles
        )

        if state_key in visited:
            continue
        visited.add(state_key)

        # Update best partial solution if better
        if state.foundation_count > best_solution.foundation_count:
            best_solution.foundation_count = state.foundation_count
            best_solution.moves = path.copy()
            status_info["message"] = f"Found partial solution with {best_solution.foundation_count}/52 cards in foundations"

        # Check if we found a winning solution
        if state.is_won():
            # If this is our first winning solution or has fewer moves than previous best
            if best_winning_solution is None or len(path) < len(best_winning_solution.moves):
                best_winning_solution = SolutionState(52, path.copy())
                status_info["message"] = f"Found solution with {len(path)} moves! Continuing search..."

                # Report the winning solution
                if progress_callback:
                    progress_callback(iterations, max_iterations,
                                      best_solution, best_winning_solution, status_info)

            # We don't immediately return - keep searching for shorter solutions

        # Explore all possible moves from current state
        moves = prioritize_moves(state.available_moves())
        for move in moves:
            next_state = state.apply_move(move)

            # Create hashable key for next state
            next_state_key = (
                tuple(next_state.stock),
                tuple(next_state.waste),
                tuple(next_state.foundations),
                tuple(tuple((card, face_up) for card, face_up in tableau)
                      for tableau in next_state.tableaus),
                next_state.stock_cycles
            )

            if next_state_key in visited:
                continue

            counter += 1
            next_cost = cost_so_far + 1
            # Priority = actual cost - heuristic (negative because better states have higher scores)
            priority = next_cost - heuristic_weight * next_state.heuristic_score()
            heapq.heappush(heap, (priority, counter, next_cost,
                                  next_state, path + [move]))

        iterations += 1

    # Final progress update
    status_info["message"] = f"Search completed after {iterations} iterations."
    if progress_callback:
        progress_callback(iterations, max_iterations,
                          best_solution, best_winning_solution, status_info)

    # Return the best winning solution if found, otherwise return the best partial solution
    if best_winning_solution:
        status_info["message"] = f"Best solution found requires {len(best_winning_solution.moves)} moves."
        if progress_callback:
            progress_callback(iterations, max_iterations,
                              best_solution, best_winning_solution, status_info)
        return best_winning_solution

    return best_solution


def from_reader_state(reader_state):
    """
    Convert memory reader state to solver state.

    Args:
        reader_state: Game state from memory reader

    Returns:
        GameState object or None if invalid
    """
    if not reader_state:
        return None

    stock = []
    waste = []
    foundations = [-1, -1, -1, -1]  # -1 indicates empty foundation
    tableaus = [[] for _ in range(7)]

    piles = reader_state.get('piles', [])

    for pile in piles:
        pile_id = pile.get('id')
        cards = pile.get('cards', [])

        if pile_id is None or cards is None:
            continue

        # Deck (Stock)
        if pile_id == 0:
            for card in cards:
                card_id = card.get('id')
                if 0 <= card_id <= 51:
                    stock.append(card_id)

        # Talon (Waste)
        elif pile_id == 1:
            for card in cards:
                card_id = card.get('id')
                if 0 <= card_id <= 51:
                    waste.append(card_id)

        # Foundations
        elif 2 <= pile_id <= 5:
            foundation_idx = pile_id - 2
            if cards:
                top_card = cards[-1]
                card_id = top_card.get('id')
                if 0 <= card_id <= 51:
                    foundations[foundation_idx] = card_rank(card_id)

        # Tableaus
        elif 6 <= pile_id <= 12:
            tableau_idx = pile_id - 6
            for card in cards:
                card_id = card.get('id')
                face_up = card.get('face_up', False)
                if 0 <= card_id <= 51:
                    tableaus[tableau_idx].append((card_id, face_up))

    return GameState(stock, waste, foundations, tableaus)


def execute_solution(solitaire_reader, pm, hwnd, solution, step_by_step=False, delay=0.5, status_callback=None):
    """
    Execute solution on the actual game.

    Args:
        solitaire_reader: Memory reader object
        pm: Process memory object
        hwnd: Window handle
        solution: Solution to execute
        step_by_step: Whether to pause between moves
        delay: Time delay between moves
        status_callback: Function to report status

    Returns:
        True if solution was executed successfully, False otherwise
    """
    if not solution or not solution.moves:
        if status_callback:
            status_callback("No solution to execute.")
        return False

    if status_callback:
        status_callback(
            f"Executing solution with {len(solution.moves)} moves...")

    # Get current game state
    game_state = from_reader_state(solitaire_reader.read_game_state(pm))
    if not game_state:
        if status_callback:
            status_callback("Error: Could not read current game state.")
        return False

    # Execute each move
    for move_idx, move in enumerate(solution.moves):
        if status_callback:
            status_callback(
                f"Move {move_idx+1}/{len(solution.moves)}: {describe_move(move)}")

        if step_by_step:
            # Longer delay in step-by-step mode
            time.sleep(1.0)

        # Execute the move
        if not move:
            if status_callback:
                status_callback(f"Warning: Invalid move {move}. Skipping.")
            continue

        if status_callback:
            status_callback(
                f"Executing: {' '.join(str(item) for item in move)}")

        success = solitaire_reader.execute_move(pm, hwnd, move)

        if success:
            # Update internal game state to match
            game_state = game_state.apply_move(move)
            time.sleep(delay)
        else:
            # Handle failure by re-reading game state
            if status_callback:
                status_callback(f"Move failed. State may be out of sync.")
            game_state = from_reader_state(
                solitaire_reader.read_game_state(pm))
            if not game_state:
                if status_callback:
                    status_callback(
                        "Error: Could not refresh game state. Aborting.")
                return False
            time.sleep(1)

    if status_callback:
        status_callback("Solution execution completed.")
    return True
