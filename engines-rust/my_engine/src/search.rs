use crate::utils::{Board, Move};
use crate::utils;
use crate::engine::EngineRef;

pub fn search_root(board: &Board, eng: &EngineRef) -> (i32, Option<Move>) {
    // Very small stub: pick the first legal move
    let moves = board.legal_moves();
    if moves.is_empty() {
        return (0, None);
    }
    (0, Some(moves[0].clone()))
}

pub fn negamax(_board: &mut Board, _depth: i32, _alpha: i32, _beta: i32, _eng: &EngineRef, _ply: i32) -> i32 {
    0
}

pub fn quiescence(_board: &mut Board, _alpha: i32, _beta: i32, _eng: &EngineRef, _q_depth: i32) -> i32 {
    0
}
