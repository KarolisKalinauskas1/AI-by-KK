pub fn game_phase(_board_repr: &str) -> i32 {
    // Simplified phase
    12
}

pub fn tapered_score(mg: i32, eg: i32, phase: i32) -> i32 {
    const MAX_PHASE: i32 = 24;
    (phase * mg + (MAX_PHASE - phase) * eg) / MAX_PHASE
}
