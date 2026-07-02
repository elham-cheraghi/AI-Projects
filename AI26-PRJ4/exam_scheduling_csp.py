from pathlib import Path

courses: list[str] = [
    "AI",
    "Database",
    "Operating Systems",
    "Networks",
    "Compiler",
    "Algorithms",
]
time_slots: list[str] = ["T_1", "T_2", "T_3", "T_4"]

# Binary not-equal constraints
constraints: list[tuple[str, str]] = [
    ("AI", "Database"),
    ("AI", "Algorithms"),
    ("Database", "Operating Systems"),
    ("Database", "Networks"),
    ("Operating Systems", "Networks"),
    ("Networks", "Compiler"),
    ("Compiler", "Algorithms"),
]

adjacency: dict[str, list[str]] = {course: [] for course in courses}
for c1, c2 in constraints:
    adjacency[c1].append(c2)
    adjacency[c2].append(c1)


def is_consistent(assignment: dict[str, str], variable: str, value: str) -> bool:
    for neighbor in adjacency[variable]:
        if neighbor in assignment and assignment[neighbor] == value:
            return False
    return True


def get_legal_values(assignment: dict[str, str], variable: str) -> list[str]:
    return [v for v in time_slots if is_consistent(assignment, variable, v)]


# Variable Selection Strategies
def select_variable_static(assignment: dict[str, str]) -> str | None:
    for course in courses:
        if course not in assignment:
            return course
    return None


def select_variable_mrv(assignment: dict[str, str]) -> str | None:
    unassigned = [c for c in courses if c not in assignment]
    if not unassigned:
        return None
    return min(
        unassigned,
        key=lambda var: (len(get_legal_values(assignment, var)), courses.index(var)),
    )


def select_variable_mrv_degree(assignment: dict[str, str]) -> str | None:
    unassigned = [c for c in courses if c not in assignment]
    if not unassigned:
        return None

    min_remaining = min(len(get_legal_values(assignment, var)) for var in unassigned)
    mrv_candidates = [
        var
        for var in unassigned
        if len(get_legal_values(assignment, var)) == min_remaining
    ]
    if len(mrv_candidates) == 1:
        return mrv_candidates[0]

    def degree(var: str) -> int:
        return sum(1 for nb in adjacency[var] if nb not in assignment)

    max_degree = max(degree(var) for var in mrv_candidates)
    degree_candidates = [var for var in mrv_candidates if degree(var) == max_degree]
    if len(degree_candidates) == 1:
        return degree_candidates[0]

    return min(degree_candidates, key=lambda var: courses.index(var))


def backtracking_solver(
    selection_strategy,
    find_all: bool = True,
) -> tuple[list[dict[str, str]], int]:
    solutions: list[dict[str, str]] = []
    node_count = [1]

    def backtrack(assignment: dict[str, str]) -> bool:
        if len(assignment) == len(courses):
            solutions.append(dict(assignment))
            return not find_all

        variable = selection_strategy(assignment)

        for value in time_slots:
            node_count[0] += 1

            if is_consistent(assignment, variable, value):
                assignment[variable] = value
                stop = backtrack(assignment)
                del assignment[variable]
                if stop:
                    return True

        return False

    backtrack({})
    return solutions, node_count[0]


def validate_solution(solution: dict[str, str]) -> bool:
    """Return True iff solution is complete and satisfies all conflict constraints."""
    if set(solution.keys()) != set(courses):
        return False
    for c1, c2 in constraints:
        if solution.get(c1) == solution.get(c2):
            return False
    return True


def _sort_key(solution: dict[str, str]) -> tuple[str, ...]:
    """Canonical tuple for set comparison / dedup checks."""
    return tuple(solution[c] for c in courses)


def print_schedule(solution: dict[str, str], indent: int = 4) -> None:
    pad = " " * indent
    for course in courses:
        print(f"{pad}{course:<26} →  {solution[course]}")


def format_schedule(solution: dict[str, str], indent: int = 4) -> str:
    pad = " " * indent
    return "\n".join(f"{pad}{course:<26} ->  {solution[course]}" for course in courses)


def count_t4(solution: dict[str, str]) -> int:
    return sum(1 for v in solution.values() if v == "T_4")


def _write_solutions_file(
    solutions: list[dict[str, str]],
    node_count: int,
    output_path: Path,
) -> None:
    best_t4_count = min(count_t4(solution) for solution in solutions)
    best_solutions = [
        solution for solution in solutions if count_t4(solution) == best_t4_count
    ]

    with output_path.open("w", encoding="utf-8") as file:
        file.write("Exam Scheduling CSP - All Valid Solutions\n")
        file.write("=" * 50 + "\n\n")
        file.write(f"Courses: {courses}\n")
        file.write(f"Time slots: {time_slots}\n")
        file.write("Conflict constraints:\n")
        for c1, c2 in constraints:
            file.write(f"  {c1} != {c2}\n")

        file.write("\n")
        file.write(f"Generated nodes for full enumeration: {node_count}\n")
        file.write(f"Total valid schedules: {len(solutions)}\n")
        file.write(f"Minimum number of T_4 exams: {best_t4_count}\n")
        file.write(f"Best schedules with this minimum: {len(best_solutions)}\n")

        file.write("\nAll valid schedules\n")
        file.write("-" * 50 + "\n")
        for index, solution in enumerate(solutions, start=1):
            file.write(f"\nSchedule {index}\n")
            file.write(format_schedule(solution))
            file.write("\n")

        file.write("\nBest schedules (minimum T_4 exams)\n")
        file.write("-" * 50 + "\n")
        for index, solution in enumerate(best_solutions, start=1):
            file.write(f"\nBest Schedule {index} (T_4 count = {best_t4_count})\n")
            file.write(format_schedule(solution))
            file.write("\n")


def main() -> None:
    SEP = "═" * 66
    strategies = [
        ("Simple Backtracking", select_variable_static),
        ("Backtracking + MRV", select_variable_mrv),
        ("Backtracking + MRV + Degree", select_variable_mrv_degree),
    ]

    print(SEP)
    print("1. FIRST VALID ANSWER")
    print(SEP)
    for label, strategy in strategies:
        first_solutions, first_nodes = backtracking_solver(strategy, find_all=False)
        if not first_solutions:
            print(f"\n{label}: no valid schedule found.")
            continue
        print()
        print(label)
        print(f"  Generated nodes: {first_nodes}")
        print("  First schedule:")
        print_schedule(first_solutions[0])

    all_solutions, all_nodes = backtracking_solver(
        select_variable_static, find_all=True
    )
    all_solutions = sorted(all_solutions, key=_sort_key)
    for solution in all_solutions:
        assert validate_solution(solution), f"Invalid schedule: {solution}"

    output_path = Path(__file__).with_name("exam_scheduling_solutions.txt")
    _write_solutions_file(all_solutions, all_nodes, output_path)

    print()
    print(SEP)
    print("2. ALL SOLUTIONS")
    print(SEP)
    print(f"  Wrote {len(all_solutions)} valid schedules to {output_path.name}.")

    print()
    print(SEP)
    print("3. BEST SCHEDULE — MINIMISING T_4 EXAMS")
    print(SEP)
    min_t4 = min(count_t4(s) for s in all_solutions)
    best_solutions = [s for s in all_solutions if count_t4(s) == min_t4]
    best_solution = best_solutions[0]

    print(f"  Minimum T_4 exams          : {min_t4}")
    print(f"  Schedules achieving minimum: {len(best_solutions)}")
    print("  One best schedule:")
    print_schedule(best_solution)


if __name__ == "__main__":
    main()
