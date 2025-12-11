"""
Homemade engine configuration for lichess-bot.
"""

import chess
from lib.engine_wrapper import MinimalEngine
from lib.lichess_types import MOVE, HOMEMADE_ARGS_TYPE

import random
import logging

logger = logging.getLogger(__name__)

# Import your custom engine
try:
    # Use absolute import from engines directory
    import sys
    import os
    
    # Add engines directory to path
    engines_dir = os.path.join(os.path.dirname(__file__), 'engines')
    if engines_dir not in sys.path:
        sys.path.insert(0, engines_dir)
    
    from my_engine.engine import AIbyKK
    CUSTOM_ENGINE_AVAILABLE = True
    logger.info("✓ Custom AIbyKK engine loaded")
    
except Exception as e:
    logger.warning(f"⚠ Could not import custom engine: {e}")
    logger.warning("⚠ Falling back to random engine")
    CUSTOM_ENGINE_AVAILABLE = False


class ExampleEngine(MinimalEngine):
    """
    Example engine that makes random moves.
    This is used as a fallback if custom engine fails to load.
    """
    
    def search(self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE) -> chess.engine.PlayResult:
        """Choose a random move."""
        legal_moves = list(board.legal_moves)
        if legal_moves:
            chosen_move = random.choice(legal_moves)
            logger.info(f"Random engine chose: {chosen_move}")
        else:
            chosen_move = None
        return chess.engine.PlayResult(chosen_move, None)


# Export the engine
if CUSTOM_ENGINE_AVAILABLE:
    # Use your custom AI engine
    Engine = AIbyKK
    logger.info("Using AIbyKK neural network engine")
else:
    # Fallback to random engine
    Engine = ExampleEngine
    logger.info("Using fallback random engine")