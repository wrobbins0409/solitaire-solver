#!/usr/bin/env python3
"""
Simple launcher for Solitaire Solver.
Run this script to start the application.
"""
from src.main import main
import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function

if __name__ == "__main__":
    main()
