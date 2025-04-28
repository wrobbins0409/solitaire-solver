"""Solitaire solver GUI application."""
import dearpygui.dearpygui as dpg
import threading
import time
import os
from src.memory import reader as memory_reader
from src.memory import display
from src.core import solution as solution_module
from src.core import solver


class SolitaireGUI:
    """GUI for the Solitaire solver application."""

    def __init__(self):
        """Initialize the GUI components."""
        self.pm = None
        self.hwnd = 0
        self.game_state = None
        self.refresh_interval = 2
        self.auto_refresh = True
        self.continue_refresh = True
        self.solution = None
        self.current_step = 0
        self.auto_executing = False
        self.execution_paused = False
        self.execute_thread = None
        self.should_stop_execution = False
        self.solving = False
        self.solver_thread = None
        self.best_solution = None
        self.best_winning_solution = None
        self.max_iterations = 50000
        self.heuristic_weight = 1.0
        self.delay = 0.5
        self.solver_progress = 0
        self.current_iteration = 0
        self.iteration_lock = threading.Lock()
        self.last_status_message = None
        self.visualization_text_tag = "visualization_text"
        self.stop_button_tag = "stop_button_tag"

        # GUI tags
        self.status_tag = "status_text"
        self.solution_text_tag = "solution_text"
        self.progress_bar_tag = "progress_bar"
        self.solver_progress_bar_tag = "solver_progress_bar"

    def init_gui(self):
        """Initialize and run the GUI."""
        dpg.create_context()
        self._setup_viewport()
        self._create_windows()

        # Start refresh thread
        self.refresh_thread = threading.Thread(
            target=self.auto_refresh_thread, daemon=True)
        self.refresh_thread.start()

        # Start GUI
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _setup_viewport(self):
        """Set up the application viewport."""
        dpg.create_viewport(title="Solitaire Solver", width=900, height=700)
        dpg.set_viewport_resizable(True)

        try:
            dpg.set_viewport_min_width(700)
            dpg.set_viewport_min_height(600)
            dpg.set_viewport_clear_color([30, 30, 40, 255])
            self.set_application_icon()
        except Exception as e:
            pass

    def _create_windows(self):
        """Create the main application windows and UI elements."""
        theme = self._create_theme()
        dpg.bind_theme(theme)

        with dpg.window(tag="main_window", label="Solitaire Solver"):
            window_theme = self._create_window_theme()
            dpg.bind_item_theme("main_window", window_theme)

            with dpg.tab_bar(tag="main_tab_bar"):
                self._create_game_state_tab()
                self._create_solution_tab()

        # Set main window to fill the viewport
        dpg.set_primary_window("main_window", True)

    def _create_theme(self):
        """Create the application theme."""
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                # Window styling
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [30, 30, 40])

                # Title bar styling
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [40, 40, 60])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [60, 60, 90])
                dpg.add_theme_color(
                    dpg.mvThemeCol_TitleBgCollapsed, [30, 30, 50])

                # Text
                dpg.add_theme_color(dpg.mvThemeCol_Text, [220, 220, 240])

                # Menu bar
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, [50, 50, 70])

                # Border
                dpg.add_theme_color(dpg.mvThemeCol_Border, [60, 60, 90])
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)

                # Tabs
                dpg.add_theme_color(dpg.mvThemeCol_Tab, [50, 50, 70])
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, [80, 80, 120])
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [70, 70, 100])

                # Buttons
                dpg.add_theme_color(dpg.mvThemeCol_Button, [60, 60, 90])
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered, [80, 80, 120])
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, [100, 100, 150])

                # Other UI colors
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [45, 45, 60])
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBgHovered, [55, 55, 75])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [65, 65, 85])
                dpg.add_theme_color(dpg.mvThemeCol_Separator, [80, 80, 120])
                dpg.add_theme_color(
                    dpg.mvThemeCol_PlotHistogram, [120, 120, 180])

                # Style settings
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5.0)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5.0)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 5.0)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 5.0)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

        return theme

    def _create_window_theme(self):
        """Create theme specific to windows."""
        with dpg.theme() as window_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [30, 30, 40])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [40, 40, 60])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [60, 60, 90])
                dpg.add_theme_color(
                    dpg.mvThemeCol_TitleBgCollapsed, [30, 30, 50])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [220, 220, 240])
                dpg.add_theme_color(dpg.mvThemeCol_Border, [60, 60, 90])
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, [50, 50, 70])
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)
        return window_theme

    def _create_game_state_tab(self):
        """Create the game state tab with controls and display."""
        with dpg.tab(label="Game State", tag="game_state_tab"):
            with dpg.group(horizontal=False):
                # Connection section
                with dpg.group():
                    with dpg.child_window(height=75, border=True):
                        with dpg.group(horizontal=True):
                            dpg.add_button(
                                label="Connect", width=120, callback=self.connect_to_solitaire)
                            dpg.add_button(
                                label="Refresh", width=120, callback=self.refresh_game_state)
                            dpg.add_checkbox(
                                label="Auto Refresh", default_value=True, callback=self.toggle_auto_refresh)

                dpg.add_spacer(height=10)

                # Solver controls section
                with dpg.child_window(height=265, border=True):
                    with dpg.group(horizontal=False):
                        dpg.add_text("Solver Controls", color=[180, 180, 220])
                        dpg.add_separator()
                        dpg.add_spacer(height=5)

                        # Solver button and iterations
                        with dpg.group(horizontal=True):
                            dpg.add_button(
                                label="Solve Game", width=120, height=30, callback=self.on_solve_button_clicked)
                            dpg.add_input_int(label="Max Iterations", default_value=self.max_iterations,
                                              callback=self.update_max_iterations, min_value=1000,
                                              max_value=1000000, step=1000, width=150)

                        dpg.add_spacer(height=10)

                        # Solver progress
                        dpg.add_text("Search Progress:")
                        dpg.add_progress_bar(
                            tag=self.solver_progress_bar_tag, default_value=0, width=-1, height=15)
                        dpg.add_text("Status:", color=[180, 180, 220])
                        dpg.add_text("Disconnected. Click Connect to start.",
                                     tag=self.status_tag, wrap=400, color=[220, 220, 150])

                        dpg.add_spacer(height=15)

                        # Heuristic slider
                        dpg.add_text("Solution Strategy:")
                        with dpg.group(horizontal=True):
                            dpg.add_text("Best", color=[150, 220, 150])
                            dpg.add_slider_float(default_value=self.heuristic_weight,
                                                 callback=self.update_heuristic_weight,
                                                 min_value=0.0, max_value=10.0, width=200)
                            dpg.add_text("Fast", color=[220, 150, 150])

                        # Add explanations
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_text(
                                    "Best = Better solution, potentially slower")
                            with dpg.group(horizontal=True):
                                dpg.add_text(
                                    "Fast = Quicker to find, may have more moves")

                dpg.add_spacer(height=10)

                # Game State Visualization
                with dpg.child_window(height=400, border=True, horizontal_scrollbar=True):
                    with dpg.group():
                        dpg.add_text("Game State Visualization",
                                     color=[180, 180, 220])
                        dpg.add_separator()
                        dpg.add_spacer(height=5)

                        # Create monospace text style
                        with dpg.theme() as mono_theme:
                            with dpg.theme_component(dpg.mvText):
                                dpg.add_theme_style(
                                    dpg.mvStyleVar_ItemSpacing, 0, 0)

                        # Game state visualization text area with monospace styling
                        visualization_text = dpg.add_text("Waiting for game state data...",
                                                          tag=self.visualization_text_tag,
                                                          wrap=0)  # Disable wrapping for proper formatting
                        dpg.bind_item_theme(visualization_text, mono_theme)

    def _create_solution_tab(self):
        """Create the solution tab with controls and display."""
        with dpg.tab(label="Solution Steps", tag="solution_steps_tab"):
            with dpg.group(horizontal=False):
                # Solution controls
                with dpg.child_window(height=140, border=True):
                    with dpg.group():
                        dpg.add_text("Solution Controls",
                                     color=[180, 180, 220])
                        dpg.add_separator()
                        dpg.add_spacer(height=5)

                        # Step indicator
                        with dpg.group(horizontal=True):
                            dpg.add_text("Current Step: ")
                            dpg.add_text("0/0", tag="step_counter",
                                         color=[220, 220, 150])

                        dpg.add_spacer(height=10)

                        # Controls
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Step", width=100,
                                           callback=self.execute_step)
                            dpg.add_button(label="Auto Execute",
                                           width=120, callback=self.execute_auto)
                            dpg.add_input_float(label="Delay (sec)", default_value=0.5, width=100,
                                                callback=self.update_delay, min_value=0.1, max_value=5.0, step=0.1)
                            dpg.add_button(label="Stop", tag=self.stop_button_tag, width=100,
                                           callback=self.toggle_execution)

                dpg.add_spacer(height=10)

                # Execution progress
                with dpg.child_window(height=80, border=True):
                    with dpg.group():
                        dpg.add_text("Execution Progress:",
                                     color=[180, 180, 220])
                        dpg.add_separator()
                        dpg.add_spacer(height=5)
                        dpg.add_progress_bar(
                            tag=self.progress_bar_tag, default_value=0, width=-1, height=15)

                dpg.add_spacer(height=10)

                # Solution text
                with dpg.child_window(autosize_x=True, height=400, border=True):
                    with dpg.group():
                        dpg.add_text("Solution:", color=[180, 180, 220])
                        dpg.add_separator()
                        dpg.add_spacer(height=5)
                        dpg.add_text("Solution will appear here when found.",
                                     tag=self.solution_text_tag, wrap=850)

    def set_application_icon(self):
        """Set custom application icon."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(
                script_dir, "..", "..", "assets", "solitaire.ico")

            if os.path.exists(icon_path):
                try:
                    dpg.set_viewport_small_icon(icon_path)
                except Exception:
                    pass

                try:
                    dpg.set_viewport_large_icon(icon_path)
                except Exception:
                    try:
                        abs_path = os.path.abspath(icon_path)
                        dpg.set_viewport_large_icon(abs_path)
                    except Exception:
                        pass
        except Exception:
            pass

    def update_max_iterations(self, sender, app_data, user_data):
        """Update maximum solver iterations."""
        self.max_iterations = app_data

    def update_heuristic_weight(self, sender, app_data, user_data):
        """Update heuristic weight for solver."""
        self.heuristic_weight = app_data

    def update_delay(self, sender, app_data, user_data):
        """Update delay between auto execution steps."""
        self.delay = app_data

    def toggle_auto_refresh(self, sender, app_data, user_data):
        """Toggle automatic game state refresh."""
        self.auto_refresh = app_data

    def auto_refresh_thread(self):
        """Thread for automatic game state refresh."""
        while self.continue_refresh:
            if self.auto_refresh and self.pm and self.pm.process_handle:
                self.refresh_game_state()
            time.sleep(self.refresh_interval)

    def connect_to_solitaire(self):
        """Connect to Solitaire game process."""
        self._safe_set_value(self.status_tag, "Connecting to Solitaire...")
        self.pm = memory_reader.get_solitaire_process()
        if self.pm:
            self._safe_set_value(self.status_tag,
                                 "Connected to Solitaire - Ready to solve")
            self.refresh_game_state()
        else:
            self._safe_set_value(
                self.status_tag, "Failed to connect to Solitaire - Check if the game is running")

    def refresh_game_state(self):
        """Refresh the game state display."""
        if not self.pm or not self.pm.process_handle:
            self._safe_set_value(self.status_tag, "Not connected to Solitaire")
            return

        try:
            self.game_state = memory_reader.read_game_state(self.pm)
            memory_reader.assign_pile_names(self.game_state)

            if self.game_state.get("error"):
                self._safe_set_value(self.status_tag,
                                     f"Error: {self.game_state['error']}")
                if "handle" in self.game_state["error"].lower() or "process" in self.game_state["error"].lower():
                    self.pm = None
                return

            self.hwnd = self.game_state.get("hwnd", 0)
            if self.hwnd == 0:
                self._safe_set_value(self.status_tag,
                                     "Warning: Could not get window handle")
            else:
                self._safe_set_value(self.status_tag, "Game state refreshed")

            # Update visualization
            try:
                formatted_state = display.format_game_state(self.game_state)
                self._safe_set_value(
                    self.visualization_text_tag, formatted_state)
            except Exception as viz_error:
                self._safe_set_value(
                    self.status_tag, f"Error updating visualization: {str(viz_error)}")

        except Exception as e:
            self._safe_set_value(
                self.status_tag, f"Error refreshing: {str(e)}")

    def _safe_set_value(self, tag, value):
        """Safely update a DPG UI element value with proper error handling."""
        try:
            # Check if UI is still active and tag exists
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
        except Exception as e:
            # If there's still an error, print to console instead of crashing
            print(f"Error setting value for {tag}: {str(e)}")

    def _safe_set_item_label(self, tag, label):
        """Safely update a DPG UI element label with proper error handling."""
        try:
            # Check if UI is still active and tag exists
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, label=label)
        except Exception as e:
            # If there's still an error, print to console instead of crashing
            print(f"Error setting label for {tag}: {str(e)}")

    def on_solve_button_clicked(self):
        """Handle solve button click."""
        if self.solving:
            self._safe_set_value(self.status_tag, "Solver is already running")
            return

        if not self.pm or not self.pm.process_handle:
            self._safe_set_value(
                self.status_tag, "Please connect to Solitaire first")
            return

        if not self.game_state:
            self._safe_set_value(
                self.status_tag, "Please refresh game state first")
            return

        self.solving = True
        self._safe_set_value(self.status_tag, "Starting solver...")
        self._safe_set_value(self.solver_progress_bar_tag, 0)
        self._safe_set_value(self.solution_text_tag,
                             "Searching for solution...\nPress 'Q' to stop the search early.")

        self.solver_thread = threading.Thread(
            target=self.solve_thread, daemon=True)
        self.solver_thread.start()

    def solve_thread(self):
        """Run solver in a separate thread."""
        try:
            # Convert game state
            solver_state = solver.from_reader_state(self.game_state)
            if not solver_state:
                self._safe_set_value(self.status_tag,
                                     "Error creating solver state from game state")
                self.solving = False
                return

            # Reset progress tracking
            with self.iteration_lock:
                self.current_iteration = 0
                self.best_solution = None
                self.best_winning_solution = None

            # Start progress monitor thread
            progress_monitor = threading.Thread(
                target=self.monitor_solver_progress, daemon=True)
            progress_monitor.start()

            # Define progress callback
            def update_progress(current_iteration, max_iterations, best_solution=None, best_winning_solution=None, status_info=None):
                with self.iteration_lock:
                    self.current_iteration = current_iteration
                    self.best_solution = best_solution
                    self.best_winning_solution = best_winning_solution
                    if status_info:
                        self.last_status_message = status_info.get(
                            "message", "")

            # Run solver
            solution = solver.solve(
                solver_state,
                max_iterations=self.max_iterations,
                heuristic_weight=self.heuristic_weight,
                progress_callback=update_progress
            )

            # Update solution
            self.solution = solution
            self.current_step = 0
            self.updating_solution_display = True

            move_count = len(
                solution.moves) if solution and solution.moves else 0

            if move_count > 0:
                self._safe_set_value(self.status_tag,
                                     f"Solution found with {move_count} moves")
                self._safe_set_value("step_counter", f"0/{move_count}")

                # Generate solution text
                solution_text = f"Found solution with {move_count} moves:\n\n"
                for i, move in enumerate(solution.moves):
                    solution_text += f"{i+1}. {solution_module.describe_move(move)}\n"
                self._safe_set_value(self.solution_text_tag, solution_text)
            else:
                self._safe_set_value(self.status_tag, "No solution found")
                self._safe_set_value(
                    self.solution_text_tag, "No solution found.")

            self.updating_solution_display = False

        except Exception as e:
            self._safe_set_value(self.status_tag, f"Error in solver: {str(e)}")

        finally:
            self.solving = False

    def monitor_solver_progress(self):
        """Monitor and update solver progress in the UI."""
        while self.solving:
            with self.iteration_lock:
                current = self.current_iteration
                progress = min(1.0, current / max(1, self.max_iterations))
                status = self.last_status_message or "Searching..."

                # Update UI elements
                self._safe_set_value(self.solver_progress_bar_tag, progress)
                self._safe_set_value(
                    self.status_tag, f"Iteration {current}/{self.max_iterations}: {status}")

                if self.best_solution:
                    foundation_count = self.best_solution.foundation_count
                    partial_msg = f"Best partial solution: {foundation_count}/52 cards in foundations"
                    solution_text = f"In progress...\n\n{partial_msg}\n\n"

                    if self.best_winning_solution:
                        win_moves = len(self.best_winning_solution.moves)
                        solution_text += f"Found winning solution with {win_moves} moves!\n\n"

                        # Show first few moves
                        max_preview = min(
                            10, len(self.best_winning_solution.moves))
                        for i in range(max_preview):
                            move = self.best_winning_solution.moves[i]
                            solution_text += f"{i+1}. {solution_module.describe_move(move)}\n"

                        if max_preview < len(self.best_winning_solution.moves):
                            solution_text += f"... and {len(self.best_winning_solution.moves) - max_preview} more moves\n"

                    self._safe_set_value(self.solution_text_tag, solution_text)

            time.sleep(0.1)

    def execute_step(self):
        """Execute one step of the solution."""
        if not self.solution or not self.solution.moves:
            self._safe_set_value(self.status_tag, "No solution available")
            return

        if self.current_step >= len(self.solution.moves):
            self._safe_set_value(
                self.status_tag, "Solution execution complete")
            return

        if not self.pm or not self.pm.process_handle:
            self._safe_set_value(self.status_tag, "Not connected to Solitaire")
            return

        if self.hwnd == 0:
            self._safe_set_value(
                self.status_tag, "Window handle not available")
            return

        move = self.solution.moves[self.current_step]
        self._safe_set_value(self.status_tag,
                             f"Executing: {solution_module.describe_move(move)}")

        success = memory_reader.execute_move(self.pm, self.hwnd, move)
        if success:
            self.current_step += 1
            self._safe_set_value("step_counter",
                                 f"{self.current_step}/{len(self.solution.moves)}")
            progress = self.current_step / len(self.solution.moves)
            self._safe_set_value(self.progress_bar_tag, progress)
        else:
            self._safe_set_value(self.status_tag,
                                 "Move execution failed. Try refreshing game state.")

    def execute_auto(self):
        """Execute solution automatically."""
        if self.auto_executing and not self.execution_paused:
            self._safe_set_value(self.status_tag,
                                 "Automatic execution already in progress")
            return

        # If execution was paused, resume it
        if self.execution_paused:
            self.execution_paused = False
            self.auto_executing = True
            self._safe_set_item_label(self.stop_button_tag, "Stop")
            self._safe_set_value(self.status_tag, "Resuming execution...")
            return

        self.auto_executing = True
        self.execution_paused = False
        self.should_stop_execution = False
        self._safe_set_item_label(self.stop_button_tag, "Stop")
        self.execute_thread = threading.Thread(
            target=self.execute_auto_thread, daemon=True)
        self.execute_thread.start()

    def execute_auto_thread(self):
        """Automatic solution execution thread."""
        try:
            self._safe_set_value(
                self.status_tag, "Starting automatic execution...")

            if not self.solution or not self.solution.moves:
                self._safe_set_value(self.status_tag, "No solution available")
                self.auto_executing = False
                return

            # Start from current step if resuming
            start_from_step = self.current_step

            # Set up a callback function that updates step counter
            def status_callback(msg):
                self._safe_set_value(self.status_tag, msg)
                # If message indicates a move is being executed, update step counter
                if msg.startswith("Move "):
                    try:
                        # Extract current move number from message like "Move 5/10: ..."
                        current_move = int(msg.split("/")[0].split(" ")[1]) - 1
                        self.current_step = current_move
                        self._safe_set_value(
                            "step_counter", f"{current_move}/{len(self.solution.moves)}")
                        progress = current_move / len(self.solution.moves)
                        self._safe_set_value(self.progress_bar_tag, progress)
                    except (ValueError, IndexError):
                        pass

            # Execute each move one by one (instead of using execute_solution)
            # to allow for proper pausing and resuming
            for i in range(start_from_step, len(self.solution.moves)):
                if not self.auto_executing:
                    # Execution was stopped
                    self._safe_set_value(self.status_tag, "Execution stopped.")
                    return

                if self.execution_paused:
                    # Execution was paused, wait until resumed
                    self._safe_set_value(self.status_tag, "Execution paused.")
                    while self.execution_paused and self.auto_executing:
                        time.sleep(0.1)

                    if not self.auto_executing:
                        self._safe_set_value(
                            self.status_tag, "Execution stopped.")
                        return

                    self._safe_set_value(self.status_tag, "Execution resumed.")

                move = self.solution.moves[i]
                self.current_step = i

                # Update progress display
                status_callback(
                    f"Move {i+1}/{len(self.solution.moves)}: {solution_module.describe_move(move)}")

                # Execute the move
                success = memory_reader.execute_move(self.pm, self.hwnd, move)

                if success:
                    time.sleep(self.delay)
                else:
                    self._safe_set_value(
                        self.status_tag, f"Move failed. State may be out of sync.")
                    # Try to refresh game state
                    self.refresh_game_state()
                    time.sleep(1)

            # Complete execution
            self.current_step = len(self.solution.moves)
            self._safe_set_value(
                "step_counter", f"{self.current_step}/{len(self.solution.moves)}")
            self._safe_set_value(self.progress_bar_tag, 1.0)
            self._safe_set_value(
                self.status_tag, "Solution execution completed.")

        except Exception as e:
            self._safe_set_value(self.status_tag,
                                 f"Error in auto execution: {str(e)}")

        finally:
            self.auto_executing = False
            self.execution_paused = False
            self._safe_set_item_label(self.stop_button_tag, "Stop")

    def toggle_execution(self):
        """Toggle between pause and resume of automatic execution."""
        if not self.auto_executing:
            self._safe_set_value(self.status_tag, "No execution in progress")
            return

        if self.execution_paused:
            # Resume execution
            self.execution_paused = False
            self._safe_set_item_label(self.stop_button_tag, "Stop")
            self._safe_set_value(self.status_tag, "Resuming execution...")
        else:
            # Pause execution
            self.execution_paused = True
            self._safe_set_item_label(self.stop_button_tag, "Resume")
            self._safe_set_value(self.status_tag, "Pausing execution...")
