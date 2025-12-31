"""
Transposition Table

Purpose: Cache search results by position to avoid redundant work.

Zobrist Hashing (implemented in utils.py):
- Each (piece, square) gets random 64-bit number
- Hash = XOR of all pieces + side-to-move + castling + en passant
- Collision probability is negligible for reasonable table sizes
- Deterministic: same position always gets same hash

Entry Types (Bound Flags):
- EXACT (0): Exact score from full search within [alpha, beta]
- LOWER (1): Fail-high (beta cutoff) - actual score >= stored score
- UPPER (2): Fail-low (no alpha improvement) - actual score <= stored score

Why these flags matter:
- EXACT: Can return score directly if depth sufficient
- LOWER: Can raise alpha (we know score is at least this good)
- UPPER: Can lower beta (we know score is at most this good)
- Proper flag handling is critical for alpha-beta correctness

Replacement Policy Options:
1. Always replace: Simple, fast, works reasonably well
2. Depth-preferred: Keep entries from deeper searches (more valuable)
3. Two-tier: Separate always-replace and depth-preferred slots

Implementation uses depth-preferred: only replace if new depth >= old depth.
This preserves expensive deep searches while still updating recent positions.

Memory Budget:
- tt_mb determines table size in megabytes
- Power-of-two sizing for fast modulo via bitwise AND
- Each entry ~40-50 bytes (depth, score, flag, best_move, age)

Performance Impact:
- Good TT can reduce nodes searched by 10-100x
- Critical for iterative deepening (seeding hash moves)
- Enables aspiration windows (fail-soft scores)
"""

from typing import NamedTuple, Optional
import chess

# TT entry bound flags
# These encode what we know about the score relative to the search window
EXACT = 0  # Score is exact (PV node, within alpha-beta window)
LOWER = 1  # Score is lower bound (fail-high, score >= beta)
UPPER = 2  # Score is upper bound (fail-low, score <= alpha)


class TTEntry(NamedTuple):
    """
    Transposition table entry.
    
    Attributes:
        depth: Search depth when this entry was stored (higher = more reliable)
        score: Score in centipawns (or mate score)
        flag: Bound type (EXACT, LOWER, or UPPER)
        best_move: Best move found at this position (for move ordering)
        age: Search generation (for aging old entries)
    
    Usage in search:
    - If flag == EXACT and depth >= current_depth: return score
    - If flag == LOWER: alpha = max(alpha, score)  # fail-high cutoff
    - If flag == UPPER: beta = min(beta, score)    # fail-low cutoff
    - best_move used as first move in ordering (hash move)
    
    Memory: ~40 bytes per entry
    - depth: 4 bytes (int)
    - score: 4 bytes (int)
    - flag: 4 bytes (int)
    - best_move: ~20 bytes (chess.Move object reference)
    - age: 4 bytes (int)
    - NamedTuple overhead: ~8 bytes
    """
    depth: int
    score: int
    flag: int
    best_move: Optional[chess.Move]
    age: int = 0


class TranspositionTable:
    """
    Transposition table for caching search results.
    
    Uses Zobrist hashing (from utils.zobrist) for position keys.
    Implements depth-preferred replacement policy.
    
    Key Operations:
    - probe(key): Look up cached position
    - store(key, entry): Save search result
    - clear(): Reset table (for new game)
    
    Performance Characteristics:
    - O(1) lookup and insertion (hash table)
    - Collision handling: overwrite with depth preference
    - Memory: size_mb * 1024 * 1024 bytes
    
    Thread Safety: Not thread-safe (single-threaded engine)
    """
    
    def __init__(self, size_mb: int):
        """
        Initialize transposition table.
        
        Args:
            size_mb: Table size in megabytes
        
        Implementation:
        - Allocates power-of-2 slots for fast indexing (key & mask)
        - Uses dict for storage (Python dict is highly optimized)
        - Could use array for slightly better cache locality
        
        Size Calculation:
        - Each entry ≈ 40 bytes
        - 128MB ≈ 3.2M entries
        - Typical collision rate: <1% with good Zobrist
        """
        # Calculate number of entries
        bytes_available = size_mb * 1024 * 1024
        entry_size = 40  # Approximate size of TTEntry
        num_entries = bytes_available // entry_size
        
        # Round down to power of 2 for fast modulo via bitwise AND
        # This allows: index = hash & mask instead of hash % size
        if num_entries > 0:
            self.size = 1 << (num_entries.bit_length() - 1)
        else:
            self.size = 1024  # Minimum size
        
        self.mask = self.size - 1
        
        # Storage: dict[index -> entry]
        # Key is (hash & mask), not full hash, to save memory
        self.table: dict[int, TTEntry] = {}
        
        # Statistics (for debugging and tuning)
        self.hits = 0
        self.misses = 0
        self.collisions = 0
        self.stores = 0
        
        # Generation counter for aging entries
        self.generation = 0
    
    def probe(self, key: int) -> Optional[TTEntry]:
        """
        Look up position in table.
        
        Args:
            key: Zobrist hash of position (from utils.zobrist)
        
        Returns:
            TTEntry if found and valid, None otherwise
        
        Note: Does NOT verify position equality (assumes Zobrist collisions rare).
        In production, could store partial key for verification.
        """
        idx = key & self.mask
        entry = self.table.get(idx)
        
        if entry is not None:
            self.hits += 1
            return entry
        else:
            self.misses += 1
            return None
    
    def store(self, key: int, entry: TTEntry) -> None:
        """
        Store position in table.
        
        Args:
            key: Zobrist hash of position
            entry: Entry to store
        
        Replacement Policy (depth-preferred):
        - Always replace if slot empty
        - Replace if new depth >= old depth (prefer deep searches)
        - Replace if entry is old (generation-based aging)
        
        Rationale:
        - Deep searches are expensive, preserve them
        - Recent searches more relevant than old ones
        - PV nodes (EXACT) slightly preferred over cut nodes
        """
        idx = key & self.mask
        existing = self.table.get(idx)
        
        # Decide whether to replace
        should_replace = False
        
        if existing is None:
            # Empty slot: always store
            should_replace = True
        elif entry.age > existing.age:
            # Newer generation: prefer recent searches
            should_replace = True
        elif entry.age == existing.age and entry.depth >= existing.depth:
            # Same generation, deeper or equal depth: replace
            should_replace = True
        elif existing.age < self.generation - 2:
            # Entry is very old (2+ generations): replace
            should_replace = True
        
        if should_replace:
            self.table[idx] = entry
            self.stores += 1
            if existing is not None:
                self.collisions += 1
    
    def clear(self):
        """
        Clear the table (for new game).
        
        Also resets statistics and increments generation.
        """
        self.table.clear()
        self.generation += 1
        
        # Reset stats
        self.hits = 0
        self.misses = 0
        self.collisions = 0
        self.stores = 0
    
    def new_search(self):
        """
        Increment generation counter for new search.
        
        Called at start of each search to mark entries as older.
        Does NOT clear table (preserves cached positions).
        """
        self.generation += 1
    
    def usage(self) -> float:
        """
        Calculate table usage percentage.
        
        Returns:
            Percentage of slots filled (0.0 to 100.0)
        """
        if self.size == 0:
            return 0.0
        return (len(self.table) / self.size) * 100.0
    
    def stats(self) -> dict:
        """
        Get statistics for debugging.
        
        Returns:
            Dict with hits, misses, hit rate, usage, etc.
        """
        total_probes = self.hits + self.misses
        hit_rate = (self.hits / total_probes * 100.0) if total_probes > 0 else 0.0
        
        return {
            "size": self.size,
            "entries": len(self.table),
            "usage_pct": self.usage(),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": hit_rate,
            "stores": self.stores,
            "collisions": self.collisions,
            "generation": self.generation
        }
