"""
Move Ordering (Stub)

Purpose: Order moves to maximize alpha-beta cutoffs.

Strategy:
1. TT move (hash move from transposition table)
2. Captures by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
3. Quiet moves (unordered for simplicity)

Why ordering matters:
- Earlier cutoffs = less tree to search
- Good ordering can reduce effective branching factor significantly
- MVV-LVA intuition: capturing queen with pawn is better than with queen
"""

import chess
from typing import Optional

# Piece values for MVV-LVA (similar to evaluation, but simplified)
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0  # King captures shouldn't happen in legal positions
}


def order_moves(board: chess.Board, tt_move: Optional[chess.Move] = None) -> list[chess.Move]:
    """
    Order moves for alpha-beta search.
    
    Ordering strategy:
    1. TT move (hash move from transposition table) - highest priority
    2. Captures sorted by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    3. Quiet moves (non-captures) - lowest priority
    
    Args:
        board: Current position
        tt_move: Best move from transposition table (if any)
    
    Returns:
        Ordered list of legal moves
    
    Example:
        For position with TT move e2e4, captures QxR and PxQ, quiet Nf3:
        Returns: [e2e4, PxQ, QxR, Nf3]
        (TT first, then PxQ scores higher than QxR, then quiet)
    """
    ordered = []
    captures = []
    quiets = []
    
    legal_moves = list(board.legal_moves)
    
    # Separate moves into categories
    for move in legal_moves:
        # Skip TT move (we'll add it first)
        if tt_move and move == tt_move:
            continue
        
        if board.is_capture(move):
            captures.append(move)
        else:
            quiets.append(move)
    
    # Sort captures by MVV-LVA (higher score = better)
    captures.sort(key=lambda m: mvv_lva_score(board, m), reverse=True)
    
    # Build final ordered list
    # 1. TT move first (if legal)
    if tt_move and tt_move in legal_moves:
        ordered.append(tt_move)
    
    # 2. Captures sorted by MVV-LVA
    ordered.extend(captures)
    
    # 3. Quiet moves (could add killer moves, history heuristic later)
    ordered.extend(quiets)
    
    return ordered


def mvv_lva_score(board: chess.Board, move: chess.Move) -> int:
    """
    Calculate MVV-LVA score for a capture.
    
    MVV-LVA (Most Valuable Victim - Least Valuable Attacker):
    - Prioritize capturing high-value pieces (victim)
    - Use low-value pieces to capture (attacker)
    - Formula: victim_value * 10 - attacker_value
    - Multiply victim by 10 to ensure it dominates the score
    
    Args:
        board: Current position
        move: Capture move
    
    Returns:
        Score (higher = better capture)
    
    Examples:
        - Pawn takes Queen: 9*10 - 1 = 89 (excellent!)
        - Queen takes Pawn: 1*10 - 9 = 1 (poor trade)
        - Knight takes Rook: 5*10 - 3 = 47 (good)
        - Rook takes Knight: 3*10 - 5 = 25 (okay)
    """
    # Get the piece being captured (victim)
    victim_square = move.to_square
    victim_piece = board.piece_at(victim_square)
    
    if victim_piece is None:
        # En passant capture
        if board.is_en_passant(move):
            victim_value = PIECE_VALUES[chess.PAWN]
        else:
            # Not a capture (shouldn't happen if used correctly)
            return 0
    else:
        victim_value = PIECE_VALUES[victim_piece.piece_type]
    
    # Get the attacking piece (attacker)
    attacker_square = move.from_square
    attacker_piece = board.piece_at(attacker_square)
    
    if attacker_piece is None:
        # Shouldn't happen in legal positions
        return 0
    
    attacker_value = PIECE_VALUES[attacker_piece.piece_type]
    
    # MVV-LVA formula: prioritize valuable victims, deprioritize valuable attackers
    # Multiply victim by 10 to ensure victim value dominates
    return victim_value * 10 - attacker_value
