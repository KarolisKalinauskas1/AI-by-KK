"""
Position Evaluator (Stub)

Purpose: Return static evaluation score (centipawns) from side-to-move perspective.

Tapered Evaluation:
- Positions transition smoothly from middlegame (MG) to endgame (EG)
- score = phase_ratio * MG_score + (1 - phase_ratio) * EG_score
- phase = sum of piece weights: N/B=1, R=2, Q=4

Evaluation Terms:
1. Material: P=100, N=320, B=330, R=500, Q=900
2. Piece-Square Tables (PST): reward centralization, king safety
3. Bishop pair: +30-50 cp
4. Mobility: bonus per legal move (capped to avoid explosion)
5. Pawn structure:
   - Doubled pawns (penalty)
   - Isolated pawns (penalty)
   - Passed pawns (bonus, grows by rank, stronger in EG)
6. King safety:
   - Pawn shield bonus
   - Open/semi-open files near king (penalty)
7. Rook on open file: +10-15 cp

All integers (no floats in hot loop for speed).
"""

import chess
import pst

# Material values in centipawns
MATERIAL_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0  # King has no material value
}

# Evaluation weights (tunable)
MOBILITY_WEIGHT = 10  # cp per legal move difference
BISHOP_PAIR_BONUS = 40
ROOK_OPEN_FILE_BONUS = 10
DOUBLED_PAWN_PENALTY = 10
ISOLATED_PAWN_PENALTY = 10
PASSED_PAWN_BONUS = [0, 10, 20, 30, 40, 50, 60, 70]  # by rank (0-7)
KING_SHIELD_BONUS = 5  # per pawn in front of king


def evaluate(board: chess.Board) -> int:
    """
    Static evaluation of position.
    
    Args:
        board: Position to evaluate
    
    Returns:
        Score in centipawns from side-to-move perspective
        Positive = good for side to move
    
    Components:
    1. Material balance
    2. Piece-square tables (tapered)
    3. Mobility
    4. Pawn structure
    5. King safety
    6. Bishop pair
    7. Rook placement
    """
    # Handle terminal positions
    if board.is_checkmate():
        return -30000 if board.turn == chess.WHITE else 30000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0
    phase = pst.game_phase(board)
    
    # 1. Material
    score += _material_balance(board)
    
    # 2. PST (tapered by phase)
    mg_white, eg_white = pst.pst_score(board, chess.WHITE)
    mg_black, eg_black = pst.pst_score(board, chess.BLACK)
    
    white_pst = pst.tapered_score(mg_white, eg_white, phase)
    black_pst = pst.tapered_score(mg_black, eg_black, phase)
    score += white_pst - black_pst
    
    # 3. Mobility
    score += _mobility(board)
    
    # 4. Bishop pair
    score += _bishop_pair(board)
    
    # 5. Pawn structure
    score += _pawn_structure(board)
    
    # 6. King safety (mostly in middlegame)
    if phase > 12:  # Only evaluate king safety in non-endgame
        score += _king_safety(board)
    
    # 7. Rook placement
    score += _rook_placement(board)
    
    return score


def _material_balance(board: chess.Board) -> int:
    """Count material for both sides."""
    balance = 0
    
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        balance += (white_count - black_count) * MATERIAL_VALUES[piece_type]
    
    return balance


def _mobility(board: chess.Board) -> int:
    """
    Mobility: count legal moves for both sides.
    
    Returns:
        Mobility score (white - black) * weight
    """
    # Save current turn
    turn = board.turn
    
    # Count white's mobility
    board.turn = chess.WHITE
    white_mobility = board.legal_moves.count()
    
    # Count black's mobility
    board.turn = chess.BLACK
    black_mobility = board.legal_moves.count()
    
    # Restore turn
    board.turn = turn
    
    return (white_mobility - black_mobility) * MOBILITY_WEIGHT


def _bishop_pair(board: chess.Board) -> int:
    """Bishop pair bonus."""
    score = 0
    
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
    
    if white_bishops >= 2:
        score += BISHOP_PAIR_BONUS
    if black_bishops >= 2:
        score -= BISHOP_PAIR_BONUS
    
    return score


def _pawn_structure(board: chess.Board) -> int:
    """
    Evaluate pawn structure:
    - Doubled pawns (penalty)
    - Isolated pawns (penalty)
    - Passed pawns (bonus, increases by rank)
    """
    score = 0
    
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1
        pawns = board.pieces(chess.PAWN, color)
        
        # Count pawns per file
        files = [0] * 8
        for sq in pawns:
            files[chess.square_file(sq)] += 1
        
        # Doubled pawns
        for count in files:
            if count > 1:
                score += sign * -DOUBLED_PAWN_PENALTY * (count - 1)
        
        # Isolated and passed pawns
        for sq in pawns:
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            
            # Isolated: no friendly pawns on adjacent files
            has_neighbor = False
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file < 8 and files[adj_file] > 0:
                    has_neighbor = True
                    break
            
            if not has_neighbor:
                score += sign * -ISOLATED_PAWN_PENALTY
            
            # Passed pawn: no enemy pawns ahead on same/adjacent files
            is_passed = True
            for adj_file in [file - 1, file, file + 1]:
                if adj_file < 0 or adj_file >= 8:
                    continue
                
                enemy_pawns = board.pieces(chess.PAWN, not color)
                for enemy_sq in enemy_pawns:
                    if chess.square_file(enemy_sq) == adj_file:
                        enemy_rank = chess.square_rank(enemy_sq)
                        # Check if enemy pawn blocks advancement
                        if color == chess.WHITE and enemy_rank > rank:
                            is_passed = False
                            break
                        elif color == chess.BLACK and enemy_rank < rank:
                            is_passed = False
                            break
                
                if not is_passed:
                    break
            
            if is_passed:
                bonus_rank = rank if color == chess.WHITE else (7 - rank)
                score += sign * PASSED_PAWN_BONUS[min(bonus_rank, 7)]
    
    return score


def _king_safety(board: chess.Board) -> int:
    """
    King safety:
    - Pawn shield bonus (pawns in front of king)
    - Open file near king penalty
    """
    score = 0
    
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1
        king_sq = board.king(color)
        
        if king_sq is None:
            continue
        
        king_file = chess.square_file(king_sq)
        king_rank = chess.square_rank(king_sq)
        
        # Pawn shield: count friendly pawns near king
        shield_pawns = 0
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if file < 0 or file >= 8:
                continue
            
            # Look for pawns 1-2 ranks ahead
            for rank_offset in [1, 2]:
                if color == chess.WHITE:
                    check_rank = king_rank + rank_offset
                else:
                    check_rank = king_rank - rank_offset
                
                if check_rank < 0 or check_rank >= 8:
                    continue
                
                sq = chess.square(file, check_rank)
                piece = board.piece_at(sq)
                
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    shield_pawns += 1
        
        score += sign * shield_pawns * KING_SHIELD_BONUS
    
    return score


def _rook_placement(board: chess.Board) -> int:
    """Rook on open/semi-open file bonus."""
    score = 0
    
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1
        rooks = board.pieces(chess.ROOK, color)
        
        for rook_sq in rooks:
            file = chess.square_file(rook_sq)
            
            # Check if file is open (no pawns) or semi-open (no friendly pawns)
            has_friendly_pawn = False
            has_enemy_pawn = False
            
            for rank in range(8):
                sq = chess.square(file, rank)
                piece = board.piece_at(sq)
                
                if piece and piece.piece_type == chess.PAWN:
                    if piece.color == color:
                        has_friendly_pawn = True
                    else:
                        has_enemy_pawn = True
            
            # Open file (no pawns at all)
            if not has_friendly_pawn and not has_enemy_pawn:
                score += sign * ROOK_OPEN_FILE_BONUS
            # Semi-open file (no friendly pawns)
            elif not has_friendly_pawn:
                score += sign * (ROOK_OPEN_FILE_BONUS // 2)
    
    return score
