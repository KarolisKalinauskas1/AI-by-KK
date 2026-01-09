use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub const INF: i32 = 50_000;
pub const MATE: i32 = 32_000;

pub fn now_ms() -> u128 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis()
}

pub fn elapsed_ms(start_ms: u128) -> u128 {
    now_ms() - start_ms
}

pub fn nps(nodes: u64, elapsed_ms: u128) -> u64 {
    if elapsed_ms == 0 { return 0; }
    ((nodes as u128 * 1000) / elapsed_ms) as u64
}

// Simple Zobrist-like hash of board string; in Python version this used chess board
pub fn zobrist(board_repr: &str) -> u64 {
    let mut s = DefaultHasher::new();
    board_repr.hash(&mut s);
    s.finish()
}

// Minimal placeholder types used across modules
#[derive(Clone, Debug)]
pub struct Move(pub String);

#[derive(Clone, Debug)]
pub struct Board {
    pub repr: String,
}

impl Board {
    pub fn new() -> Self {
        Board { repr: String::from("startpos") }
    }

    pub fn legal_moves(&self) -> Vec<Move> {
        // Placeholder: return some pseudo-moves
        vec![Move(String::from("e2e4")), Move(String::from("d2d4"))]
    }

    pub fn push(&mut self, mv: &Move) {
        // Update repr for hashing simplicity
        self.repr = format!("{} {}", self.repr, mv.0);
    }

    pub fn pop(&mut self) {
        // No-op for stub
    }
}
