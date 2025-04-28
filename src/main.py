"""Solitaire solver application entry point."""
from src.gui.app import SolitaireGUI
import sys
import os

# Add the project root directory to the Python path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """
    Launch the Solitaire solver application.

    Creates and initializes the GUI application.
    """
    app = SolitaireGUI()
    app.init_gui()


if __name__ == "__main__":
    main()
