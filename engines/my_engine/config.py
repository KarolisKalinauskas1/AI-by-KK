"""
Engine Configuration

Centralizes all engine knobs and provides YAML loading with safe defaults.

Why keep config small:
- Simplifies exam explanations and testing
- Each parameter has clear impact on strength/speed
- Easy to tune without complex interactions

Configuration Structure:
- search: depth limits, time control, TT size, quiescence, ordering
- evaluation: weights for each eval component
- logging: debug output control

Safe defaults ensure the engine works out-of-box even with minimal config.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
import yaml
from pathlib import Path


@dataclass
class EngineConfig:
    """
    Engine configuration parameters.
    
    Attributes:
        max_depth: Maximum search depth (typical: 6-8)
        time_ms: Fixed time per move in ms (None = use clock-based time mgmt)
        tt_mb: Transposition table size in MB (16-1024)
        quiescence: Enable quiescence search (recommended: True)
        ordering: Move ordering strategy
        eval_weights: Weights for evaluation components
        logging: Debug output settings
    
    How each knob affects performance:
    - max_depth: Higher = stronger but slower; 7 is good balance
    - time_ms: Fixed time per move; useful for testing
    - tt_mb: More memory = better caching; 128MB is reasonable
    - quiescence: Prevents horizon effect; critical for tactical play
    - eval_weights: Fine-tune positional understanding
    """
    
    max_depth: int = 7
    time_ms: Optional[int] = 1500
    tt_mb: int = 128
    quiescence: bool = True
    ordering: Literal["tt_mvv_lva_quiet"] = "tt_mvv_lva_quiet"
    
    eval_weights: dict[str, float] = field(default_factory=lambda: {
        "pst": 1.0,
        "mobility": 0.1,
        "king_safety": 0.2,
        "pawns": 0.15,
        "rook_open_file": 0.1,
        "bishop_pair": 0.25
    })
    
    logging: dict[str, bool] = field(default_factory=lambda: {
        "emit_pv": True,
        "emit_depth_log": True
    })


def load_config(path: str) -> EngineConfig:
    """
    Load engine configuration from YAML file.
    
    Args:
        path: Path to config.yaml file
    
    Returns:
        EngineConfig with loaded values or defaults
    
    Note: Missing fields use default values for robustness.
    """
    config_path = Path(path)
    
    # Return defaults if file doesn't exist
    if not config_path.exists():
        return EngineConfig()
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return EngineConfig()
        
        # Extract nested sections
        search = data.get('search', {})
        evaluation = data.get('evaluation', {})
        logging = data.get('logging', {})
        
        # Build config with explicit values or defaults
        return EngineConfig(
            max_depth=search.get('max_depth', 7),
            time_ms=search.get('time_ms', 1500),
            tt_mb=search.get('tt_mb', 128),
            quiescence=search.get('quiescence', True),
            ordering=search.get('ordering', "tt_mvv_lva_quiet"),
            eval_weights=evaluation.get('weights', EngineConfig().eval_weights),
            logging={
                "emit_pv": logging.get('pv', True),
                "emit_depth_log": logging.get('depth_log', True)
            }
        )
    
    except Exception as e:
        print(f"# Warning: Error loading config from {path}: {e}")
        return EngineConfig()
