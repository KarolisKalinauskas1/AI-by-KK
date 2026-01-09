use std::collections::HashMap;
use crate::utils::Move;

#[derive(Clone, Debug)]
pub struct TTEntry {
    pub depth: i32,
    pub score: i32,
    pub flag: i32,
    pub best_move: Option<Move>,
    pub age: i32,
}

pub struct TranspositionTable {
    table: HashMap<u64, TTEntry>,
    pub generation: i32,
}

impl TranspositionTable {
    pub fn new(_size_mb: usize) -> Self {
        TranspositionTable { table: HashMap::new(), generation: 0 }
    }

    pub fn probe(&self, key: u64) -> Option<TTEntry> {
        self.table.get(&key).cloned()
    }

    pub fn store(&mut self, key: u64, entry: TTEntry) {
        self.table.insert(key, entry);
    }

    pub fn clear(&mut self) {
        self.table.clear();
        self.generation += 1;
    }

    pub fn new_search(&mut self) {
        self.generation += 1;
    }
}
