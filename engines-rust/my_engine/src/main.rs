mod engine;
mod evaluator;
mod ordering;
mod pst;
mod search;
mod tt;
mod uci;
mod utils;

use uci::main_loop;

fn main() {
    println!("Starting my_engine (Rust) — UCI stub");
    main_loop();
}
