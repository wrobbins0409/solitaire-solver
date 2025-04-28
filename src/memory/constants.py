"""Windows API and memory constants for Microsoft Solitaire."""
import ctypes
import ctypes.wintypes

# Windows API Types
HWND = ctypes.wintypes.HWND    # Window handle
LPARAM = ctypes.wintypes.LPARAM  # Message parameter
WPARAM = ctypes.wintypes.WPARAM  # Message parameter
UINT = ctypes.wintypes.UINT    # Unsigned integer
DWORD = ctypes.wintypes.DWORD  # 32-bit unsigned integer
WORD = ctypes.wintypes.WORD    # 16-bit unsigned integer
LONG = ctypes.wintypes.LONG    # 32-bit signed integer
POINT = ctypes.wintypes.POINT  # Point structure (x, y coordinates)

# Windows Messages for mouse interaction
WM_LBUTTONDOWN = 0x0201  # Mouse left button down
WM_LBUTTONUP = 0x0202    # Mouse left button up
WM_MOUSEMOVE = 0x0200    # Mouse movement
MK_LBUTTON = 0x0001      # Mouse key state for WPARAM in WM_MOUSEMOVE

# Memory Offsets for reading game state
H_MEM_GLOBAL_OFFSET = 0xD01C           # Base memory handle offset
GAME_COL_COUNT_OFFSET = 0x64           # Number of columns/piles
GAME_FIRST_COL_PTR_OFFSET = 0x6C       # Pointer to first column
COL_BASE_X_OFFSET = 0x08               # Column's base X coordinate
COL_BASE_Y_OFFSET = 0x0C               # Column's base Y coordinate
COL_CARD_COUNT_OFFSET = 0x1C           # Number of cards in column
COL_CARD_ARRAY_OFFSET = 0x24           # Pointer to card array
CARD_FLAGS_ID_OFFSET = 0x0             # Card flags and ID
CARD_POS_X_OFFSET = 0x4                # Card X position
CARD_POS_Y_OFFSET = 0x8                # Card Y position
CARD_STRUCT_SIZE = 12                  # Size of card structure in memory
HWND_PARENT_GLOBAL_OFFSET = 0xF194     # Parent window handle offset

# Card Constants
SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]  # Card suits (0-3)
RANKS = [                                          # Card ranks (0-12)
    "Ace", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "Jack", "Queen", "King"
]
