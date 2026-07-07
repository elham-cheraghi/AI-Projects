import random
import time

import pygame
from pyDatalog import pyDatalog
from src.minesweeper import MineSweeper

# =========================================================================
# Section 1: Define First-Order Logic Terms (FOL Terms)
# Students should define the required terms, facts, and rules for pyDatalog here.
# =========================================================================
# Hint: pyDatalog.create_terms('X, Y, R, C, ...')

pyDatalog.create_terms(
    "R, C, R2, C2, N, F, U, "
    "Adjacent, Value, FlaggedNeighborCount, HiddenNeighborCount, UnknownCell, "
    "Safe, Mine"
)

# Suggested constants for the agent's internal memory (Shadow Board)
AGENT_UNKNOWN = -1
AGENT_FLAGGED = -2

dynamic_facts = []

def get_neighbors(r, c, rows, cols):
    """Returns the list of valid (row, col) coordinates adjacent to (r, c)."""
    neighbors = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbors.append((nr, nc))
    return neighbors


# =========================================================================
# Section 2: Generation of Logical Facts and Rules
# =========================================================================


def init_static_facts(rows, cols):
    """
    Task 1: Generate static facts at the beginning of the game
    (e.g., adjacency relationships between cells).
    """
    for r in range(rows):
        for c in range(cols):
            for nr, nc in get_neighbors(r, c, rows, cols):
                +Adjacent(r, c, nr, nc)


def init_rules():
    """
    Task 2: Define logical inference rules (Safety Rule and Danger Rule).
    According to the project documentation, rules must be defined based on first-order logic.
    """
    Safe(R2, C2) <= (
        Value(R, C, N)
        & FlaggedNeighborCount(R, C, N)
        & Adjacent(R, C, R2, C2)
        & UnknownCell(R2, C2)
    )

    Mine(R2, C2) <= (
        Value(R, C, N)
        & FlaggedNeighborCount(R, C, F)
        & HiddenNeighborCount(R, C, U)
        & (N == F + U)
        & (U > 0)
        & Adjacent(R, C, R2, C2)
        & UnknownCell(R2, C2)
    )


def update_knowledge_base(agent_board, rows, cols):
    """
    Task 3: Convert the agent's internal memory (agent_board) into dynamic facts in each turn.
    Before adding new facts, facts from the previous turn must be cleared.
    """
    global dynamic_facts

    for relation, args in dynamic_facts:
        -relation(*args)
    dynamic_facts = []

    for r in range(rows):
        for c in range(cols):
            val = agent_board[(r, c)]

            if val == AGENT_UNKNOWN:
                +UnknownCell(r, c)
                dynamic_facts.append((UnknownCell, (r, c)))
            elif val == AGENT_FLAGGED:
                continue
            else:
                # Revealed cell with a numeric clue (0-8)
                neighbors = get_neighbors(r, c, rows, cols)
                flagged_count = sum(
                    1
                    for (nr, nc) in neighbors
                    if agent_board[(nr, nc)] == AGENT_FLAGGED
                )
                hidden_count = sum(
                    1
                    for (nr, nc) in neighbors
                    if agent_board[(nr, nc)] == AGENT_UNKNOWN
                )

                +Value(r, c, val)
                dynamic_facts.append((Value, (r, c, val)))

                +FlaggedNeighborCount(r, c, flagged_count)
                dynamic_facts.append((FlaggedNeighborCount, (r, c, flagged_count)))

                +HiddenNeighborCount(r, c, hidden_count)
                dynamic_facts.append((HiddenNeighborCount, (r, c, hidden_count)))


def query_solver():
    """
    Task 4: Query the inference engine to find safe cells and mines.
    Output: Two lists containing the coordinates of safe cells and mine cells.
    """
    safe_moves = []
    mine_moves = []

    # Code for querying Safe(R, C) and Mine(R, C)
    safe_result = Safe(R2, C2)
    if safe_result:
        for r, c in safe_result:
            if (r, c) not in safe_moves:
                safe_moves.append((r, c))

    mine_result = Mine(R2, C2)
    if mine_result:
        for r, c in mine_result:
            if (r, c) not in mine_moves:
                mine_moves.append((r, c))

    return safe_moves, mine_moves


# =========================================================================
# Section 3: Uncertainty Handling Strategy (Smart Guess) - Optional/Bonus
# =========================================================================


def get_safest_guess(agent_board, rows, cols):
    """
    Task 5 (Optional): Calculate the probability of cells being mines during a logical deadlock.
    """
    mine_probabilities = {}

    for r in range(rows):
        for c in range(cols):
            val = agent_board[(r, c)]
            if val in (AGENT_UNKNOWN, AGENT_FLAGGED):
                continue

            neighbors = get_neighbors(r, c, rows, cols)
            flagged = [n for n in neighbors if agent_board[n] == AGENT_FLAGGED]
            unknown = [n for n in neighbors if agent_board[n] == AGENT_UNKNOWN]

            if not unknown:
                continue

            remaining_mines = val - len(flagged)
            if remaining_mines < 0:
                continue

            probability = remaining_mines / len(unknown)
            for cell in unknown:
                mine_probabilities.setdefault(cell, []).append(probability)

    if not mine_probabilities:
        return None

    # Pick the unknown cell with the lowest average estimated mine probability
    best_cell = min(
        mine_probabilities,
        key=lambda cell: sum(mine_probabilities[cell]) / len(mine_probabilities[cell]),
    )
    return best_cell


# =========================================================================
# Section 4: Main Agent Loop
# =========================================================================


def prolog_solver(game):
    # Initialize static facts and rules
    init_static_facts(game.rows, game.cols)
    init_rules()

    # Create agent's internal memory (Shadow Board) - initially all cells are unknown
    agent_board = {}
    for r in range(game.rows):
        for c in range(game.cols):
            agent_board[(r, c)] = AGENT_UNKNOWN

    # Get starting position (Guaranteed to be 0 and safe according to the project documentation)
    start_r, start_c = game.get_start_pos()
    print(f"Starting at guaranteed safe position: {start_r}, {start_c}")

    # First move: Reveal the starting cell and record it in the agent's memory
    start_val = game.reveal(start_r, start_c)
    agent_board[(start_r, start_c)] = start_val if start_val is not None else 0

    running = True
    while running and not game.game_over:
        # Handle Pygame events to prevent the window from freezing/crashing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Update the knowledge base based on the latest state of the agent's memory
        update_knowledge_base(agent_board, game.rows, game.cols)

        # 2. Query the logic engine
        safe_moves, mine_moves = query_solver()
        move_made = False

        # 3. Apply the extracted logical actions to the game environment and update memory
        # Hint: Reveal safe cells first, then flag the mine cells.
        for r, c in safe_moves:
            if agent_board[(r, c)] == AGENT_UNKNOWN:
                val = game.reveal(r, c)
                agent_board[(r, c)] = val if val is not None else 0
                move_made = True
                if game.game_over:
                    break

        if not game.game_over:
            for r, c in mine_moves:
                if agent_board[(r, c)] == AGENT_UNKNOWN:
                    game.flag(r, c)
                    agent_board[(r, c)] = AGENT_FLAGGED
                    move_made = True

        # 4. Deadlock management (if no deterministic logical move is found)
        if not move_made and not game.game_over:
            print("Logical deadlock! Attempting guess...")
            # First use the Heuristic, and if no data is available, make a completely random choice
            guess = get_safest_guess(agent_board, game.rows, game.cols)
            if guess is None:
                unknown_cells = [
                    pos for pos, value in agent_board.items() if value == AGENT_UNKNOWN
                ]
                if unknown_cells:
                    guess = random.choice(unknown_cells)

            if guess is not None:
                r, c = guess
                val = game.reveal(r, c)
                agent_board[(r, c)] = val if val is not None else 0

        # Render the environment and add a short delay to observe the solving process
        game.render()
        time.sleep(0.2)

    # Keep the window open after the game ends
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        game.render()


if __name__ == "__main__":
    # Default settings based on the first scenario (Simple level) in the evaluation table
    # Note: auto_flood_fill must be False to preserve the encapsulation of the agent's memory.
    ms = MineSweeper(rows=45, cols=80, mines=200, seed=-1, auto_flood_fill=False)
    prolog_solver(ms)
