# Solitaire Solver

A Python-based tool to automatically solve and play the Classic Microsoft Solitaire for Windows XP. Currently only able to solve on draw one mode.

## Demo

[Here](https://youtu.be/4NSqbirvrgg) is a short youtube demo.

## Features

- Reads Solitaire game state directly from memory
- Uses A* search algorithm to find optimal solutions
- Automatically executes moves through Windows message simulation
- User-friendly GUI with real-time game state visualization

## Requirements

- Windows operating system
- Microsoft Solitaire Collection game
- Python 3.6+
- Git (for cloning the repository)

## Installation

1. Clone the repository:

   ```
   git clone git@github.com:wrobbins0409/solitaire-solver.git
   cd solitaire-solver
   ```
2. Set up a virtual environment:

   ```
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```
4. Run the application using the simple launcher:

   ```
   python run.py
   ```

## Running provided .exe on windows

To run the provided [.exe](dist/SolitaireSolver.exe) simply double click it in windows file explorer

**Hash Verification**

To verify the integrity of the downloaded executable, check its SHA-256 hash:

```
SHA-256: 76c98fc7e3dc012db14123594add3e18a3c91dc6daee788447e3faf4c335ca6b
```

You can verify the hash of your downloaded executable using PowerShell:

```
Get-FileHash -Algorithm SHA256 .\dist\SolitaireSolver.exe
```

## Building the Executable

To create a standalone executable of the Solitaire Solver:

1. Clone the repository and set up a virtual environment as described in the Installation section:

   ```
   git clone git@github.com:wrobbins0409/solitaire-solver.git
   cd solitaire-solver
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```
3. Run the build script:

   ```
   python build.py
   ```

   This will automatically install PyInstaller if it's not already installed.
4. The executable will be created in the `dist` directory as `SolitaireSolver.exe`

## Usage

1. Start [Microsoft Solitaire](dist/sol.exe) and begin a game

   ```
   SHA-256: 8886ac5c321011e9d1940af88790403c4d2f78a42458c56db033e694d0100d39
   ```
2. Launch the Solitaire Solver application
3. Click "Connect" to connect to the running Solitaire game
4. Click "Solve Game" to find a solution
5. Use "Step" or "Auto Execute" to play the solution automatically

## Configuration Options

- **Max Iterations**: Controls how many game states the solver will evaluate
- **Solution Strategy**: Adjust between finding the best solution (higher quality) and finding a quick solution (faster)
- **Delay**: Control the speed of automatic move execution

## Project Structure

This is a standalone application with the following folder structure:

- **[src/](src/)** - Main source code
  - **[src/main.py](src/main.py)** - Entry point for the application
  - **[src/core/](src/core/)** - Core solving algorithms and game state representation
    - **[src/core/game_state.py](src/core/game_state.py)** - Game state representation and manipulation
    - **[src/core/solver.py](src/core/solver.py)** - A* search algorithm implementation
    - **[src/core/solution.py](src/core/solution.py)** - Solution representation and management
  - **[src/memory/](src/memory/)** - Memory reading and interaction with Solitaire
    - **[src/memory/reader.py](src/memory/reader.py)** - Memory reading functionality
    - **[src/memory/display.py](src/memory/display.py)** - Visualization of memory data
    - **[src/memory/constants.py](src/memory/constants.py)** - Constants for memory offsets
  - **[src/gui/](src/gui/)** - User interface components
    - **[src/gui/app.py](src/gui/app.py)** - Main GUI application
- **[dist/](dist/)** - Executable files
  - **[dist/SolitaireSolver.exe](dist/SolitaireSolver.exe)** - Compiled executable
- **[assets/](assets/)** - Application resources and images
  - **[assets/solitaire.ico](assets/solitaire.ico)** - Application icon file
- **[build.py](build.py)** - Script to build the executable
- **[run.py](run.py)** - Simple launcher script
- **[requirements.txt](requirements.txt)** - Python dependencies

## Future Developments

Update to also be able to solve with draw 3 mode.

## License

This project is for educational purposes only.
