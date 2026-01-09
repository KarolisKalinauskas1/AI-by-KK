use crate::utils::{Board, Move};

pub fn order_moves(board: &Board, _tt_move: Option<&Move>) -> Vec<Move> {
    // Return board.legal_moves() as-is for now
    board.legal_moves()
}

pub fn mvv_lva_score(_board: &Board, _mv: &Move) -> i32 {
    0
}
