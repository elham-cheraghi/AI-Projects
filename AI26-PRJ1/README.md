# Search in a Grid World

<sub>Project 1 · Uninformed and informed search</sub>

<p align="center">
  <a href="media/demo.mp4"><img src="media/demo.webp" alt="BFS and A* solving the same map: Arya collects dragonglass, picks up the dagger and defeats the Night King" width="100%"></a>
</p>
<p align="center"><sub>BFS, then A*, on <code>medium-weapon</code> · click for the full-quality video</sub></p>

Arya has to collect every piece of dragonglass on a snowy grid while the Night King walks a fixed patrol loop. Ice is slow to cross, crates block the way, and on some maps a dagger lets her remove the Night King altogether.

The world is fully observable, deterministic and discrete. The other agent moves on a known schedule, so each algorithm plans the whole route up front and the game then plays it back.

## How it works

**State.** Arya's position, the remaining targets, the Night King's phase in his patrol cycle, whether Arya holds the dagger, and whether the Night King is still alive. Two states are equal only when all five match. That keeps duplicate detection correct even though the enemy never stops moving.

**Costs and score.**

| Event | Effect |
| :-- | :-- |
| Step onto snow | cost 5 |
| Step onto ice | cost 100 |
| Meet the Night King without the dagger | cost 10,000; these states are pruned from the search |
| Collect every target | +200 per target |
| Defeat the Night King with the dagger | +500 |

Final score = rewards − total path cost.

**Algorithms** (in [`search/`](search))

| Algorithm | File | What it optimizes |
| :-- | :-- | :-- |
| Breadth-first search | `bfs.py` | Fewest moves; terrain cost is ignored |
| Depth-limited / iterative deepening | `dls.py` | Fewest moves via DFS; without a limit it deepens up to *rows × cols* |
| Uniform-cost search | `ucs.py` | Lowest total cost |
| A\* | `a_star.py` | Lowest total cost, guided by a heuristic |

**The A\* heuristic** is the largest of several lower bounds on the remaining cost, all built on terrain-aware Dijkstra distances that are cached between calls:

- the distance to the nearest target plus a minimum spanning tree over the remaining targets;
- the cheapest ordering of any three remaining targets;
- a weapon-aware variant that also considers detouring through the dagger first.

Ties on *f* are broken in favour of states that hold the dagger or are closer to it, then by smaller *h*.

## Results

Path cost and nodes expanded on the course maps, as recorded in the [report](report/main.pdf).

| Map | BFS | DLS / IDS | UCS | A\* |
| :-- | --: | --: | --: | --: |
| `easy-no-weapon` | 280 · 888 | 280 · 2,653 | 110 · 486 | **110 · 40** |
| `easy-weapon` | 270 · 651 | 270 · 1,586 | 90 · 417 | **90 · 18** |
| `medium-no-weapon` | 330 · 8,778 | 330 · 40,237 | 170 · 4,789 | **170 · 50** |
| `medium-weapon` | 225 · 65,069 | 225 · 291,863 | 130 · 40,067 | **130 · 26** |
| `medium` | timeout | timeout | 420 · 320,721 | **420 · 394** |
| `hard-no-weapon` | 680 · 7,050 | 680 · 53,054 | 325 · 9,282 | **325 · 211** |

<sub>Each cell is <i>path cost · nodes expanded</i>.</sub>

A\* returns the same optimal cost as UCS on every map while expanding a small fraction of the nodes. BFS and IDS find the shortest routes in moves, but those routes cross ice.

## Run it

```bash
cd AI26-PRJ1
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

`main.py` runs A\* on `medium-no-weapon`. To try another map or algorithm, change the call at the bottom:

```python
play("medium-weapon", a_star, delay=200)   # bfs, dls, ucs, a_star
```

Maps live in [`env/src/maps/`](env/src/maps): `easy`, `medium`, `hard` and `extra`, each with and without a weapon. Press <kbd>Esc</kbd> to stop the playback early. Path cost, score and nodes expanded are printed to the terminal.

## Project layout

```
AI26-PRJ1/
├── main.py              entry point
├── env/                 game environment
│   ├── domain.py        GameState, successors, costs
│   ├── game.py          runner and scoring
│   ├── rendering.py     pygame renderer
│   └── src/             maps and sprites
├── search/              bfs.py · dls.py · ucs.py · a_star.py
└── report/              write-up (Persian, PDF + LaTeX)
```

---

<sub>Part of [AI Projects](../README.md) · University of Isfahan · Artificial Intelligence, Spring 2026</sub>
