use std::io::{self, Write};
use crate::engine::{Engine, TimeControl};
use crate::utils::{Board};

pub fn main_loop() {
    let mut engine = Engine::new(128);
    let mut board = Board::new();

    let stdin = io::stdin();
    loop {
        let mut line = String::new();
        if stdin.read_line(&mut line).is_err() { break; }
        let line = line.trim();
        if line.is_empty() { continue; }
        let parts: Vec<&str> = line.split_whitespace().collect();
        match parts[0] {
            "uci" => {
                println!("id name MyEngine-Rust");
                println!("id author KK");
                println!("uciok");
            }
            "isready" => println!("readyok"),
            "ucinewgame" => { engine.tt.clear(); board = Board::new(); },
            "position" => {
                // Very small support: "position startpos" or "position fen ..."
                if parts.len() >= 2 && parts[1] == "startpos" {
                    board = Board::new();
                }
            }
            "go" => {
                let tc = TimeControl { wtime: None, btime: None, winc: None, binc: None, movestogo: None };
                let mv = engine.choose_move(&mut board, &tc);
                println!("bestmove {}", mv.0);
            }
            "stop" => engine.stop_token.set(),
            "quit" => break,
            _ => println!("# Unknown command: {}", parts[0]),
        }
        io::stdout().flush().ok();
    }
}
