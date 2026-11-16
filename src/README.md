# Task 1 – N-Queens (Local Search & Propositional Logic)

## Requirements
Python 3.9+ and the packages in `requirements.txt`:

    pip install -r requirements.txt

## Structure
    nqueens/board.py         QueensBoard: board state, validity check, printing
    nqueens/cnf_encoder.py   CNFEncoder: propositional encoding -> CNF clauses
    nqueens/sat_solver.py    SATQueensSolver: solves the CNF with Glucose3 (PySAT)
    nqueens/min_conflicts.py MinConflictsSolver: Min-Conflicts + heuristics
    main.py                  command-line demo
    run_experiments.py       experiments -> results/*.csv, results/*.png
    demo.txt                 sample output

## Usage
    python main.py --n 8 --method sat
    python main.py --n 8 --method mc --var-heuristic oldest --init greedy --seed 1
    python run_experiments.py          # full experiments (a few minutes)
    python run_experiments.py --quick  # small run

Options for `--method mc`: `--var-heuristic {random,max_conflict,oldest}`, `--init {random,greedy}`.

## Encoding summary
Variable `x(r,c)` = "queen at row r, column c" (id `r*N + c + 1`).
Clauses: at-least-one per row and column; pairwise `(~a v ~b)` for any two squares sharing a
row, column or diagonal. #clauses = 2N + 2N*C(N,2) + 2*(2*sum_{k=1}^{N-1} C(k,2) + C(N,2)).
