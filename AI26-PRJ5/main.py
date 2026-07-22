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
    "Safe, Mine, HiddenNeighbor, FrontierClue"
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

    HiddenNeighbor(R, C, R2, C2) <= Adjacent(R, C, R2, C2) & UnknownCell(R2, C2)
    FrontierClue(R, C, N, F) <= Value(R, C, N) & FlaggedNeighborCount(R, C, F)


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

                if hidden_count == 0:
                    continue  # fully resolved, can't inform Safe/Mine anymore

                +Value(r, c, val)
                dynamic_facts.append((Value, (r, c, val)))

                +FlaggedNeighborCount(r, c, flagged_count)
                dynamic_facts.append((FlaggedNeighborCount, (r, c, flagged_count)))

                +HiddenNeighborCount(r, c, hidden_count)
                dynamic_facts.append((HiddenNeighborCount, (r, c, hidden_count)))


def build_frontier_constraints():
    constraints = []
    for r, c, n, f in FrontierClue(R, C, N, F):
        unknown = {(r2, c2) for r2, c2 in HiddenNeighbor(r, c, R2, C2)}
        if unknown:
            constraints.append([unknown, n - f])
    return constraints


def frontier_subset_inference():
    constraints = build_frontier_constraints()
    safe_cells = set()
    mine_cells = set()

    changed = True
    while changed:
        changed = False

        # Fold in anything learned so far: drop known cells from each
        # constraint and account for any known mines in its value.
        refreshed = []
        for cells, val in constraints:
            known_mines_here = cells & mine_cells
            cells = cells - safe_cells - mine_cells
            val -= len(known_mines_here)
            if cells:
                refreshed.append([cells, val])
        constraints = refreshed

        # Trivial resolution: remaining_mines == 0 -> all safe;
        # remaining_mines == len(frontier) -> all mines.
        remaining = []
        for cells, val in constraints:
            if val <= 0:
                if not cells <= safe_cells:
                    changed = True
                safe_cells.update(cells)
            elif val >= len(cells):
                if not cells <= mine_cells:
                    changed = True
                mine_cells.update(cells)
            else:
                remaining.append([cells, val])
        constraints = remaining

        # Pairwise elimination between overlapping frontiers.
        for i in range(len(constraints)):
            for j in range(len(constraints)):
                if i == j:
                    continue
                set_i, val_i = constraints[i]
                set_j, val_j = constraints[j]
                if set_i.isdisjoint(set_j):
                    continue

                only_i = set_i - set_j
                only_j = set_j - set_i
                diff = val_i - val_j

                if only_i and diff == len(only_i):
                    mine_cells.update(only_i)
                    safe_cells.update(only_j)
                    changed = True
                elif only_j and diff == -len(only_j):
                    mine_cells.update(only_j)
                    safe_cells.update(only_i)
                    changed = True

    return list(safe_cells), list(mine_cells)


def query_solver():
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

    frontier_safe, frontier_mines = frontier_subset_inference()
    safe_moves.extend(move for move in frontier_safe if move not in safe_moves)
    mine_moves.extend(move for move in frontier_mines if move not in mine_moves)

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
    ms = MineSweeper(rows=20, cols=20, mines=75, seed=123, auto_flood_fill=False)
    prolog_solver(ms)
