"""
UCI Protocol Handler

Minimal UCI protocol parser and emitter.
Supports core UCI commands for chess engine communication.

UCI Commands Supported:
- uci: identify engine and options
- isready: check if engine is ready
- ucinewgame: reset internal state
- position [startpos|fen] moves ...: set board position
- go [wtime btime winc binc movestogo]: start search
- stop: halt search immediately
- quit: exit engine

Info Lines:
The engine emits 'info' lines during search with:
- depth: current search depth
- nodes: nodes searched
- nps: nodes per second
- score cp: centipawn score
- pv: principal variation (best line)

These info lines are critical for GUI/starter diagnostics and debugging.
"""

import sys
import chess
from typing import Optional

import config as cfg
import engine as eng

# Global state
stop_token = None
current_engine: Optional[eng.Engine] = None
current_board: chess.Board = chess.Board()


def print_flush(msg: str):
    """Print message and flush stdout for UCI communication."""
    print(msg)
    sys.stdout.flush()


def handle_uci():
    """Respond to 'uci' command with engine identification."""
    print_flush("id name MyEngine")
    print_flush("id author KK")
    print_flush("option name Hash type spin default 128 min 16 max 1024")
    print_flush("uciok")


def handle_isready():
    """Respond to 'isready' command."""
    print_flush("readyok")


def handle_ucinewgame():
    """Reset engine state for new game."""
    global current_engine, current_board
    if current_engine and hasattr(current_engine, 'tt'):
        # Clear transposition table for new game
        current_engine.tt.clear()
    current_board = chess.Board()


def handle_position(parts: list[str]):
    """
    Parse and set board position.
    Format: position [startpos | fen <fenstring>] [moves <move1> <move2> ...]
    """
    global current_board
    
    idx = 1
    if idx < len(parts):
        if parts[idx] == "startpos":
            current_board = chess.Board()
            idx += 1
        elif parts[idx] == "fen":
            # Read FEN string (next 6 tokens typically)
            fen_parts = []
            idx += 1
            while idx < len(parts) and parts[idx] != "moves":
                fen_parts.append(parts[idx])
                idx += 1
            fen_string = " ".join(fen_parts)
            current_board = chess.Board(fen_string)
    
    # Apply moves if present
    if idx < len(parts) and parts[idx] == "moves":
        idx += 1
        while idx < len(parts):
            move_uci = parts[idx]
            try:
                move = chess.Move.from_uci(move_uci)
                if move in current_board.legal_moves:
                    current_board.push(move)
            except Exception as e:
                print_flush(f"# Error parsing move {move_uci}: {e}")
            idx += 1


def handle_go(parts: list[str]):
    """
    Parse 'go' command and start search.
    Format: go [wtime X] [btime X] [winc X] [binc X] [movestogo X] [depth X] [movetime X]
    """
    global current_engine, current_board
    
    tc = eng.TimeControl()
    
    # Parse time control parameters
    i = 1
    while i < len(parts):
        param = parts[i]
        if param == "wtime" and i + 1 < len(parts):
            tc.wtime = int(parts[i + 1])
            i += 2
        elif param == "btime" and i + 1 < len(parts):
            tc.btime = int(parts[i + 1])
            i += 2
        elif param == "winc" and i + 1 < len(parts):
            tc.winc = int(parts[i + 1])
            i += 2
        elif param == "binc" and i + 1 < len(parts):
            tc.binc = int(parts[i + 1])
            i += 2
        elif param == "movestogo" and i + 1 < len(parts):
            tc.movestogo = int(parts[i + 1])
            i += 2
        else:
            i += 1
    
    # Call engine to choose move
    if current_engine:
        try:
            best_move = current_engine.choose_move(current_board, tc)
            print_flush(f"bestmove {best_move.uci()}")
        except Exception as e:
            print_flush(f"# Error in search: {e}")
            # Return a random legal move as fallback
            if list(current_board.legal_moves):
                import random
                fallback = random.choice(list(current_board.legal_moves))
                print_flush(f"bestmove {fallback.uci()}")


def handle_stop():
    """Handle 'stop' command - set stop flag."""
    global stop_token
    if stop_token:
        stop_token.set()


def handle_command(line: str):
    """
    Handle a single UCI command.
    
    Args:
        line: UCI command line
    
    Used for testing and scripted interaction.
    """
    global current_engine, stop_token
    
    # Initialize engine if not already done (for testing)
    if current_engine is None:
        engine_config = cfg.EngineConfig()
        current_engine = eng.Engine(engine_config)
        stop_token = current_engine.stop_token
    
    line = line.strip()
    if not line:
        return
    
    parts = line.split()
    command = parts[0]
    
    if command == "uci":
        handle_uci()
    elif command == "isready":
        handle_isready()
    elif command == "ucinewgame":
        handle_ucinewgame()
    elif command == "position":
        handle_position(parts)
    elif command == "go":
        handle_go(parts)
    elif command == "stop":
        handle_stop()
    elif command == "quit":
        pass
    else:
        print_flush(f"# Unknown command: {command}")


def main(config_path: str):
    """
    Main UCI loop.
    
    Args:
        config_path: Path to config.yaml file
    """
    global current_engine, stop_token
    
    # Load configuration and create engine
    engine_config = cfg.load_config(config_path)
    current_engine = eng.Engine(engine_config)
    stop_token = current_engine.stop_token
    
    # UCI command loop
    while True:
        try:
            line = input().strip()
            if not line:
                continue
            
            parts = line.split()
            command = parts[0]
            
            if command == "uci":
                handle_uci()
            elif command == "isready":
                handle_isready()
            elif command == "ucinewgame":
                handle_ucinewgame()
            elif command == "position":
                handle_position(parts)
            elif command == "go":
                handle_go(parts)
            elif command == "stop":
                handle_stop()
            elif command == "quit":
                break
            else:
                print_flush(f"# Unknown command: {command}")
        
        except EOFError:
            break
        except Exception as e:
            print_flush(f"# Error: {e}")
