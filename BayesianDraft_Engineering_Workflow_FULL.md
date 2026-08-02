# BayesianDraft — Engineering Workflow and Milestone Handoff

## 1. Purpose

This document converts the BayesianDraft product specification into an executable engineering workflow.

Treat the project specification as the source of truth.

Before making changes, read:

- README.md
- docs/product-spec.md
- docs/architecture.md
- docs/modeling.md
- docs/data-schema.md
- docs/data-sources.md
- docs/scoring.md
- docs/ui.md
- docs/testing.md
- docs/backtesting.md
- docs/api.md
- docs/model-registry.md
- docs/roadmap.md
- Existing ADRs
- Existing source code
- Existing tests

---

## 2. Engineering Workflow

Build BayesianDraft in small, complete vertical slices.

Never attempt to build the entire application in one pass.

Before each milestone:

1. Read relevant documentation.
2. Summarize current repository state.
3. State the milestone objective.
4. List files to create or modify.
5. State acceptance criteria.
6. State tests to add.
7. Identify risks and assumptions.
8. Ask for approval if the change is large, destructive, or ambiguous.

During implementation:

1. Make small changes.
2. Run tests frequently.
3. Keep the repository runnable.
4. Avoid unrelated refactors.
5. Keep public interfaces typed.
6. Use fixtures instead of live services in tests.
7. Document configuration changes.
8. Avoid placeholder logic that looks production-ready.

After implementation:

1. Format.
2. Lint.
3. Type-check.
4. Run unit tests.
5. Run integration tests.
6. Run simulation tests when relevant.
7. Update docs.
8. Update CHANGELOG.md.
9. Summarize changes.
10. Propose a commit message.
11. Provide exact Git commands.
12. Do not push unless explicitly asked.

---

## 3. GitHub Repository Setup

If the folder is not yet a Git repository:

```bash
git init
git branch -M main
```

Do not create a remote until repository visibility is confirmed.

After confirmation:

```bash
gh repo create BayesianDraft --private --source=. --remote=origin --push
```

Use `--public` only if explicitly requested.

Create:

- .gitignore
- .editorconfig
- .env.example
- README.md
- CONTRIBUTING.md
- CHANGELOG.md
- LICENSE after confirming license
- .github/workflows/
- .github/ISSUE_TEMPLATE/
- .github/pull_request_template.md

Do not commit:

- Secrets
- API keys
- Cookies
- ESPN authentication tokens
- Node modules
- Virtual environments
- Build output
- Large raw datasets
- Unlicensed proprietary data
- Large model artifacts
- Local database files with sensitive information

---

## 4. Branch and Commit Strategy

Keep `main` runnable.

Use short-lived branches for substantial work.

Examples:

- feature/scoring-engine
- feature/draft-state
- feature/manual-draft-ui
- feature/recommendation-engine
- feature/monte-carlo
- feature/projections
- feature/season-simulator
- data/nflverse-ingestion
- test/historical-backtesting
- docs/data-schema

Commit message examples:

- `chore: initialize BayesianDraft repository`
- `feat: add configurable ESPN scoring engine`
- `feat: implement deterministic snake draft state`
- `test: cover defense scoring boundaries`
- `docs: define player and projection schemas`
- `data: add versioned nflverse ingestion manifest`
- `refactor: separate roster utility from recommendation logic`
- `fix: correct reverse-order draft progression`

Each commit should:

- Contain one coherent idea
- Include tests for behavior changes
- Avoid unrelated formatting
- Keep the repository runnable
- Explain why the change exists

---

## 5. Definition of Done

A milestone is complete only when:

- Acceptance criteria are satisfied
- Tests pass
- Documentation is updated
- Static checks pass
- No secrets are committed
- No temporary files are committed
- Known limitations are documented
- Project runs locally
- CHANGELOG.md is updated
- A coherent commit message is proposed

---

## 6. Milestone Plan

## Milestone 0 — Repository Foundation

### Goal

Create a clean, reproducible monorepo.

### Deliverables

- Git repository
- Base directory structure
- Python project configuration
- React/TypeScript frontend setup
- Shared development commands
- .gitignore
- .editorconfig
- .env.example
- README setup instructions
- GitHub Actions CI
- Ruff
- pytest
- mypy where practical
- frontend linting
- frontend tests
- league YAML
- documentation skeleton
- ADR template

### Acceptance criteria

- Backend installs
- Frontend installs
- Backend tests run
- Frontend tests run
- CI exists
- League config validates
- No production feature logic is required

### Suggested commit

`chore: initialize BayesianDraft repository and tooling`

---

## Milestone 1 — Configurable Scoring Engine

### Goal

Convert raw player/team statistics into exact fantasy points.

### Implement

- Passing scoring
- Rushing scoring
- Receiving scoring
- Kicking scoring
- D/ST event scoring
- D/ST points-allowed buckets
- D/ST yards-allowed buckets

### Requirements

- Pure functions
- Config-driven
- No UI dependency
- No data-source dependency
- Boundary tests

### Tests

- Passing TD = 4
- Rushing TD = 6
- Receiving TD = 6
- Full PPR = 1 per reception
- 60+ FG = 6
- Missed FG = -1
- 18–27 points allowed = 0
- 300–349 yards allowed = 0
- Every bucket boundary
- Negative scoring
- Combined stat lines

### Acceptance criteria

- Exact league scoring reproduced
- Config can be replaced without core code changes
- Boundary tests pass

### Suggested commit

`feat: implement configurable ESPN scoring engine`

---

## Milestone 2 — Deterministic Draft-State Engine

### Goal

Implement the 12-team snake draft.

### Domain entities

- Manager
- Player
- DraftPick
- Roster
- DraftState
- LeagueConfig

### Implement

- Snake order
- Current manager
- Current round
- Overall pick
- Round pick
- the user's future picks
- Record pick
- Remove player from availability
- Add player to roster
- Advance draft
- Undo
- Redo
- Edit prior pick
- Save
- Load
- Serialize
- Restore

### Tests

- Round 1 order
- Round 2 reverse order
- Multi-round progression
- the user at 1.09
- the user at 2.04
- the user at 3.09
- the user at 4.04
- Duplicate player rejection
- Invalid manager rejection
- Undo restoration
- Redo restoration
- Save/load equality

### Acceptance criteria

- Complete mock draft can be entered through backend logic
- State transitions are deterministic
- State can be serialized and restored

### Suggested commit

`feat: add deterministic snake draft state engine`

---

## Milestone 3 — Data Schemas and Snapshot Model

### Goal

Define stable internal schemas before integrating live data.

### Create schemas

- Player
- Team
- Game
- WeeklyStats
- SeasonStats
- Projection
- ADP
- Injury
- DraftPick
- Roster
- DraftState
- Recommendation
- SimulationResult
- LeagueConfig
- DataSnapshot

### Requirements

- Typed models
- Validation
- Source provenance
- Schema version
- Example records
- Synthetic fixtures
- Stable identifiers
- Cross-source ID mapping

### Acceptance criteria

- All schemas validate
- Invalid fields fail clearly
- Every data record links to source metadata
- Fixtures are clearly marked synthetic
- `docs/data-schema.md` is complete

### Suggested commit

`feat: define core data and snapshot schemas`

---

## Milestone 4 — Baseline Player Dataset

### Goal

Create a small, reproducible player dataset that supports the product before advanced ingestion is complete.

### Implement

- Local fixture dataset
- Player IDs
- Position/team mapping
- Basic projections
- ESPN ADP field
- Underdog ADP field
- Injury field
- Tier field
- Source metadata

### Requirements

- Do not present synthetic data as real
- Use snapshot manifests
- Support JSON/Parquet/CSV imports
- Add validation

### Acceptance criteria

- Dataset loads
- Data source is visible
- Snapshot ID is visible
- Invalid rows are rejected
- Tests are offline

### Suggested commit

`data: add baseline player snapshot and fixtures`

---

## Milestone 5 — Baseline Ranking Engine

### Goal

Produce transparent rankings before advanced ML.

### Implement

- Projected points
- Position rank
- Overall rank
- Replacement level
- VORP
- Value above starter
- Tier assignment
- ESPN ADP difference
- Underdog ADP difference
- Sleeper score
- Fade score

### Requirements

- Transparent formulas
- Configurable replacement assumptions
- Position-aware ranking
- Export JSON/CSV

### Acceptance criteria

- Rankings deterministic
- Replacement logic tested
- Sleeper/fade scores explainable
- Exports work

### Suggested commit

`feat: add baseline value-based rankings`

---

## Milestone 6 — FastAPI Backend

### Goal

Expose league, draft, roster, and ranking behavior through a local API.

### Endpoints

- Health
- League config
- Create draft
- Get draft state
- Available players
- Record pick
- Undo
- Redo
- Edit pick
- Manager rosters
- User roster
- Rankings
- Player details
- Save draft
- Load draft

### Requirements

- Typed request/response models
- Useful errors
- OpenAPI docs
- Integration tests
- No authentication required for local use

### Acceptance criteria

- Full manual draft workflow works through API
- Invalid transitions return useful errors
- Integration tests pass

### Suggested commit

`feat: expose draft and ranking engines through FastAPI`

---

## Milestone 7 — Live Draft UI Vertical Slice

### Goal

Create a usable manual draft room.

### Build

- Current-pick header
- Manager on clock
- Picks until the user
- Available-player table
- Position filters
- Search
- Mark drafted
- Manager default
- Confirmation
- Draft board
- the user roster
- Opponent rosters
- Undo
- Redo
- Save
- Load
- Data freshness

### UX priorities

- Fast
- Minimal clicks
- Desktop-first
- Clear recommendation area
- Manual mode always available

### Acceptance criteria

- Full 12-team draft can be entered through UI
- Draft board updates
- Rosters update
- Undo works
- Saved draft survives reload

### Suggested commit

`feat: build manual live draft room`

---

## Milestone 8 — Explainable Baseline Recommendation Engine

### Goal

Recommend players using transparent state-aware heuristics.

### Score components

- VORP
- Position need
- Starting vacancies
- Tier scarcity
- Roster balance
- ESPN value
- Underdog value
- Estimated availability
- Penalty for unnecessary backup positions
- Late-round D/ST/K handling

### Output

- Primary recommendation
- Top alternatives
- Why this player
- Why this position
- Why now
- Next-pick availability
- Roster impact
- Confidence

### Acceptance criteria

- Recommendation changes with roster state
- Explanations match actual score components
- System does not blindly select raw projected points
- Logic deterministic and tested

### Suggested commit

`feat: add explainable roster-aware recommendations`

---

## Milestone 9 — ADP Distributions and Availability Model

### Goal

Estimate whether a player survives to future picks.

### Implement

- ADP probability distributions
- Expected selection range
- Position demand
- Roster-need effects
- Position-run effects
- Pick-distance effects
- Seeded simulation
- Availability probability

### Metrics

- Brier score
- Log loss
- Calibration
- Error by position
- Error by tier

### Acceptance criteria

- Same seed reproduces results
- Impossible cases approach zero
- Near-certain cases approach one
- the user's next pick calculated correctly
- Results inspectable

### Suggested commit

`feat: add player availability prediction`

---

## Milestone 10 — Monte Carlo Draft Simulator

### Goal

Simulate complete drafts conditional on current state.

### Implement

- Generalized opponent selection model
- Roster constraints
- ADP-based choices
- Position runs
- Candidate rollouts
- Seed control
- Simulation count control
- Caching
- Result export

### Acceptance criteria

- Drafts always remain legal
- Duplicate players impossible
- Results reproducible
- Runtime measured
- Simulation cache works

### Suggested commit

`feat: add Monte Carlo draft simulation`

---

## Milestone 11 — Historical Data Ingestion

### Goal

Build reproducible pipelines for historical NFL and fantasy-market data.

### Workstreams

- nflverse ingestion
- Roster ingestion
- Schedule ingestion
- Weekly stats
- Participation/snaps
- ADP snapshots
- Injury snapshots
- Team context

### Requirements

- Source manifest
- Retrieval timestamp
- Raw immutable copy
- Processed copy
- Checksum
- Schema version
- License notes
- Retry behavior
- Validation
- No silent data loss

### Acceptance criteria

- Data downloads reproducibly
- Snapshots can be listed
- Schema validation runs
- Provenance visible
- Data source documented

### Suggested commit

`data: add versioned historical data ingestion`

---

## Milestone 12 — Player Projection Models

### Goal

Train position-specific probabilistic projections.

### Baselines

- Prior-year points
- Historical average
- Consensus projection
- Linear model

### Candidate models

- CatBoost
- LightGBM
- Quantile regression
- Ensembles

### Outputs

- Mean
- Median
- Floor
- Ceiling
- Volatility
- Games played
- Injury-adjusted projection

### Validation

- Time-based splits
- No future leakage
- Metrics by position
- Calibration
- Baseline comparison
- Artifact versioning

### Acceptance criteria

- Baselines reported
- Complex models selected only if better
- Artifacts include metadata
- Predictions reproducible

### Suggested commits

- `data: add player feature pipeline`
- `feat: train position-specific projection baselines`
- `feat: add calibrated player projection distributions`

---

## Milestone 13 — Injury and Games-Played Model

### Goal

Model availability risk without overstating certainty.

### Implement

- Expected games played
- Probability of missed games
- Injury status features
- Historical durability features
- Practice status updates
- Return-date uncertainty

### Acceptance criteria

- Model calibrated
- Uncertainty displayed
- Medical certainty not implied
- Historical leakage avoided

### Suggested commit

`feat: add player availability and games-played model`

---

## Milestone 14 — Weekly Lineup and Season Simulator

### Goal

Evaluate complete rosters.

### Implement

- Weekly outcome sampling
- Injury sampling
- Bye weeks
- Legal lineup optimization
- Bench substitution
- Head-to-head schedule
- Standings
- Playoffs
- Championship

### Requirements

- Configurable playoff rules
- Configurable schedule
- Reproducible seeds
- Lineup legality
- Correlation support where practical

### Acceptance criteria

- Legal lineups always used
- Same seed reproduces season
- Strong fixture rosters outperform weak fixtures over many simulations
- Championship probabilities are coherent

### Suggested commit

`feat: add weekly lineup and season simulation`

---

## Milestone 15 — Full Candidate Rollout Optimizer

### Goal

Choose picks using downstream draft and season outcomes.

### For each candidate

1. Add candidate.
2. Simulate remaining draft.
3. Simulate seasons.
4. Estimate expected points.
5. Estimate playoff probability.
6. Estimate championship probability.
7. Estimate downside.
8. Compare alternatives.

### Acceptance criteria

- Candidate order can differ from raw rank
- Output includes uncertainty
- Runtime configurable
- Cache invalidation correct
- Explanation references actual results

### Suggested commit

`feat: optimize live picks through draft and season rollouts`

---

## Milestone 16 — Rankings and Simulator UI

### Goal

Complete the three-mode product.

### Rankings

- Overall
- Position
- ESPN comparison
- Underdog comparison
- Sleepers
- Fades
- Tiers
- Floor/median/ceiling
- Availability by pick

### Simulator

- Mock drafts
- Strategy comparison
- Force candidate
- Compare players
- Lock manager picks
- Export results

### Acceptance criteria

- Sort/filter works
- Simulation settings visible
- Reproducible results
- Export works

### Suggested commit

`feat: add rankings and strategy simulator interfaces`

---

## Milestone 17 — Personalized Opponent Models

### Goal

Model managers individually.

### Features

- Position timing
- ADP adherence
- Favorite teams
- Favorite players
- Early QB
- TE strategy
- Position-run reactions
- Historical roster style
- Manual notes

### Requirements

- Graceful fallback
- Sparse-data uncertainty
- No overfitting
- Personalization disabled if it does not improve validation

### Acceptance criteria

- Personalized model must beat generalized baseline
- Uncertainty visible
- Priors documented

### Suggested commit

`feat: add optional manager-specific draft tendencies`

---

## Milestone 18 — ESPN Integration

### Goal

Reduce manual pick entry while preserving manual fallback.

### Investigate in order

1. Paste/import draft results
2. Accessible ESPN endpoints
3. Browser extension or DOM bridge
4. Other safe local methods

### Requirements

- No committed credentials
- Sync failure visible
- Conflict detection
- Manual correction
- Manual mode always works

### Acceptance criteria

- Imported picks map reliably
- Duplicates detected
- Conflicts reconciled
- Failure does not corrupt draft

### Suggested commit

`feat: add optional ESPN draft synchronization`

---

## Milestone 19 — Historical Backtesting

### Goal

Measure whether BayesianDraft beats simple baselines.

### Compare against

- ESPN ADP
- Underdog ADP
- Expert consensus
- Raw projected points
- VORP
- Static tiers
- Hero RB
- Zero RB
- WR-first
- Balanced
- Early QB
- Late QB

### Report

- Projection error
- Availability calibration
- Draft value
- Weekly points
- Playoff rate
- Championship rate
- Regret
- Runtime

### Acceptance criteria

- Time-based splits
- Snapshot preservation
- Reproducibility
- No future leakage
- Negative results documented honestly

### Suggested commit

`test: add rolling historical draft backtesting`

---

## Milestone 20 — Draft-Day Hardening

### Goal

Make the tool dependable for August 8.

### Complete

- Performance profiling
- Fast mode
- Deep mode
- Autosave
- Crash recovery
- Offline fallback
- Emergency recommendation mode
- Keyboard shortcuts
- Full mock-draft rehearsal
- Logging
- Backup export
- Data freshness warnings
- Sync fallback

### Acceptance criteria

- Full 12-team rehearsal completed
- Restart recovery works
- Manual mode works offline
- Recommendation latency meets target
- Backup rankings export exists
- Failure scenarios documented

### Suggested commit

`chore: harden BayesianDraft for live draft day`

---

## Milestone 21 — Post-Draft Decision Audit

### Goal

Evaluate decisions after the draft.

### Add

- Final roster report
- Recommendation history
- Actual choice versus recommendation
- Expected value gained/lost
- Draft grade
- Confidence
- Alternative scenarios
- Ex-ante versus hindsight analysis
- Exportable report

### Acceptance criteria

- Recommendation linked to snapshot and model version
- Hindsight separated from original information
- Report reproducible

### Suggested commit

`feat: add post-draft decision audit`

---

## 7. Priority Order

The draft is August 8, so the reliable live tool comes first.

Minimum viable draft-day product:

1. Repository foundation
2. Exact scoring
3. Draft-state engine
4. Data schemas
5. Baseline player snapshot
6. Baseline rankings
7. FastAPI
8. Manual draft UI
9. Explainable recommendations
10. Availability simulation
11. Save/restore/undo
12. Draft rehearsal

Advanced projections, personalized managers, and ESPN synchronization must not jeopardize the reliable manual workflow.

---

## 8. Testing Strategy

### Unit tests

- Scoring
- Draft order
- Roster legality
- Ranking formulas
- Recommendation components
- Availability calculations
- Serialization

### Integration tests

- API workflows
- Draft entry
- Undo/redo
- Save/load
- Frontend/backend interaction
- Snapshot loading

### Simulation tests

- Reproducibility
- Legal picks
- Legal lineups
- Probability sanity checks
- Cache correctness
- Runtime

### Backtesting

- Rolling historical seasons
- Time-based splits
- Baseline comparisons
- Calibration

### Failure tests

- Missing dataset
- Stale data
- Duplicate pick
- Invalid player ID
- Sync failure
- App restart
- Partial save
- Network unavailable

---

## 9. Documentation Requirements

Maintain:

- README.md
- CONTRIBUTING.md
- CHANGELOG.md
- docs/product-spec.md
- docs/architecture.md
- docs/modeling.md
- docs/data-schema.md
- docs/data-sources.md
- docs/scoring.md
- docs/draft-engine.md
- docs/simulation.md
- docs/testing.md
- docs/backtesting.md
- docs/api.md
- docs/model-registry.md
- docs/ui.md
- docs/roadmap.md
- docs/engineering-workflow.md
- docs/decisions/

Major decisions require ADRs.

Suggested ADRs:

- ADR-0001 Repository structure
- ADR-0002 DuckDB versus SQLite
- ADR-0003 React/Vite frontend
- ADR-0004 Manual-first ESPN integration
- ADR-0005 Simulation reproducibility
- ADR-0006 Data provenance strategy
- ADR-0007 Model registry approach

---

## 10. Initial Codex Handoff Task

Perform only the initial engineering handoff:

1. Inspect current repository.
2. Read all documents.
3. Identify what exists.
4. Create or update:
   - docs/engineering-workflow.md
   - docs/milestones.md
   - CONTRIBUTING.md
   - CHANGELOG.md
   - .github/pull_request_template.md
   - ADR template
5. Create Milestone 0 checklist.
6. Propose final repository structure.
7. Identify technical decisions requiring confirmation.
8. Provide Git initialization commands.
9. Do not create a GitHub remote until visibility is confirmed.
10. Do not begin Milestone 1.
11. End with:
   - Files created or modified
   - Open decisions
   - Milestone 0 checklist
   - Proposed first commit
   - Next Codex prompt

