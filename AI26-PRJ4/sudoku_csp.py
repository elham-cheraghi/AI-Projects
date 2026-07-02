from collections import deque


INITIAL_GRID = [
    [1, 0, 0, 0, 6, 0],
    [0, 0, 3, 0, 0, 0],
    [0, 5, 0, 0, 0, 2],
    [0, 0, 0, 4, 0, 0],
    [0, 0, 0, 2, 0, 0],
    [0, 2, 0, 0, 0, 5],
]

SIZE = 6
BLOCK_ROWS = 2
BLOCK_COLS = 3
VALUES = list(range(1, SIZE + 1))


def print_grid(grid):
    border = ("+" + "-" * (2 * BLOCK_COLS + 1)) * (SIZE // BLOCK_COLS) + "+"
    print(border)
    for row_index, row_values in enumerate(grid):
        row = "|"
        for col_index, value in enumerate(row_values):
            row += " " + (str(value) if value else ".")
            if (col_index + 1) % BLOCK_COLS == 0:
                row += " |"
        print(row)
        if (row_index + 1) % BLOCK_ROWS == 0:
            print(border)


def create_variables():
    return [(row, col) for row in range(SIZE) for col in range(SIZE)]


def create_domains(grid):
    return {
        (row, col): [grid[row][col]] if grid[row][col] else list(VALUES)
        for row in range(SIZE)
        for col in range(SIZE)
    }


def build_neighbors():
    neighbors = {}
    for row, col in create_variables():
        peers = set()
        peers.update((row, other_col) for other_col in range(SIZE) if other_col != col)
        peers.update((other_row, col) for other_row in range(SIZE) if other_row != row)

        block_row = (row // BLOCK_ROWS) * BLOCK_ROWS
        block_col = (col // BLOCK_COLS) * BLOCK_COLS
        peers.update(
            (peer_row, peer_col)
            for peer_row in range(block_row, block_row + BLOCK_ROWS)
            for peer_col in range(block_col, block_col + BLOCK_COLS)
            if (peer_row, peer_col) != (row, col)
        )
        neighbors[(row, col)] = peers
    return neighbors


def initial_assignment(grid):
    return {
        (row, col): grid[row][col]
        for row in range(SIZE)
        for col in range(SIZE)
        if grid[row][col]
    }


def is_consistent(assignment, variable, value, neighbors):
    return all(assignment.get(neighbor) != value for neighbor in neighbors[variable])


def get_legal_values(variable, assignment, domains, neighbors):
    return [
        value
        for value in domains[variable]
        if is_consistent(assignment, variable, value, neighbors)
    ]


def select_static(assignment, domains, variables, neighbors):
    for variable in variables:
        if variable not in assignment:
            return variable
    return None


def select_mrv(assignment, domains, variables, neighbors):
    unassigned = [variable for variable in variables if variable not in assignment]
    if not unassigned:
        return None
    return min(
        unassigned,
        key=lambda variable: (
            len(get_legal_values(variable, assignment, domains, neighbors)),
            variables.index(variable),
        ),
    )


def select_mrv_forward_checking(assignment, domains, variables, neighbors):
    unassigned = [variable for variable in variables if variable not in assignment]
    if not unassigned:
        return None
    indexes = {variable: index for index, variable in enumerate(variables)}
    return min(unassigned, key=lambda variable: (len(domains[variable]), indexes[variable]))


def forward_check(variable, value, domains, neighbors, assignment):
    new_domains = {key: list(values) for key, values in domains.items()}
    for neighbor in neighbors[variable]:
        if neighbor not in assignment and value in new_domains[neighbor]:
            new_domains[neighbor].remove(value)
            if not new_domains[neighbor]:
                return None
    return new_domains


def backtrack(
    assignment,
    domains,
    variables,
    neighbors,
    counter,
    selector,
    use_forward_checking=False,
):
    if len(assignment) == len(variables):
        return dict(assignment)

    variable = selector(assignment, domains, variables, neighbors)

    for value in sorted(domains[variable]):
        counter["nodes"] += 1
        if use_forward_checking:
            if not is_consistent(assignment, variable, value, neighbors):
                continue
            next_domains = forward_check(variable, value, domains, neighbors, assignment)
            if next_domains is None:
                continue
            assignment[variable] = value
            result = backtrack(
                assignment,
                next_domains,
                variables,
                neighbors,
                counter,
                selector,
                use_forward_checking=True,
            )
        else:
            if not is_consistent(assignment, variable, value, neighbors):
                continue
            assignment[variable] = value
            result = backtrack(
                assignment,
                domains,
                variables,
                neighbors,
                counter,
                selector,
            )

        if result is not None:
            return result
        del assignment[variable]

    return None


def revise(domains, first, second):
    removed = [
        value
        for value in domains[first]
        if not any(other_value != value for other_value in domains[second])
    ]
    for value in removed:
        domains[first].remove(value)
    return bool(removed)


def ac3(domains, neighbors):
    queue = deque((first, second) for first in domains for second in neighbors[first])
    while queue:
        first, second = queue.popleft()
        if revise(domains, first, second):
            if not domains[first]:
                return False
            queue.extend(
                (neighbor, first)
                for neighbor in neighbors[first]
                if neighbor != second
            )
    return True


def prepare_forward_checking(grid, neighbors):
    domains = create_domains(grid)
    assignment = {}
    for variable, value in sorted(initial_assignment(grid).items()):
        domains = forward_check(variable, value, domains, neighbors, assignment)
        if domains is None:
            return None, assignment
        assignment[variable] = value
    return domains, assignment


def assignment_to_grid(assignment):
    grid = [[0] * SIZE for _ in range(SIZE)]
    for (row, col), value in assignment.items():
        grid[row][col] = value
    return grid


def validate_solution(assignment, neighbors):
    if len(assignment) != SIZE * SIZE:
        return False
    return all(
        assignment.get(neighbor) != value
        for variable, value in assignment.items()
        for neighbor in neighbors[variable]
    )


def run_search(label, selector, variables, neighbors, domains, assignment, use_forward_checking):
    counter = {"nodes": 0}
    solution = backtrack(
        dict(assignment),
        domains,
        variables,
        neighbors,
        counter,
        selector,
        use_forward_checking,
    )
    return label, {"solution": solution, "nodes": counter["nodes"]}


def solve_all_methods():
    variables = create_variables()
    neighbors = build_neighbors()
    givens = initial_assignment(INITIAL_GRID)

    results = {}
    for label, selector in [
        ("Backtracking", select_static),
        ("Backtracking + MRV", select_mrv),
    ]:
        name, result = run_search(
            label,
            selector,
            variables,
            neighbors,
            create_domains(INITIAL_GRID),
            givens,
            False,
        )
        results[name] = result

    domains_fc, assignment_fc = prepare_forward_checking(INITIAL_GRID, neighbors)
    name, result = run_search(
        "Backtracking + MRV + Forward Checking",
        select_mrv_forward_checking,
        variables,
        neighbors,
        domains_fc,
        assignment_fc,
        True,
    )
    results[name] = result

    domains_ac3 = create_domains(INITIAL_GRID)
    ac3(domains_ac3, neighbors)
    name, result = run_search(
        "AC-3 + MRV + Forward Checking",
        select_mrv_forward_checking,
        variables,
        neighbors,
        domains_ac3,
        givens,
        True,
    )
    results[name] = result

    return results, neighbors, domains_ac3


def main():
    labels = [
        "Backtracking",
        "Backtracking + MRV",
        "Backtracking + MRV + Forward Checking",
        "AC-3 + MRV + Forward Checking",
    ]
    results, _, _ = solve_all_methods()
    first_solution = results[labels[0]]["solution"]
    print("6x6 Sudoku CSP")
    print()
    print("Initial puzzle:")
    print_grid(INITIAL_GRID)
    print()
    print("Generated nodes:")
    for label in labels:
        solved = "yes" if results[label]["solution"] else "no"
        print(f"{label:<38} {results[label]['nodes']:>4} nodes  solved: {solved}")

    print()
    print("Final solution:")
    print_grid(assignment_to_grid(first_solution))
    print()


if __name__ == "__main__":
    main()
