# PST - Piece Square Tables

import chess

# Piece phase values
PHASE_VALUES = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.PAWN: 0,
    chess.KING: 0
}

MAX_PHASE = 24

# Pawn PST
PAWN_PST_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]

PAWN_PST_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    80, 80, 80, 80, 80, 80, 80, 80,
    50, 50, 50, 50, 50, 50, 50, 50,
    30, 30, 30, 30, 30, 30, 30, 30,
    20, 20, 20, 20, 20, 20, 20, 20,
    10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10,
    0, 0, 0, 0, 0, 0, 0, 0
]

# Knight PST
KNIGHT_PST_MG = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

KNIGHT_PST_EG = KNIGHT_PST_MG

# Bishop PST
BISHOP_PST_MG = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

BISHOP_PST_EG = BISHOP_PST_MG

# Rook PST
ROOK_PST_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]

ROOK_PST_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    30, 30, 30, 30, 30, 30, 30, 30,
    10, 10, 10, 10, 10, 10, 10, 10,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]

# Queen PST
QUEEN_PST_MG = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

QUEEN_PST_EG = QUEEN_PST_MG

# King PST
KING_PST_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20
]

KING_PST_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

# Lookup tables
PST_MG = {
    chess.PAWN: PAWN_PST_MG,
    chess.KNIGHT: KNIGHT_PST_MG,
    chess.BISHOP: BISHOP_PST_MG,
    chess.ROOK: ROOK_PST_MG,
    chess.QUEEN: QUEEN_PST_MG,
    chess.KING: KING_PST_MG
}

PST_EG = {
    chess.PAWN: PAWN_PST_EG,
    chess.KNIGHT: KNIGHT_PST_EG,
    chess.BISHOP: BISHOP_PST_EG,
    chess.ROOK: ROOK_PST_EG,
    chess.QUEEN: QUEEN_PST_EG,
    chess.KING: KING_PST_EG
}


def game_phase(board):
    """Calculate game phase (0-24)."""
    phase = 0
    for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        phase += len(board.pieces(pt, chess.WHITE)) * PHASE_VALUES[pt]
        phase += len(board.pieces(pt, chess.BLACK)) * PHASE_VALUES[pt]
    return min(phase, MAX_PHASE)


def mirror_square(sq):
    """Mirror square for black."""
    return (7 - sq // 8) * 8 + sq % 8


def pst_value(piece_type, square, color, mg=True):
    """Get PST value for a piece."""
    table = PST_MG if mg else PST_EG
    sq = square if color == chess.WHITE else mirror_square(square)
    return table[piece_type][sq]


def pst_score(board, side):
    """Calculate PST score for one side."""
    mg, eg = 0, 0
    for pt in chess.PIECE_TYPES:
        for sq in board.pieces(pt, side):
            mg += pst_value(pt, sq, side, mg=True)
            eg += pst_value(pt, sq, side, mg=False)
    return (mg, eg)


def tapered_score(mg_score, eg_score, phase):
    """Blend MG and EG scores."""
    if MAX_PHASE == 0:
        return eg_score
    return (phase * mg_score + (MAX_PHASE - phase) * eg_score) // MAX_PHASE
