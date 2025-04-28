"""Memory reading functionality for Microsoft Solitaire."""
import ctypes
import time
import traceback
import pymem
import pymem.process
from . import constants as const


def get_solitaire_process():
    """
    Find and attach to the Microsoft Solitaire process.

    Returns:
        Pymem object connected to sol.exe, or None if not found
    """
    try:
        pm = pymem.Pymem("sol.exe")
        return pm
    except pymem.exception.ProcessNotFound:
        return None
    except Exception:
        return None


def get_card_details(card_id_flags):
    """
    Decode card ID and face-up status from memory value.

    Args:
        card_id_flags: Combined card ID and face-up flag from memory

    Returns:
        Tuple of (card_description, is_face_up, card_id)
    """
    if card_id_flags is None:
        return "Read Error", False, -1

    # Extract card ID (lower 15 bits) and face-up status (highest bit)
    card_id = card_id_flags & 0x7FFF
    is_face_up = (card_id_flags & 0x8000) != 0

    if not (0 <= card_id <= 51):
        return f"Invalid ID ({card_id})", is_face_up, card_id

    # Extract suit (0-3) and rank (0-12) from card ID
    suit_index = card_id & 3
    rank_index = card_id >> 2

    if not (0 <= suit_index <= 3) or not (0 <= rank_index <= 12):
        return f"Invalid Index (S:{suit_index}, R:{rank_index})", is_face_up, card_id

    suit = const.SUITS[suit_index]
    rank = const.RANKS[rank_index]
    return f"{rank} of {suit}", is_face_up, card_id


def card_rank(card_id):
    """
    Extract rank (0-12) from card ID.

    Args:
        card_id: Card identifier (0-51)

    Returns:
        Rank index (0=Ace, 12=King)
    """
    return card_id >> 2


def card_suit(card_id):
    """
    Extract suit (0-3) from card ID.

    Args:
        card_id: Card identifier (0-51)

    Returns:
        Suit index (0=Clubs, 1=Diamonds, 2=Hearts, 3=Spades)
    """
    return card_id & 3


def read_game_state(pm):
    """
    Read the entire Solitaire game state from memory.

    Args:
        pm: Pymem object connected to Solitaire process

    Returns:
        Dictionary containing the complete game state
    """
    game_state = {"piles": [], "error": None, "hwnd": 0}

    try:
        # Verify process handle is valid
        if not pm.process_handle:
            game_state["error"] = "Process handle is invalid (process likely closed)."
            return game_state

        # Test read to ensure process is still active
        try:
            pm.read_int(pm.base_address)
        except Exception as e:
            game_state[
                "error"] = f"Process handle test read failed (process likely closed): {e}"
            if pm.process_handle:
                try:
                    pm.close_process()
                except:
                    pass
            pm.process_handle = None
            return game_state

        # Find the sol.exe module
        module = pymem.process.module_from_name(pm.process_handle, "sol.exe")
        if not module:
            game_state["error"] = "Could not find sol.exe module."
            return game_state
        base_addr = module.lpBaseOfDll

        # Read window handle
        hwnd_parent_addr = base_addr + const.HWND_PARENT_GLOBAL_OFFSET
        game_state["hwnd"] = pm.read_uint(hwnd_parent_addr)
        if game_state["hwnd"] == 0:
            game_state["error"] = "Could not read main window handle (hWndParent)."

        # Read base memory handle
        hmem_ptr_addr = base_addr + const.H_MEM_GLOBAL_OFFSET
        hmem_base = pm.read_uint(hmem_ptr_addr)
        if hmem_base == 0:
            game_state["error"] = "hMem base pointer is NULL."
            return game_state

        # Read number of piles
        col_count = pm.read_int(hmem_base + const.GAME_COL_COUNT_OFFSET)
        if not (0 < col_count <= 13):
            game_state["error"] = f"Invalid column count: {col_count}"
            col_count = 13  # Force to default value for safety

        # Read each pile of cards
        first_col_ptr_addr = hmem_base + const.GAME_FIRST_COL_PTR_OFFSET
        piles_data = []

        for pile_idx in range(col_count):
            pile_info = {
                "id": pile_idx,
                "name": "",
                "cards": [],
                "address": 0,
                "base_x": 0,
                "base_y": 0,
                "count": 0
            }

            try:
                # Read pile (column) address
                pile_address = pm.read_uint(
                    first_col_ptr_addr + (pile_idx * 4))
                pile_info["address"] = pile_address

                if pile_address == 0:
                    pile_info["cards"] = None
                    piles_data.append(pile_info)
                    continue

                # Read number of cards in pile
                card_count = pm.read_int(
                    pile_address + const.COL_CARD_COUNT_OFFSET)
                pile_info["count"] = card_count

                # Read pile base coordinates
                pile_info["base_x"] = pm.read_int(
                    pile_address + const.COL_BASE_X_OFFSET)
                pile_info["base_y"] = pm.read_int(
                    pile_address + const.COL_BASE_Y_OFFSET)

                # Get address of card array
                card_array_base = pile_address + const.COL_CARD_ARRAY_OFFSET

                # Read all cards in the pile
                cards_in_pile = []
                if 0 < card_count < 53:  # Valid card count range
                    for card_idx in range(card_count):
                        card_addr = card_array_base + \
                            (card_idx * const.CARD_STRUCT_SIZE)

                        # Read card data
                        card_flags_id = pm.read_ushort(
                            card_addr + const.CARD_FLAGS_ID_OFFSET)
                        card_pos_x = pm.read_int(
                            card_addr + const.CARD_POS_X_OFFSET)
                        card_pos_y = pm.read_int(
                            card_addr + const.CARD_POS_Y_OFFSET)

                        # Decode card details
                        card_desc, is_face_up, card_id = get_card_details(
                            card_flags_id)

                        # Store card information
                        cards_in_pile.append({
                            "id": card_id,
                            "desc": card_desc,
                            "face_up": is_face_up,
                            "flags": card_flags_id,
                            "index": card_idx,
                            "x": card_pos_x,
                            "y": card_pos_y
                        })

                    pile_info["cards"] = cards_in_pile
                elif card_count == 0:
                    pile_info["cards"] = []  # Empty pile
                else:
                    pile_info["cards"] = []  # Invalid count, treat as empty

            except pymem.exception.MemoryReadError:
                pile_info["cards"] = None
                pile_info["count"] = -1
            except Exception:
                traceback.print_exc()
                pile_info["cards"] = None
                pile_info["count"] = -1
            finally:
                piles_data.append(pile_info)

        game_state["piles"] = piles_data
        return game_state

    except pymem.exception.ProcessError as e:
        game_state["error"] = f"Process Error: {e}"
        return game_state
    except pymem.exception.MemoryReadError as e:
        game_state["error"] = f"Memory Read Error: {e}"
        return game_state
    except Exception as e:
        game_state["error"] = f"Unexpected Error reading state: {e}"
        traceback.print_exc()
        return game_state


def assign_pile_names(game_state):
    """
    Assign standard names to piles based on their IDs.

    Args:
        game_state: Game state dictionary with piles
    """
    pile_names = {
        0: "Deck",   # Stock
        1: "Talon",  # Waste
        2: "F1",     # Foundation 1 (Clubs)
        3: "F2",     # Foundation 2 (Diamonds)
        4: "F3",     # Foundation 3 (Hearts)
        5: "F4",     # Foundation 4 (Spades)
        6: "T1",     # Tableau 1
        7: "T2",     # Tableau 2
        8: "T3",     # Tableau 3
        9: "T4",     # Tableau 4
        10: "T5",    # Tableau 5
        11: "T6",    # Tableau 6
        12: "T7"     # Tableau 7
    }

    if game_state and isinstance(game_state.get("piles"), list):
        for pile in game_state["piles"]:
            if isinstance(pile, dict) and not pile.get("name"):
                pile_id = pile.get("id")
                pile["name"] = pile_names.get(
                    pile_id, f"Col {pile_id if pile_id is not None else '?'}")


def get_card_screen_pos(hwnd, pile, card_index, y_offset_fraction=0.1):
    """
    Calculate screen coordinates for a card in a pile.

    Args:
        hwnd: Window handle for Solitaire
        pile: Pile dictionary containing card information
        card_index: Index of the card within the pile
        y_offset_fraction: Vertical position within card (0.0-1.0)

    Returns:
        Tuple of (screen_x, screen_y) or None if coordinates can't be determined
    """
    if not hwnd:
        return None

    # Handle empty piles by using the base coordinates
    cards = pile.get('cards')
    if cards is None or not isinstance(cards, list) or len(cards) == 0:
        base_x = pile.get('base_x', 0)
        base_y = pile.get('base_y', 0)

        if base_x == 0 and base_y == 0:
            return None

        card_width = 71
        card_height = 96
        client_x = base_x + card_width // 2
        client_y = base_y + int(card_height * y_offset_fraction)

        # Convert client coordinates to screen coordinates
        screen_point = const.POINT(const.LONG(client_x), const.LONG(client_y))
        success = ctypes.windll.user32.ClientToScreen(
            hwnd, ctypes.byref(screen_point))

        if not success:
            return None

        return screen_point.x, screen_point.y

    # Ensure card index is valid
    if not (0 <= card_index < len(cards)):
        return None

    # Get card information
    card = cards[card_index]
    if not card:
        return None

    # Calculate click position on the card
    card_width = 71
    card_height = 96
    card_x = card.get('x')
    card_y = card.get('y')
    if card_x is None or card_y is None:
        return None

    client_x = card_x + card_width // 2
    client_y = card_y + int(card_height * y_offset_fraction)

    # Convert client coordinates to screen coordinates
    screen_point = const.POINT(const.LONG(client_x), const.LONG(client_y))
    success = ctypes.windll.user32.ClientToScreen(
        hwnd, ctypes.byref(screen_point))
    if not success:
        return None

    return screen_point.x, screen_point.y


def make_lparam(x, y):
    """
    Create LPARAM value from x,y coordinates for Windows messages.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        LPARAM value with packed coordinates
    """
    return const.LPARAM((y << 16) | (x & 0xFFFF))


def simulate_drag(hwnd, start_pos, end_pos):
    """
    Simulate a mouse drag operation using Windows messages.

    Args:
        hwnd: Window handle
        start_pos: Starting position (screen coordinates)
        end_pos: Ending position (screen coordinates)

    Returns:
        True if all messages were sent successfully, False otherwise
    """
    if not hwnd or not start_pos or not end_pos:
        return False

    start_x, start_y = start_pos
    end_x, end_y = end_pos

    # Create point structures
    start_point_screen = const.POINT(const.LONG(start_x), const.LONG(start_y))
    end_point_screen = const.POINT(const.LONG(end_x), const.LONG(end_y))

    # Convert screen coordinates to client coordinates
    start_point_client = start_point_screen
    end_point_client = end_point_screen

    if not ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(start_point_client)):
        return False
    if not ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(end_point_client)):
        return False

    # Create packed LPARAM values for client coordinates
    lparam_start_client = make_lparam(
        start_point_client.x, start_point_client.y)
    lparam_end_client = make_lparam(end_point_client.x, end_point_client.y)

    # Send mouse down at start position
    result_down = ctypes.windll.user32.PostMessageW(
        hwnd, const.WM_LBUTTONDOWN, const.MK_LBUTTON, lparam_start_client)
    if not result_down:
        return False

    # Small delay to simulate real mouse movement
    time.sleep(0.05)

    # Send mouse move to end position
    result_move = ctypes.windll.user32.PostMessageW(
        hwnd, const.WM_MOUSEMOVE, const.MK_LBUTTON, lparam_end_client)
    if not result_move:
        return False

    # Small delay before releasing button
    time.sleep(0.05)

    # Send mouse up at end position
    result_up = ctypes.windll.user32.PostMessageW(
        hwnd, const.WM_LBUTTONUP, 0, lparam_end_client)
    if not result_up:
        return False

    return True


def simulate_click(hwnd, pos):
    """
    Simulate a mouse click at specific screen coordinates.

    Args:
        hwnd: Window handle
        pos: Screen coordinates (x, y)

    Returns:
        True if click was simulated successfully, False otherwise
    """
    if not hwnd or not pos:
        return False

    x_screen, y_screen = pos

    # Create point structure and convert to client coordinates
    point_screen = const.POINT(const.LONG(x_screen), const.LONG(y_screen))
    point_client = point_screen
    if not ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(point_client)):
        return False

    # Create packed LPARAM for client coordinates
    lparam_client = make_lparam(point_client.x, point_client.y)

    # Send mouse down message
    result_down = ctypes.windll.user32.PostMessageW(
        hwnd, const.WM_LBUTTONDOWN, const.MK_LBUTTON, lparam_client)
    if not result_down:
        return False

    # Small delay between down and up
    time.sleep(0.03)

    # Send mouse up message
    result_up = ctypes.windll.user32.PostMessageW(
        hwnd, const.WM_LBUTTONUP, 0, lparam_client)
    if not result_up:
        return False

    return True


def get_pile_by_name(game_state, name_prefix):
    """
    Find a pile in the game state by name prefix.

    Args:
        game_state: Game state dictionary
        name_prefix: Start of pile name (case-insensitive)

    Returns:
        Pile dictionary or None if not found
    """
    if not game_state or not isinstance(game_state.get('piles'), list):
        return None

    name_prefix = name_prefix.lower()
    for pile in game_state['piles']:
        if isinstance(pile, dict) and pile.get('name', '').lower().startswith(name_prefix):
            return pile

    return None


def execute_move(pm, hwnd, action):
    """
    Execute a move through the reader interface using mouse automation.

    Args:
        pm: Pymem process object
        hwnd: Window handle
        action: Move action list (e.g., ["TALON", "F1"])

    Returns:
        True if move was executed successfully, False otherwise
    """
    # Read current game state and assign standard names to piles
    game_state = read_game_state(pm)
    assign_pile_names(game_state)

    src_name = ""
    src_card_idx_from_top = -1
    dest_name = ""

    # Parse the move action to determine source and destination
    if action[0] == 'DECK':
        src_name = 'Deck'
        dest_name = 'Deck'  # Click on deck
        src_card_idx_from_top = 0
    elif action[0] == 'TALON':
        src_name = 'Talon'  # Waste pile
        src_card_idx_from_top = 0

        # Determine destination from action
        if len(action) >= 2:
            if action[1].startswith('F') or action[1].startswith('T'):
                dest_name = action[1]
            elif len(action) >= 3 and action[2].startswith(('F', 'T')):
                dest_name = action[2]

        if not dest_name:
            return False
    elif action[0].startswith('T'):
        src_name = action[0]  # Source tableau

        if len(action) == 2:
            # Tableau to foundation move
            src_card_idx_from_top = 0
            dest_name = action[1]
        elif len(action) == 3:
            # Tableau to tableau move with sequence
            src_card_idx_from_top = int(action[1])
            dest_name = action[2]

    # Find source and destination piles
    src_pile = get_pile_by_name(game_state, src_name)
    dest_pile = get_pile_by_name(game_state, dest_name)

    if not src_pile or not dest_pile:
        return False

    # Handle special case for clicking on the deck
    if src_name == 'Deck' and dest_name == 'Deck':
        deck_pos = get_card_screen_pos(hwnd, src_pile, 0, 0.1)
        if deck_pos:
            return simulate_click(hwnd, deck_pos)
        else:
            return False

    # Calculate actual source card index
    actual_src_index = -1
    src_cards = src_pile.get('cards')
    actual_src_list_len = len(src_cards) if isinstance(src_cards, list) else -1

    if src_name == 'Deck':
        actual_src_index = 0
    elif src_name == 'Talon':
        if actual_src_list_len > 0:
            actual_src_index = actual_src_list_len - 1  # Top card
    elif src_name.startswith('T'):
        if actual_src_list_len > 0:
            top_card_index = actual_src_list_len - 1
            # Find the first face-up card in tableau
            first_face_up_idx = next(
                (k for k, card in enumerate(src_cards) if card.get('face_up')), -1)

            if first_face_up_idx != -1:
                # Calculate index based on how many cards from top we want to move
                target_index = top_card_index - src_card_idx_from_top
                if target_index >= first_face_up_idx:
                    actual_src_index = target_index

    if actual_src_index == -1:
        return False

    # Get screen coordinates for source and destination
    start_coords = get_card_screen_pos(hwnd, src_pile, actual_src_index, 0.1)
    end_coords = None

    # Get destination coordinates
    dest_cards = dest_pile.get('cards')
    actual_dest_list_len = len(dest_cards) if isinstance(
        dest_cards, list) else -1

    if actual_dest_list_len > 0:
        # Target the top card of destination pile
        end_coords = get_card_screen_pos(
            hwnd, dest_pile, actual_dest_list_len - 1, 0.4)
    elif actual_dest_list_len == 0:
        # Target empty pile
        end_coords = get_card_screen_pos(hwnd, dest_pile, 0, 0.4)

    if not start_coords or not end_coords:
        return False

    # Execute the drag operation
    move_successful = simulate_drag(hwnd, start_coords, end_coords)

    # Check for face-up card flips after move (if moving from tableau)
    if move_successful and src_name.startswith('T'):
        time.sleep(0.5)  # Wait for the move animation to complete

        # Check for a face-down card that may need to be flipped automatically
        current_state_after = read_game_state(pm)
        if current_state_after and not current_state_after.get("error"):
            assign_pile_names(current_state_after)
            src_pile_after = get_pile_by_name(current_state_after, src_name)

            # Check if we need to flip a card manually
            if src_pile_after and isinstance(src_pile_after.get('cards'), list):
                src_cards_after = src_pile_after.get('cards')
                if src_cards_after and len(src_cards_after) > 0:
                    top_card = src_cards_after[-1]

                    # If the top card is still face down, simulate a click to flip it
                    if not top_card.get('face_up', True):
                        flip_pos = get_card_screen_pos(
                            hwnd, src_pile_after, len(src_cards_after) - 1, 0.5)
                        if flip_pos:
                            simulate_click(hwnd, flip_pos)
                            time.sleep(0.3)  # Wait for flip animation

    return move_successful
