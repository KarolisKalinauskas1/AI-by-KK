"""
Engine Facade

Main engine interface that UCI layer communicates with.
Handles time management, statistics tracking, and move selection.

Time Management:
- Clock-based: Allocate ~60% of remaining time / expected moves + 80% increment
- Safety overhead: Reserve 250-400ms to prevent time forfeits
- Fixed time: Use config.time_ms if clocks not provided

StopToken:
- Checked during search to respect time limits
- Set by 'stop' command or time expiration
- Guarantees clean termination without timeout

Why 60% allocation:
- Conservative to avoid time pressure
- Leaves buffer for complex positions
- Increment provides recovery time

Why safety overhead:
- Network latency in online play
- OS scheduling delays
- Guarantees we don't flag even with variance
"""

import sys
import chess
from dataclasses import dataclass
from typing import Optional

import tt
import config as cfg
import utils
import search


@dataclass
class TimeControl:
    """Time control information from 'go' command."""
    wtime: Optional[int] = None  # white time in ms
    btime: Optional[int] = None  # black time in ms
    winc: Optional[int] = None   # white increment in ms
    binc: Optional[int] = None   # black increment in ms
    movestogo: Optional[int] = None  # moves to next time control


@dataclass
class Stats:
    """
    Search statistics for debugging and info output.
    
    Attributes:
        nodes: Regular search nodes
        qnodes: Quiescence search nodes
        tt_hits: Transposition table hits
        depth: Current search depth
        start_time_ms: Search start time in milliseconds
    """
    nodes: int = 0
    qnodes: int = 0
    tt_hits: int = 0
    depth: int = 0
    start_time_ms: int = 0


class StopToken:
    """
    Thread-safe flag to signal search termination.
    Checked frequently during search to respect time limits.
    """
    
    def __init__(self):
        self._stopped = False
    
    def is_set(self) -> bool:
        """Check if stop has been requested."""
        return self._stopped
    
    def set(self):
        """Request search to stop."""
        self._stopped = True
    
    def reset(self):
        """Clear stop flag for new search."""
        self._stopped = False


class Engine:
    """
    Main engine class.
    
    Responsibilities:
    - Time budget calculation
    - Search coordination
    - Statistics tracking
    - UCI info output
    
    The engine is the main facade between UCI layer and search algorithms.
    It owns the transposition table, manages time budgets, and tracks statistics.
    """
    
    def __init__(self, cfg: cfg.EngineConfig):
        """
        Initialize engine with configuration.
        
        Args:
            cfg: Engine configuration from config.yaml
        
        Initializes:
        - Transposition table (sized by cfg.tt_mb)
        - Stop token (for search cancellation)
        - Statistics (reset before each search)
        """
        self.cfg = cfg
        self.tt = tt.TranspositionTable(cfg.tt_mb)
        self.stop_token = StopToken()
        self.stats = Stats()
        
        # Time management state
        self._budget_ms: Optional[int] = None
        self._hard_limit_ms: int = 0
    
    def choose_move(self, board: chess.Board, tc: TimeControl) -> chess.Move:
        """
        Select best move for current position.
        
        Args:
            board: Current chess position
            tc: Time control information
        
        Returns:
            Best move found
        
        Time Management Strategy:
        - If clocks provided: budget = 0.6 * (remaining / expected_moves) + 0.8 * increment - overhead
        - Expected moves heuristic: 40 moves (conservative for midgame)
        - Safety overhead: 300ms to prevent flagging
        - Hard limit: 90% of budget (leave some margin)
        - Else: use fixed time from config
        
        Stop Token:
        - Set when time expires
        - Checked during search to exit gracefully
        - Prevents time forfeit
        """
        # Reset state for new search
        self.stop_token.reset()
        self.stats = Stats()
        self.stats.start_time_ms = utils.now_ms()
        
        # Increment TT generation for aging
        self.tt.new_search()
        
        # Calculate time budget and limits
        self._budget_ms = self._calculate_budget(board, tc)
        
        # Set hard limit (90% of budget to ensure we finish in time)
        if self._budget_ms:
            self._hard_limit_ms = int(self._budget_ms * 0.9)
        else:
            self._hard_limit_ms = 0
        
        # Log search start
        if self.cfg.logging.get("emit_depth_log", True):
            if self._budget_ms:
                print(f"# Time budget: {self._budget_ms}ms (hard limit: {self._hard_limit_ms}ms)", file=sys.stderr)
                print(f"# Clock: W={tc.wtime}ms B={tc.btime}ms, Inc: W={tc.winc}ms B={tc.binc}ms", file=sys.stderr)
            else:
                print(f"# Depth-only search to depth {self.cfg.max_depth}", file=sys.stderr)
            sys.stderr.flush()
        
        # Run the actual search!
        score, best_move = search.search_root(board, self)
        
        # Fallback if search returns None (shouldn't happen, but safety check)
        if best_move is None:
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                raise ValueError("No legal moves available")
            best_move = legal_moves[0]  # Just take first legal move
        
        # Log search completion
        if self.cfg.logging.get("emit_depth_log", True):
            elapsed = utils.elapsed_ms(self.stats.start_time_ms)
            nps_value = utils.nps(self.stats.nodes, elapsed) if elapsed > 0 else 0
            print(f"# Search completed: {elapsed}ms, {self.stats.nodes} nodes, {nps_value} nps", file=sys.stderr)
            if self._budget_ms:
                usage_pct = (elapsed / self._budget_ms * 100) if self._budget_ms > 0 else 0
                print(f"# Budget usage: {usage_pct:.1f}%", file=sys.stderr)
            sys.stderr.flush()
        
        return best_move
    
    def _calculate_budget(self, board: chess.Board, tc: TimeControl) -> Optional[int]:
        """
        Calculate time budget for this move.
        
        Args:
            board: Current position (to determine side to move)
            tc: Time control
        
        Returns:
            Time budget in milliseconds, or None for depth-only search
        
        Heuristic (clock-based):
        - Base allocation: 60% of remaining time / expected moves
        - Increment bonus: 80% of increment (save 20% for time pressure)
        - Safety overhead: 300ms reserved for network/OS delays
        - Minimum budget: 100ms (always try to think a bit)
        
        Why 60%:
        - Conservative to build time bank
        - Allows thinking longer in critical positions later
        - Accounts for variance in position complexity
        
        Why 40 moves:
        - Chess games typically last 40-80 moves
        - Assumes we're in early/mid game
        - Better to have time left than run out
        
        Why 300ms overhead:
        - Network latency in online play (50-150ms)
        - OS scheduling delays (50-100ms)
        - Search cleanup time (50-100ms)
        - Total safety margin: 300ms
        """
        if tc.wtime is not None and tc.btime is not None:
            # Determine our time and increment based on side to move
            if board.turn == chess.WHITE:
                our_time = tc.wtime
                our_inc = tc.winc or 0
            else:
                our_time = tc.btime
                our_inc = tc.binc or 0
            
            # Expected moves remaining
            # Use movestogo if provided (classical time control)
            # Otherwise assume 40 moves (typical game length / 2)
            if tc.movestogo and tc.movestogo > 0:
                expected_moves = tc.movestogo
            else:
                # Estimate based on move count (if we could track it)
                # For now, use conservative 40
                expected_moves = 40
            
            # Calculate base budget from remaining time
            time_per_move = our_time / expected_moves
            base_budget = 0.6 * time_per_move
            
            # Add increment bonus (save 20% for emergencies)
            inc_budget = 0.8 * our_inc
            
            # Safety overhead (network + OS + cleanup)
            safety_overhead = 300
            
            # Total budget
            budget = base_budget + inc_budget - safety_overhead
            
            # Ensure minimum viable budget
            # Even in severe time pressure, try to think at least 100ms
            budget = max(100, int(budget))
            
            # Cap at remaining time minus overhead (don't overshoot)
            max_safe_time = our_time - safety_overhead
            if max_safe_time > 0:
                budget = min(budget, max_safe_time)
            
            return budget
        
        # Fall back to fixed time from config
        # Used when no clock info provided (e.g., position analysis)
        return self.cfg.time_ms
    
    def emit_info(self, depth: int, score: int, pv: list[chess.Move]):
        """
        Output UCI info line with search statistics.
        
        Args:
            depth: Current search depth
            score: Score in centipawns (or mate score)
            pv: Principal variation (best line)
        
        Format: info depth D nodes N nps X score cp S pv move1 move2 ...
        
        Note: Uses utils.elapsed_ms for consistent timing.
        """
        if not self.cfg.logging.get("emit_pv", True):
            return
        
        elapsed = utils.elapsed_ms(self.stats.start_time_ms)
        elapsed = max(1, elapsed)  # Avoid division by zero
        
        nps_value = utils.nps(self.stats.nodes, elapsed)
        
        pv_str = " ".join(m.uci() for m in pv) if pv else ""
        
        # Format score (handle mate scores)
        if abs(score) >= utils.MATE - 1000:
            # Mate score: convert to mate distance
            if score > 0:
                mate_ply = utils.MATE - score
                mate_moves = (mate_ply + 1) // 2
                score_str = f"mate {mate_moves}"
            else:
                mate_ply = utils.MATE + score
                mate_moves = (mate_ply + 1) // 2
                score_str = f"mate -{mate_moves}"
        else:
            score_str = f"cp {score}"
        
        # Build info string
        info = f"info depth {depth} nodes {self.stats.nodes} nps {nps_value} score {score_str}"
        if pv_str:
            info += f" pv {pv_str}"
        
        print(info)
        sys.stdout.flush()
    
    def should_stop(self) -> bool:
        """
        Check if search should stop.
        
        Returns:
            True if search should terminate
        
        Reasons to stop:
        - Stop token set (from 'stop' command)
        - Hard time limit exceeded
        """
        # Check explicit stop command
        if self.stop_token.is_set():
            return True
        
        # Check time limit
        if self._hard_limit_ms > 0:
            elapsed = utils.elapsed_ms(self.stats.start_time_ms)
            if elapsed >= self._hard_limit_ms:
                return True
        
        return False
