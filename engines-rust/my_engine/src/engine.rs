use crate::tt::TranspositionTable;
use crate::utils::{Board, Move, now_ms};
use crate::search;

pub struct TimeControl {
    pub wtime: Option<i64>,
    pub btime: Option<i64>,
    pub winc: Option<i64>,
    pub binc: Option<i64>,
    pub movestogo: Option<i32>,
}

pub struct Stats {
    pub nodes: u64,
    pub qnodes: u64,
}

pub struct StopToken {
    stopped: bool,
}

impl StopToken {
    pub fn new() -> Self { StopToken { stopped: false } }
    pub fn is_set(&self) -> bool { self.stopped }
    pub fn set(&mut self) { self.stopped = true; }
    pub fn reset(&mut self) { self.stopped = false; }
}

pub struct Engine {
    pub tt: TranspositionTable,
    pub stop_token: StopToken,
    pub stats: Stats,
}

pub type EngineRef = Engine;

impl Engine {
    pub fn new(tt_mb: usize) -> Self {
        Engine {
            tt: TranspositionTable::new(tt_mb),
            stop_token: StopToken::new(),
            stats: Stats { nodes: 0, qnodes: 0 },
        }
    }

    pub fn choose_move(&mut self, board: &mut Board, _tc: &TimeControl) -> Move {
        self.stop_token.reset();
        self.stats.nodes = 0;
        let start = now_ms();
        let (_score, best_move) = search::search_root(board, self);
        if let Some(mv) = best_move {
            mv
        } else {
            // fallback
            board.legal_moves().get(0).unwrap().clone()
        }
    }

    pub fn should_stop(&self) -> bool {
        self.stop_token.is_set()
    }
}
