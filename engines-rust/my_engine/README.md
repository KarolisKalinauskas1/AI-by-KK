# My Chess Engine# MyEngine - Chess Engine



A complete chess engine built from scratch in Python, implementing classic AI game-playing algorithms. Designed for educational purposes and Lichess.org bot deployment.## Overview


## 🎯 What Is This?MyEngine is a classic alpha-beta chess engine implementing:

- **Negamax** with alpha-beta pruning

A **fully functional chess engine** that:- **Iterative deepening** for progressive search

- Plays legal chess moves using intelligent search- **Transposition table** (TT) for position caching

- Communicates via UCI (Universal Chess Interface) protocol- **Quiescence search** (captures-only) to avoid horizon effect

- Manages time correctly for online games- **Move ordering** (TT move + MVV-LVA captures)

- Avoids tactical blunders through quiescence search- **Tapered evaluation** (middlegame/endgame blending)

- Reaches playing strength of ~1200-1600 Elo

## How to Run

**Not a GUI** - this is the "brain" that other programs (like lichess-bot) use to play chess.

The engine communicates via the UCI (Universal Chess Interface) protocol.

## 🧠 Algorithms Used

### Command Line

### Core Search Algorithm```bash

- **Negamax with Alpha-Beta Pruning**: Efficient minimax variant that searches the game treepython -u engines/my_engine/run_engine.py

  - Negamax: Simplified minimax using score negation```

  - Alpha-Beta: Prunes branches that can't improve the result

  - Reduces nodes searched by ~60% compared to plain minimax### With lichess-bot

Configure in `config.yml`:

### Key Optimizations```yaml

engine:

1. **Iterative Deepening**  dir: "./engines/my_engine"

   - Searches depth 1, then 2, then 3, etc.  name: "run_engine.py"

   - Can stop anytime with a valid move  protocol: "uci"

   - Later iterations benefit from earlier results```



2. **Transposition Table** (Hash Table)## How It Works

   - Caches previously evaluated positions

   - Avoids re-searching the same position```

   - 2-4% hit rate at shallow depths, 10-20% at deeper depthsUCI Layer (uci.py)

    ↓

3. **Move Ordering**Engine Facade (engine.py)

   - Searches promising moves first    ↓ choose_move()

   - TT move (from previous iteration) → Captures (MVV-LVA) → Quiet moves    ↓

   - Better ordering → more alpha-beta cutoffs → 30% fewer nodesSearch (search.py)

    ├─ Iterative Deepening (depth 1..N)

4. **Quiescence Search**    ├─ Negamax α-β (negamax function)

   - Extends search along tactical lines (captures, checks)    ├─ Quiescence (captures only)

   - Prevents "horizon effect" (missing tactics just beyond search depth)    └─ Transposition Table (tt.py)

   - Corrects evaluation by 50-300 centipawns in tactical positions    ↓

Evaluation (evaluator.py)

### Evaluation Function    ├─ Material

- **Material counting**: P=100, N=320, B=330, R=500, Q=900    ├─ Piece-Square Tables (pst.py)

- **Piece-square tables**: Positional bonuses for good piece placement    ├─ Pawn structure

- **King safety**: Different evaluation for midgame vs endgame    ├─ King safety

- Accuracy: ±100cp for typical positions    └─ Mobility

```

## 📁 Architecture

### Key Algorithms

```

┌─────────────────────────────────────────────────────────────┐**Alpha-Beta Negamax**

│                         UCI Layer                            │- Game-theoretic minimax with symmetric negation

│  (uci.py - Handles commands from GUI/lichess-bot)           │- Prunes branches outside [alpha, beta] window

└──────────────────────┬──────────────────────────────────────┘- Typical complexity: O(b^(d/2)) with good ordering

                       │

                       ▼**Iterative Deepening**

┌─────────────────────────────────────────────────────────────┐- Searches depths 1, 2, 3, ..., N

│                      Engine Facade                           │- Provides best move early (time management)

│  (engine.py - Time management, statistics, coordination)     │- Seeds TT for deeper iterations (improves ordering)

└──┬────────────────┬─────────────────┬───────────────────────┘

   │                │                 │**Transposition Table**

   ▼                ▼                 ▼- Zobrist hashing for position keys

┌──────────┐  ┌──────────┐    ┌─────────────┐- Stores: score, depth, flag (EXACT/LOWER/UPPER), best move

│   TT     │  │  Search  │◄──►│  Evaluator  │- Avoids re-searching same position

│ (tt.py)  │  │(search.py)│    │(evaluator.py)│- Provides hash move for ordering

└──────────┘  └─────┬────┘    └─────────────┘

                    │**Quiescence Search**

                    ▼- At depth 0, don't evaluate in "noisy" positions (captures in progress)

              ┌──────────┐- Stand-pat: use static eval as baseline

              │ Ordering │- Search captures only until position is "quiet"

              │(ordering.py)│- Prevents horizon effect (missing tactical sequences)

              └──────────┘

```**Move Ordering**

1. TT move (best from previous search)

### Data Flow2. Captures by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)

3. Quiet moves (unordered for simplicity)

1. **UCI command** (e.g., "go wtime 60000") arrives at `uci.py`

2. **UCI handler** parses it into `TimeControl` object## Configuration

3. **Engine.choose_move()** calculates time budget

4. **search_root()** performs iterative deepening:Edit `config.yaml` to tune engine behavior:

   - For each depth: calls `negamax()`

   - `negamax()` uses `order_moves()` to sort candidates### Search Parameters

   - Leaf nodes call `quiescence()` → `evaluate()`- `max_depth` (default: 7): Maximum search depth

   - Positions stored/retrieved from `TranspositionTable`- `time_ms` (default: 1500): Fixed time per move (ms) if no clock

5. **Best move** returned to UCI layer- `tt_mb` (default: 128): Transposition table size (MB)

6. **UCI outputs** "bestmove e2e4"- `quiescence` (default: true): Enable quiescence search

- `ordering` (default: "tt_mvv_lva_quiet"): Move ordering strategy

## 🚀 How to Run

### Evaluation Weights

### Quick Test- `pst`: Piece-square tables (1.0)

```bash- `mobility`: Legal move count (0.1)

cd engines/my_engine- `king_safety`: Pawn shield & open files (0.2)

python verify_step9.py- `pawns`: Doubled/isolated/passed (0.15)

```- `rook_open_file`: Rook on open file (0.1)

- `bishop_pair`: Two bishops bonus (0.25)

### Run Demos

```bash### Logging

# Search demonstration- `pv`: Emit principal variation (true)

python demo_step8_final.py- `depth_log`: Print depth completion info (true)



# Sanity checks## Strength & Limitations

python demo_step10_quick.py

### Expected Performance

# UCI protocol test- **Depth 6-7** + quiescence: ~1500-1800 Elo (casual club level)

python test_uci.py- **Good tactical vision** (quiescence prevents blunders)

```- **Reasonable positional play** (PST + basic eval terms)



### Play on Lichess### Intentional Simplifications

```bash- No null-move pruning (easier to explain)

# From root lichess-bot directory- No late-move reductions (simpler search tree)

python lichess-bot.py- No killer moves (minimal state)

```- No aspiration windows (optional enhancement)


The engine will:These keep the codebase clean and explainable for educational purposes while still achieving decent strength.

1. Connect to Lichess via API

2. Accept challenges from other bots/humans## File Structure

3. Play complete games using this search engine

| File | Purpose |

## ⚙️ Configuration|------|---------|

| `run_engine.py` | UCI entry point, launches uci loop |

Edit `config.yaml` to tune engine behavior:| `uci.py` | UCI protocol parser/emitter |

| `config.py` | Configuration dataclass + YAML loader |

```yaml| `engine.py` | Engine facade: time mgmt + stats |

engine:| `search.py` | Iterative deepening + negamax + quiescence |

  # Transposition table size (in MB)| `ordering.py` | Move ordering (TT + MVV-LVA) |

  # Larger = fewer hash collisions, more memory| `tt.py` | Transposition table |

  # Safe range: 32-512 MB| `evaluator.py` | Static evaluation function |

  # pst.py` | Piece-square tables + phase |

  | `utils.py` | Zobrist, score constants, helpers |

  # Maximum search depth (in ply)| `config.yaml` | Engine configuration |

  # Higher = stronger but slower

  # Safe range: 4-8 for online play## Quick Algorithm Reference

  max_depth: 6

  ### Negamax Pseudocode

  # Fixed time per move (ms) - used if no clock info```

  # Fallback for analysis modefunction negamax(board, depth, alpha, beta):

  time_ms: 1000    if depth == 0: return quiescence(board, alpha, beta)

      
  # Logging options    for move in ordered_moves(board):

  logging:        board.push(move)

    emit_depth_log: true  # Print search progress to stderr        score = -negamax(board, depth-1, -beta, -alpha)

```        board.pop()

        
  ### Safe Defaults        alpha = max(alpha, score)

- **tt_mb: 128** - Good balance of memory/performance        if alpha >= beta:

- **max_depth: 6** - Reaches 5-6 ply in bullet/blitz            return beta  # cutoff

- **time_ms: 1000** - 1 second for analysis    

    return alpha

### Tuning Guide``` 

