# Product Notes

BayesianDraft is a local fantasy football draft assistant for configurable ESPN-style full-PPR redraft leagues.

The project is built around a live draft-room workflow: enter picks as they happen, keep every roster up to date, and use the current board state to decide what to do next.

## Core Idea

Static rankings are only one part of a draft decision. BayesianDraft tries to combine:

- the available player pool
- your current roster
- other managers' rosters
- player projections
- positional scarcity
- ADP and market cost
- your future pick positions
- probability that a player or position will still be available later
- simulated roster outcomes

The recommendation is not meant to be magic. It should be inspectable enough that you can understand why the engine likes a player.

## Main Modes

- Draft Room: live manual draft tracking, recommendations, draft board, rosters, save/load, and undo/redo.
- Rankings: all-player and position-filtered rankings with tiers, ADP deltas, VORP, and selected-player details.
- Recommendations: best overall pick, score breakdown, position groups, and path-bank opportunity context.
- Simulation: seeded draft-path analysis for comparing managers and next-pick strategy directions.

## Public League Config

The committed league config is public-safe:

- Platform: ESPN-style
- Format: 14-team redraft
- Scoring: full PPR
- Draft type: snake
- User draft slot: 8

Real manager names should stay in local ignored config files, not committed docs or config.
