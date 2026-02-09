"""
This module implements a 4x4 grid GUI for 2048 AI synchronization.
States:
- SETUP: User manually enters the board.
- THINKING: GUI waits for HTTP response from AI server.
- MOVE_WAITING: AI suggestion is displayed; waiting for keyboard input.
- MOVE_DONE: Move executed; waiting for tile spawn location.

Main Flow:
  SETUP → THINKING → MOVE_WAITING → MOVE_DONE → SETUP
"""
import tkinter as tk
from tkinter import messagebox
import requests
import threading
import copy
import platform

# --- Configuration & Constants ---
SERVER_URL = "http://localhost:8080/move"

# Colors (Gabriele Cirulli style)
COLORS = {
    'bg': "#faf8ef",
    'grid_bg': "#bbada0",
    'tile_empty': "#cdc1b4",
    'text_dark': "#776e65",
    'text_light': "#f9f6f2",
    2: "#eee4da",
    4: "#ede0c8",
    8: "#f2b179",
    16: "#f59563",
    32: "#f67c5f",
    64: "#f65e3b",
    128: "#edcf72",
    256: "#edcc61",
    512: "#edc850",
    1024: "#edc53f",
    2048: "#edc22e",
    'super': "#3c3a32" # For > 2048
}

FONT_SCORE_LABEL = ("Verdana", 12, "bold")
FONT_SCORE_VAL = ("Verdana", 20, "bold")
FONT_TILE = ("Clear Sans", 24, "bold")
FONT_MSG = ("Helvetica", 12)
FONT_ARROW = ("Arial", 50, "bold")

# Game States
STATE_SETUP = "STATE_SETUP"
STATE_THINKING = "STATE_THINKING"
STATE_MOVE_WAITING = "STATE_MOVE_WAITING" # Waiting for user to press arrow
STATE_MOVE_DONE = "STATE_MOVE_DONE"       # Move done, waiting for spawn click

# Platform-specific right-click
RIGHT_CLICK = "<Button-2>" if platform.system() == "Darwin" else "<Button-3>"

class Game2048GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2048 AI Interface")
        self.root.geometry("700x430")
        self.root.configure(bg=COLORS['bg'])

        # --- Game Data ---
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        
        # Undo history: (board_copy, score_copy)
        self.undo_stack = None 
        
        # self.current_state = STATE_SETUP
        self.suggested_move = None
        
        # Timer reference for message cycling
        self.msg_timer = None
        self.inactivity_counter = 0

        # --- UI Setup ---
        self._setup_ui()
        
        # Bindings
        self.root.bind("<Key>", self.handle_keypress)
        self.root.bind("<Button-1>", self.clear_focus, add="+")
        self.root.bind(RIGHT_CLICK, self.clear_focus, add="+")

        # Initial Draw
        self.update_board_ui()
        self.set_state(STATE_SETUP)

    def _setup_ui(self):
        # Main Container
        main_frame = tk.Frame(self.root, bg=COLORS['bg'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # -- Left Area: Board --
        self.left_frame = tk.Frame(main_frame, bg=COLORS['grid_bg'], width=400, height=400)
        self.left_frame.pack(side="left", padx=(0, 20))
        self.left_frame.pack_propagate(False) # Force size

        # Initialize Grid Tiles (Labels)
        self.tiles = []
        for r in range(4):
            row_tiles = []
            for c in range(4):
                # Frame for padding/spacing
                f = tk.Frame(self.left_frame, bg=COLORS['tile_empty'], width=85, height=85)
                f.grid(row=r, column=c, padx=5, pady=5)
                f.pack_propagate(False)
                
                # The label displaying the number
                l = tk.Label(f, text="", bg=COLORS['tile_empty'], font=FONT_TILE)
                l.pack(fill="both", expand=True)
                
                # Bind click event to the label and the frame
                l.bind("<Button-1>", lambda e, r=r, c=c: self.handle_tile_click(r, c, 1))
                f.bind("<Button-1>", lambda e, r=r, c=c: self.handle_tile_click(r, c, 1))
                # Right click for reverse progression
                l.bind(RIGHT_CLICK, lambda e, r=r, c=c: self.handle_tile_click(r, c, -1))
                f.bind(RIGHT_CLICK, lambda e, r=r, c=c: self.handle_tile_click(r, c, -1))
                
                row_tiles.append((f, l))
            self.tiles.append(row_tiles)

        # -- Right Area: Info --
        self.right_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        self.right_frame.pack(side="left", fill="both", expand=True)

        # Slot 1: Score
        score_frame = tk.Frame(self.right_frame, bg=COLORS['bg'])
        score_frame.pack(fill="x", pady=(0, 10))
        tk.Label(score_frame, text="SCORE", bg=COLORS['bg'], fg=COLORS['text_dark'], font=FONT_SCORE_LABEL).pack(anchor="w")
        
        # Editable Score Entry
        self.score_var = tk.StringVar(value="0")
        self.score_entry = tk.Entry(score_frame, textvariable=self.score_var, font=FONT_SCORE_VAL, width=10, justify="center")
        self.score_entry.pack(anchor="w")
        # Validate score input to be numeric
        vcmd = (self.root.register(self.validate_score), '%P')
        self.score_entry.configure(validate="key", validatecommand=vcmd)
        # When the user presses Enter while inside the score box
        self.score_entry.bind("<Return>", lambda e: self.root.focus_set())
        self.score_entry.bind("<KP_Enter>", lambda e: self.root.focus_set())

        # Slot 2: AI Suggestion
        ai_frame = tk.Frame(self.right_frame, bg=COLORS['bg'], height=100)
        ai_frame.pack(fill="x", pady=(0,10))
        tk.Label(ai_frame, text="AI SUGGESTION", bg=COLORS['bg'], fg=COLORS['text_dark'], font=FONT_SCORE_LABEL).pack(anchor="w")
        
        self.arrow_label = tk.Label(ai_frame, text="", bg=COLORS['bg'], fg="#f65e3b", font=FONT_ARROW)
        self.arrow_label.pack(anchor="center")

        # Slot 3: Messages
        msg_frame = tk.Frame(self.right_frame, bg=COLORS['grid_bg'], padx=10, pady=10)
        msg_frame.pack(fill="x", pady=0)
        
        self.msg_label = tk.Label(msg_frame, text="Welcome...", bg=COLORS['grid_bg'], fg="#f9f6f2", 
                                  font=FONT_MSG, wraplength=240, justify="left")
        self.msg_label.pack(anchor="nw")

    # --- Logic: Validation & Helpers ---

    def validate_score(self, new_val):
        if new_val == "": return True
        return new_val.isdigit()

    def update_score_display(self):
        self.score_var.set(str(self.score))

    def update_board_ui(self):
        for r in range(4):
            for c in range(4):
                val = self.board[r][c]
                frame, label = self.tiles[r][c]
                
                # Background color
                bg_color = COLORS.get(val, COLORS['super']) if val > 2048 else COLORS.get(val, COLORS['tile_empty'])
                if val == 0: bg_color = COLORS['tile_empty']
                
                # Text color
                fg_color = COLORS['text_dark'] if val in (2, 4) else COLORS['text_light']
                
                text = str(val) if val > 0 else ""
                
                frame.config(bg=bg_color)
                label.config(text=text, bg=bg_color, fg=fg_color)

    def encode_board(self):
        """Encodes board to the specific hex string format for the AI server."""
        # 0->0, 2->1, 4->2 ... 1024->A, 2048->B ...
        mapping = "0123456789ABCDEF"
        board_str = ""
        for r in range(4):
            for c in range(4):
                val = self.board[r][c]
                if val == 0:
                    board_str += "0"
                else:
                    # log2(val)
                    power = val.bit_length() - 1
                    if power < 16:
                        board_str += mapping[power]
                    else:
                        board_str += "F" # Fallback for extremely high numbers
        return board_str

    # --- State Machine Management ---

    def set_state(self, new_state):
        self.current_state = new_state
        if self.msg_timer:
            self.root.after_cancel(self.msg_timer)
            self.msg_timer = None

        if new_state == STATE_SETUP:
            self.arrow_label.config(text="") # Clear arrow
            self.score_entry.config(state="normal")
            self.msg_label.config(text="It's time to set up your board.\n\nClick on any tile repeatedly to cycle numbers.\n\nUpdate the score to reflect your actual game.\n\nPress ENTER when done.")
        
        elif new_state == STATE_THINKING:
            self.score_entry.config(state="disabled") # Lock score logic start
            self.msg_label.config(text="Thinking...")
            # Run network request in thread
            threading.Thread(target=self.query_ai, daemon=True).start()

        elif new_state == STATE_MOVE_WAITING:
            # Score editable only before move
            self.score_entry.config(state="normal") 
            self.msg_label.config(text="Here's the suggested move.\n\nUse ARROW KEYS to move the board.\n(Up, Down, Left, Right)")

        elif new_state == STATE_MOVE_DONE:
            # Score disabled to prevent sync issues vs Undo
            self.score_entry.config(state="disabled") 
            self.msg_label.config(text="The move is done.\n\nWhere did the new tile appear?\n\nClick any of the empty tiles to tell me.")
            self.inactivity_counter = 0
            self.start_message_cycle()

    def start_message_cycle(self):
        """Cycles messages in STATE_MOVE_DONE based on inactivity."""
        self.inactivity_counter += 1
        
        if self.inactivity_counter > 1: # After ~6 seconds
            msgs = [
                "Not the correct move?\n\nUndo with Ctrl-Z.",
                "Where did the new tile appear?\n\nGo ahead and set up the board and score to reflect your actual game."
            ]
            # Cycle through messages based on counter
            idx = (self.inactivity_counter) % 2
            self.msg_label.config(text=msgs[idx])
            
        self.msg_timer = self.root.after(6000, self.start_message_cycle)

    # --- Interaction Handlers ---

    def handle_keypress(self, event):
        key = event.keysym
        
        if self.current_state == STATE_SETUP:
            if key in ["Return", "KP_Enter"]:
                # Validate score sync
                try:
                    self.score = int(self.score_var.get())
                except ValueError:
                    self.score = 0
                self.set_state(STATE_THINKING)
                
        elif self.current_state == STATE_MOVE_WAITING:
            if key in ["Up", "Down", "Left", "Right"]:
                # Sync score just in case user edited it before pressing arrow
                try:
                    self.score = int(self.score_var.get())
                except ValueError:
                    pass
                self.perform_game_move(key)
        
        elif self.current_state == STATE_MOVE_DONE:
            # Check for Undo
            if (event.state & 0x0004) and (key.lower() == 'z'): # Ctrl+Z
                self.undo_move()
            # Also support standard keysym for undo on some OS
            elif key == "Undo": 
                self.undo_move()
    
    def clear_focus(self, event):
        # If the widget clicked isn't the score entry, shift focus to the root
        if event.widget != self.score_entry:
            self.root.focus_set()

    def handle_tile_click(self, r, c, direction=1):
        if self.current_state == STATE_SETUP:
            self.cycle_tile(r, c, direction)
            
        elif self.current_state == STATE_MOVE_DONE:
            # This is the transition where user places the spawn

            # 1. Commit the move (clear undo essentially, though we just drop the stack)
            self.undo_stack = None
                
            # 2. Transition logic:
            self.set_state(STATE_SETUP)
            self.msg_label.config(text="Continue setting up if needed.\n\nPress ENTER to get next suggestion.")
            self.cycle_tile(r, c, direction)

    def cycle_tile(self, r, c, direction=1):
        progression = [0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        current_val = self.board[r][c]
        
        # Get current index, or 0 if somehow not in list
        try:
            idx = progression.index(current_val)
        except ValueError:
            idx = 0
            
        # Calculate new index with wrap-around logic
        new_idx = (idx + direction) % len(progression)
        self.board[r][c] = progression[new_idx]
        self.update_board_ui()

    # --- Core AI & Game Logic ---

    def query_ai(self):
        board_str = self.encode_board()
        url = f"{SERVER_URL}?board={board_str}"
        
        try:
            response = requests.get(url, timeout=5)
            # Process in main thread
            self.root.after(0, self.process_ai_response, response)
        except Exception as e:
            self.root.after(0, self.handle_ai_error, str(e))

    def process_ai_response(self, response):
        if response.status_code != 200:
            self.handle_ai_error(f"Status {response.status_code}")
            return

        move_char = response.text.strip()
        
        arrows = {
            'u': '↑', 'd': '↓', 'l': '←', 'r': '→',
            'g': 'GAME\nOVER'
        }
        
        if move_char == 'g':
            self.arrow_label.config(text=arrows['g'], fg="red", font=("Arial", 20, "bold"))
            self.msg_label.config(text="Sorry, there are no more valid moves.\nGame Over!\n\n(Edit board to reset)")
            # We effectively stay in a "dead" state until user manually edits board (clicks tile)
            # Resetting to Setup mode allows them to fix it.
            self.current_state = STATE_SETUP 
            self.score_entry.config(state="normal")
        elif move_char in arrows:
            self.arrow_label.config(text=arrows[move_char], fg="#f65e3b", font=FONT_ARROW)
            self.set_state(STATE_MOVE_WAITING)
        else:
            self.handle_ai_error(f"Unknown response: {move_char}")

    def handle_ai_error(self, err_msg):
        messagebox.showerror("AI Error", f"Could not contact AI server:\n{err_msg}")
        self.set_state(STATE_SETUP)

    # --- 2048 Move Implementation ---

    def perform_game_move(self, key_direction):
        """
        Executes the move on the internal board.
        Saves state for Undo.
        Updates Score.
        """
        # Save state for Undo
        prev_board = copy.deepcopy(self.board)
        prev_score = self.score
        
        # Map key to vector
        vectors = {
            "Up": (-1, 0), "Down": (1, 0),
            "Left": (0, -1), "Right": (0, 1)
        }
        dr, dc = vectors[key_direction]
        
        moved, new_board, score_gain = self.logic_move(self.board, dr, dc)
        
        if moved:
            self.undo_stack = (prev_board, prev_score)
            self.board = new_board
            self.score += score_gain
            self.update_score_display()
            self.update_board_ui()
            self.set_state(STATE_MOVE_DONE)
        else:
            # Invalid move (nothing changed)
            # Usually in 2048 game logic, if a move does nothing, it's ignored.
            pass

    def undo_move(self):
        if self.undo_stack:
            self.board, self.score = self.undo_stack
            self.undo_stack = None # Clear stack (one level undo)
            self.update_board_ui()
            self.update_score_display()
            self.set_state(STATE_MOVE_WAITING)
        else:
            print("Nothing to undo")

    def logic_move(self, board, dr, dc):
        """
        Generic 2048 move logic.
        Returns (moved_boolean, new_board, score_gained)
        """
        # We'll rotate the board so we always process "Left" logic, then rotate back
        # This simplifies the merging logic significantly.
        
        # Standardize to Left:
        # Up: Rotate 270 (or -90)
        # Right: Rotate 180
        # Down: Rotate 90
        # Left: 0
        
        k = 0
        if (dr, dc) == (-1, 0): k = 1 # Up
        elif (dr, dc) == (0, 1): k = 2 # Right
        elif (dr, dc) == (1, 0): k = 3 # Down
        
        working_board = self.rotate_board(board, k)
        
        # Process Left Move
        new_board_arr = []
        total_score = 0
        moved = False
        
        for r in range(4):
            row = working_board[r]
            # 1. Compress (remove zeros)
            non_zeros = [x for x in row if x != 0]
            
            # 2. Merge
            merged = []
            skip = False
            for i in range(len(non_zeros)):
                if skip:
                    skip = False
                    continue
                val = non_zeros[i]
                if i + 1 < len(non_zeros) and non_zeros[i+1] == val:
                    merged.append(val * 2)
                    total_score += (val * 2)
                    skip = True
                else:
                    merged.append(val)
            
            # 3. Fill zeros
            while len(merged) < 4:
                merged.append(0)
                
            if merged != row:
                moved = True
            new_board_arr.append(merged)
            
        # Rotate back (4-k)
        final_board = self.rotate_board(new_board_arr, (4 - k) % 4)
        
        return moved, final_board, total_score

    def rotate_board(self, board, k):
        """Rotate board 90 degrees Anti-Clockwise k times"""
        b = copy.deepcopy(board)
        for _ in range(k):
            # Transpose + Reverse (standard matrix rotation)
            # To rotate 90 Counter Clockwise:
            # New[i][j] = Old[j][Width-1-i]
            new_b = [[0]*4 for _ in range(4)]
            for r in range(4):
                for c in range(4):
                    new_b[r][c] = b[c][3-r]
            b = new_b
        return b

if __name__ == "__main__":
    root = tk.Tk()
    app = Game2048GUI(root)
    root.mainloop()