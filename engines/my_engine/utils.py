"""
Utilities (Stub)

Purpose: Low-level helpers for search and evaluation.

Constants:
- INF = 50000 (infinity for alpha-beta)
- MATE = 32000 (mate score base)

Mate Encoding:
- mate_in(ply) = MATE - ply (prefer faster mates)
- mated_in(ply) = -MATE + ply (prefer longer defense)
- Allows distinguishing mate distance in search

Zobrist Hashing:
- Deterministic random number generation (seeded)
- One 64-bit number per (piece_type, color, square)
- Additional bits for: side-to-move, castling rights, en passant file
- XOR-based incremental updates during search

Timing:
- now_ms(): current time in milliseconds
- nps(nodes, ms): nodes per second calculation
"""

import chess
import random
import time
from typing import Optional

# Score constants
Score = int
INF = 50000
MATE = 32000


def mate_in(ply: int) -> int:
    """
    Encode mate-in-N score.
    
    Args:
        ply: Plies until mate
    
    Returns:
        Score value (higher ply = lower score to prefer faster mates)
    """
    return MATE - ply


def mated_in(ply: int) -> int:
    """
    Encode mated-in-N score.
    
    Args:
        ply: Plies until being mated
    
    Returns:
        Negative score (higher ply = less negative to prefer longer defense)
    """
    return -MATE + ply


# Zobrist keys (initialized once)
_zobrist_initialized = False
_zobrist_pieces: dict = {}
_zobrist_side: int = 0
_zobrist_castling: dict = {}
_zobrist_ep: dict = {}


def _init_zobrist():
    """Initialize Zobrist random numbers (deterministic seed for reproducibility)."""
    global _zobrist_initialized, _zobrist_pieces, _zobrist_side, _zobrist_castling, _zobrist_ep
    
    if _zobrist_initialized:
        return
    
    # Seed for determinism (same keys across runs)
    random.seed(42)
    
    # Piece keys: (piece_type, color, square) -> random int
    _zobrist_pieces = {}
    for piece_type in chess.PIECE_TYPES:
        for color in chess.COLORS:
            for square in chess.SQUARES:
                _zobrist_pieces[(piece_type, color, square)] = random.getrandbits(64)
    
    # Side to move
    _zobrist_side = random.getrandbits(64)
    
    # Castling rights (4 bits: K, Q, k, q)
    _zobrist_castling = {
        chess.BB_A1: random.getrandbits(64),  # White queenside
        chess.BB_H1: random.getrandbits(64),  # White kingside
        chess.BB_A8: random.getrandbits(64),  # Black queenside
        chess.BB_H8: random.getrandbits(64),  # Black kingside
    }
    
    # En passant file (0-7)
    _zobrist_ep = {file: random.getrandbits(64) for file in range(8)}
    
    _zobrist_initialized = True


def zobrist(board: chess.Board) -> int:
    """
    Compute Zobrist hash for position.
    
    Args:
        board: Position to hash
    
    Returns:
        64-bit hash value
    
    Note: Deterministic (same position = same hash).
    """
    _init_zobrist()
    
    h = 0
    
    # XOR all pieces
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            h ^= _zobrist_pieces[(piece.piece_type, piece.color, square)]
    
    # Side to move
    if board.turn == chess.BLACK:
        h ^= _zobrist_side
    
    # Castling rights (simplified)
    if board.has_kingside_castling_rights(chess.WHITE):
        h ^= _zobrist_castling[chess.BB_H1]
    if board.has_queenside_castling_rights(chess.WHITE):
        h ^= _zobrist_castling[chess.BB_A1]
    if board.has_kingside_castling_rights(chess.BLACK):
        h ^= _zobrist_castling[chess.BB_H8]
    if board.has_queenside_castling_rights(chess.BLACK):
        h ^= _zobrist_castling[chess.BB_A8]
    
    # En passant
    if board.ep_square is not None:
        ep_file = chess.square_file(board.ep_square)
        h ^= _zobrist_ep[ep_file]
    
    return h


def now_ms() -> int:
    """
    Current time in milliseconds.
    
    Returns:
        Current timestamp in milliseconds (integer)
    """
    return int(time.time() * 1000)


def elapsed_ms(start_ms: int) -> int:
    """
    Calculate elapsed time since start.
    
    Args:
        start_ms: Start time in milliseconds
    
    Returns:
        Elapsed time in milliseconds
    """
    return now_ms() - start_ms


def nps(nodes: int, elapsed_ms: int) -> int:
    """
    Calculate nodes per second.
    
    Args:
        nodes: Total nodes searched
        elapsed_ms: Elapsed time in milliseconds
    
    Returns:
        Nodes per second (0 if elapsed_ms is 0)
    """
    if elapsed_ms <= 0:
        return 0
    return int((nodes * 1000) / elapsed_ms)
