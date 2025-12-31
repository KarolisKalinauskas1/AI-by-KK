"""
Search Algorithms

Contains:
- search_root: Iterative deepening framework
- negamax: Alpha-beta pruning with transposition table
- quiescence: Captures-only search to avoid horizon effect

The search explores a game tree using:
1. Iterative deepening (gradually increase depth)
2. Alpha-beta pruning (skip obviously bad moves)
3. Transposition table (remember positions we've seen)
4. Move ordering (try good moves first)
5. Quiescence search (resolve tactical sequences)
"""

import chess
from typing import TYPE_CHECKING, Optional
import evaluator
import ordering
import utils
from utils import INF, MATE
import tt as tt_module

if TYPE_CHECKING:
    from engine import Engine

# Quiescence search limits
MAX_Q_DEPTH = 10  # Maximum quiescence depth to prevent infinite recursion
DELTA_MARGIN = 900  # Delta pruning margin (queen value)


def search_root(board: chess.Board, eng: 'Engine') -> tuple[int, Optional[chess.Move]]:
    """
    Root search with iterative deepening.
    
    Iterative deepening searches depth 1, then 2, then 3, etc.
    Benefits:
    - Can stop anytime and have a valid move
    - Earlier depths help order later depths (via TT)
    - Overhead is minimal (~20% extra nodes for huge benefits)
    
    Args:
        board: Position to search
        eng: Engine instance with config, TT, stop token
    
    Returns:
        (score, best_move) tuple
    
    Algorithm:
    1. Loop depth = 1, 2, 3, ... until max_depth or time limit
    2. For each depth: call negamax with full window [-INF, INF]
    3. Extract PV (principal variation) from TT
    4. Emit info to UCI (depth, score, nodes, pv)
    5. Check stop token between iterations
    """
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        # No legal moves (checkmate or stalemate)
        return (0, None)
    
    if len(legal_moves) == 1:
        # Only one legal move, return it immediately
        return (0, legal_moves[0])
    
    best_move = legal_moves[0]  # Fallback
    best_score = -INF
    
    # Iterative deepening loop
    for depth in range(1, eng.cfg.max_depth + 1):
        if eng.should_stop():
            break
        
        # New search iteration
        eng.tt.new_search()
        alpha = -INF
        beta = INF
        current_best_move = None
        current_best_score = -INF
        
        # Get TT move from previous iteration (if any)
        tt_entry = eng.tt.probe(utils.zobrist(board))
        tt_move = tt_entry.best_move if tt_entry else None
        
        # Order moves (TT move first)
        moves = ordering.order_moves(board, tt_move)
        
        # Search each move at root
        for move in moves:
            board.push(move)
            
            # Negamax from opponent's perspective
            score = -negamax(board, depth - 1, -beta, -alpha, eng)
            
            board.pop()
            
            # Update best move
            if score > current_best_score:
                current_best_score = score
                current_best_move = move
            
            # Update alpha
            if score > alpha:
                alpha = score
            
            # Check if we should stop
            if eng.should_stop():
                break
        
        # Check if search was interrupted
        if eng.should_stop() and depth > 1:
            # Use result from previous completed depth
            break
        
        # Update best move and score from this depth
        best_score = current_best_score
        best_move = current_best_move
        
        # Store in TT
        if current_best_move:
            zobrist_key = utils.zobrist(board)
            entry = tt_module.TTEntry(
                depth=depth,
                score=best_score,
                flag=tt_module.EXACT,
                best_move=current_best_move,
                age=eng.tt.generation
            )
            eng.tt.store(zobrist_key, entry)
        
        # Extract PV from TT
        pv = _extract_pv(board, eng, depth)
        
        # Emit UCI info
        eng.emit_info(depth, best_score, pv)
        
        # Check for mate
        if abs(best_score) > MATE - 100:
            # Found forced mate, no need to search deeper
            break
    
    return (best_score, best_move)


def _extract_pv(board: chess.Board, eng: 'Engine', max_depth: int) -> list[chess.Move]:
    """
    Extract principal variation from transposition table.
    
    Walk through TT following best moves until we hit a dead end.
    
    Args:
        board: Current position
        eng: Engine with TT
        max_depth: Maximum PV length
    
    Returns:
        List of moves in the principal variation
    """
    pv = []
    seen_positions = set()
    board_copy = board.copy()
    
    for _ in range(max_depth):
        zobrist_key = utils.zobrist(board_copy)
        
        # Avoid repetitions
        if zobrist_key in seen_positions:
            break
        seen_positions.add(zobrist_key)
        
        # Probe TT
        entry = eng.tt.probe(zobrist_key)
        if not entry or not entry.best_move:
            break
        
        # Check if move is legal
        if entry.best_move not in board_copy.legal_moves:
            break
        
        pv.append(entry.best_move)
        board_copy.push(entry.best_move)
    
    return pv


def negamax(board: chess.Board, depth: int, alpha: int, beta: int, eng: 'Engine', ply: int = 0) -> int:
    """
    Negamax search with alpha-beta pruning.
    
    Negamax is a variant of minimax where we negate scores instead of
    alternating between min/max. Simpler and equivalent.
    
    Alpha-beta pruning skips branches that can't affect the final result:
    - Alpha: best score we can guarantee (lower bound)
    - Beta: worst score opponent will allow (upper bound)
    - If score >= beta: position is too good, opponent won't allow it (cut)
    
    Args:
        board: Position to search
        depth: Remaining depth (0 = call quiescence)
        alpha: Lower bound (we can get at least this)
        beta: Upper bound (opponent won't allow better than this)
        eng: Engine instance
        ply: Distance from root (for mate scoring)
    
    Returns:
        Score in centipawns from side-to-move perspective
    
    Algorithm:
    1. Check stop token and terminal positions
    2. Probe TT (might have stored result from previous search)
    3. At depth 0: call quiescence search
    4. Generate and order moves
    5. For each move: recursively search with negated window
    6. Track best score and alpha
    7. Beta cutoff if alpha >= beta
    8. Store result in TT with appropriate flag
    """
    # Update node count
    eng.stats.nodes += 1
    
    # Check time limit periodically (every 1024 nodes)
    if eng.stats.nodes & 1023 == 0:
        if eng.should_stop():
            return 0
    
    # Check for draws
    if board.is_fifty_moves() or board.is_repetition(2):
        return 0
    
    # Check for terminal positions
    if board.is_checkmate():
        return -MATE + ply  # Prefer later mates when losing
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # TT probe
    zobrist_key = utils.zobrist(board)
    tt_entry = eng.tt.probe(zobrist_key)
    tt_move = None
    
    if tt_entry:
        tt_move = tt_entry.best_move
        
        # TT cutoff: use stored result if depth is sufficient
        if tt_entry.depth >= depth:
            score = tt_entry.score
            
            # Adjust mate scores for current ply
            if score >= MATE - 100:
                score -= ply
            elif score <= -MATE + 100:
                score += ply
            
            # Check if we can use this score
            if tt_entry.flag == tt_module.EXACT:
                return score
            elif tt_entry.flag == tt_module.LOWER and score >= beta:
                return score
            elif tt_entry.flag == tt_module.UPPER and score <= alpha:
                return score
    
    # Leaf node: call quiescence search
    if depth <= 0:
        return quiescence(board, alpha, beta, eng)
    
    # Move generation and ordering
    moves = ordering.order_moves(board, tt_move)
    
    if not moves:
        # No legal moves (shouldn't happen, caught above)
        return 0
    
    best_score = -INF
    best_move = None
    original_alpha = alpha
    
    # Search each move
    for move in moves:
        board.push(move)
        
        # Recursive negamax call
        score = -negamax(board, depth - 1, -beta, -alpha, eng, ply + 1)
        
        board.pop()
        
        # Update best score
        if score > best_score:
            best_score = score
            best_move = move
        
        # Update alpha (raise lower bound)
        if score > alpha:
            alpha = score
        
        # Beta cutoff (fail-high)
        if alpha >= beta:
            # This position is too good, opponent won't let us reach it
            break
    
    # Determine TT flag
    if best_score <= original_alpha:
        # All moves were too weak (fail-low)
        flag = tt_module.UPPER
    elif best_score >= beta:
        # Position was too good (fail-high)
        flag = tt_module.LOWER
    else:
        # Exact score within window
        flag = tt_module.EXACT
    
    # Adjust mate scores for storage
    store_score = best_score
    if best_score >= MATE - 100:
        store_score += ply
    elif best_score <= -MATE + 100:
        store_score -= ply
    
    # Store in TT
    entry = tt_module.TTEntry(
        depth=depth,
        score=store_score,
        flag=flag,
        best_move=best_move,
        age=eng.tt.generation
    )
    eng.tt.store(zobrist_key, entry)
    
    return best_score


def quiescence(board: chess.Board, alpha: int, beta: int, eng: 'Engine', q_depth: int = 0) -> int:
    """
    Quiescence search - captures only to avoid horizon effect.
    
    The horizon effect: At depth 0, we might think we're winning material,
    but opponent can recapture immediately. Quiescence extends search along
    forcing lines (captures, later checks) until position is "quiet".
    
    Algorithm:
    1. Stand-pat: Evaluate current position (option to stand still)
    2. Beta cutoff: If stand-pat >= beta, position is too good (fail-high)
    3. Alpha update: Raise alpha if stand-pat is better
    4. Delta pruning: Skip captures that can't possibly raise alpha
    5. Search captures: Try each capture and recurse
    
    Args:
        board: Position to search
        alpha: Lower bound (fail-low if score <= alpha)
        beta: Upper bound (fail-high if score >= beta)
        eng: Engine instance (for stats, config)
        q_depth: Current quiescence depth (for limiting recursion)
    
    Returns:
        Score in centipawns from side-to-move perspective
    
    Example:
        Position: White can capture Black's queen, but Black recaptures
        Without quiescence: +900 (won queen!)
        With quiescence: 0 (equal after recapture)
    """
    # Update stats
    eng.stats.nodes += 1
    
    # Limit quiescence depth to prevent runaway recursion
    if q_depth >= MAX_Q_DEPTH:
        return evaluator.evaluate(board)
    
    # Check time limit
    if eng.should_stop():
        return evaluator.evaluate(board)
    
    # Terminal position check
    if board.is_checkmate():
        # We're checkmated (very bad for side to move)
        return -30000 + q_depth  # Prefer later mates
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Stand-pat: Evaluate current position
    # This is the score if we "stand still" and don't capture anything
    stand_pat = evaluator.evaluate(board)
    
    # Flip score to side-to-move perspective
    # evaluator.evaluate() returns from white's perspective
    # We need it from current player's perspective
    if board.turn == chess.BLACK:
        stand_pat = -stand_pat
    
    # Beta cutoff: Position is already too good
    # Opponent won't let us reach this position (they'll choose a different move earlier)
    if stand_pat >= beta:
        return beta
    
    # Alpha update: Raise lower bound if stand-pat is better
    # We can always choose to stand still, so alpha is at least stand_pat
    if stand_pat > alpha:
        alpha = stand_pat
    
    # Delta pruning: Skip captures that can't possibly help
    # If even capturing a queen won't raise alpha, don't bother searching
    # This is a safe optimization (won't miss tactical wins)
    if stand_pat + DELTA_MARGIN < alpha:
        # Even best possible capture won't raise alpha
        return alpha
    
    # Generate and order captures
    captures = []
    for move in board.legal_moves:
        if board.is_capture(move):
            captures.append(move)
    
    # Sort captures by MVV-LVA (good captures first for better pruning)
    captures.sort(key=lambda m: ordering.mvv_lva_score(board, m), reverse=True)
    
    # Search each capture
    for move in captures:
        # Make move
        board.push(move)
        
        # Recurse with negated window (negamax)
        # Opponent's score is negated from our perspective
        score = -quiescence(board, -beta, -alpha, eng, q_depth + 1)
        
        # Unmake move
        board.pop()
        
        # Beta cutoff: This capture is too good
        # Opponent won't let us reach this position
        if score >= beta:
            return beta
        
        # Alpha update: Found a better move
        if score > alpha:
            alpha = score
    
    # Return best score found (or stand-pat if no captures improved position)
    return alpha
