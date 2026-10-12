#!/bin/bash
# Detached launcher for run_p2_grid.sh (survives the terminal closing).
cd "/c/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.claude/worktrees/heuristic-germain-8b299e" || exit 1
exec bash run_p2_grid.sh >> p2_grid_chain.log 2>&1
