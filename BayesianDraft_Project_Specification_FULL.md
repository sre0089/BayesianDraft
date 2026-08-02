# BayesianDraft — Complete Project Specification

## 1. Project Identity

**Project name:** BayesianDraft

**Tagline:** A probabilistic draft optimization engine.

**Core idea:** Most fantasy-football tools rank players. BayesianDraft ranks decisions.

BayesianDraft is a local-first, machine-learning-powered fantasy football draft assistant for a private 14-team ESPN redraft league. The system should not simply predict which players will score the most fantasy points. It should model the full draft state and recommend the available player who maximizes the expected strength of the user's eventual roster.

The project should be treated as a sequential decision-making system under uncertainty. Each recommendation should depend on:

- Current available players
- Every completed pick
- Every manager's roster
- Current round and pick
- Future user pick positions
- League scoring
- Starting-lineup requirements
- Positional scarcity
- Player projection distributions
- Injury and games-played uncertainty
- ESPN and Underdog market rankings
- Opponent draft behavior
- Probability a player remains available
- Expected downstream roster outcomes
- Simulated playoff and championship probability

The system should combine probabilistic forecasting, conditional probability models, simulation, and optimization. It should be explainable and reproducible rather than a black box.

---

## 2. Primary User

The primary user is **Primary User**.

The application should be optimized for the user's private league, while keeping the league configuration general enough to support other leagues later.

---

## 3. League Configuration

### Platform

- ESPN Fantasy Football

### League format

- 14 teams
- Redraft
- Snake draft
- Full PPR
- Trades enabled
- Standard waiver rules
- Draft date: August 8, 2026
- the user's draft position: 8

### Draft order

Always refer to managers by these names:

1. Manager 01
2. Manager 02
3. Manager 03
4. Manager 04
5. Manager 05
6. Manager 06
7. Manager 07
8. Primary User
9. Manager 09
10. Manager 10
11. Manager 11
12. Manager 12
13. Manager 13
14. Manager 14

### Snake picks for the user

- 1.08
- 2.07
- 3.08
- 4.07
- 5.08
- 6.07
- Continue the alternating pattern for all rounds

### Roster settings

Starting lineup:

- 1 QB
- 2 RB
- 2 WR
- 1 TE
- 1 FLEX
- 1 D/ST
- 1 K

Additional slots:

- 7 bench
- 1 IR

Initial FLEX assumption:

- RB / WR / TE

This must be configurable rather than hardcoded.

---

## 4. Exact Scoring Rules

All scoring must be configuration-driven and stored in a versioned league configuration file.

Recommended file:

`configs/leagues/espn_2026.yaml`

### Passing

- Passing yards: 0.04 points per yard
- Passing touchdown: 4 points
- Interception thrown: -2 points
- Passing two-point conversion: 2 points

### Rushing

- Rushing yards: 0.1 points per yard
- Rushing touchdown: 6 points
- Rushing two-point conversion: 2 points

### Receiving

- Receiving yards: 0.1 points per yard
- Reception: 1 point
- Receiving touchdown: 6 points
- Receiving two-point conversion: 2 points

### Kicking

- PAT made: 1 point
- Field goal missed: -1 point
- Field goal made, 0–39 yards: 3 points
- Field goal made, 40–49 yards: 4 points
- Field goal made, 50–59 yards: 5 points
- Field goal made, 60+ yards: 6 points

### D/ST touchdowns and returns

- Kickoff return touchdown: 6
- Punt return touchdown: 6
- Interception return touchdown: 6
- Fumble return touchdown: 6
- Blocked punt or field-goal return touchdown: 6
- Two-point return: 2
- One-point safety: 1

### D/ST events

- Sack: 1
- Blocked punt, PAT, or field goal: 2
- Interception: 2
- Fumble recovery: 2
- Safety: 2

### D/ST points allowed

- 0 points allowed: 5
- 1–6: 4
- 7–13: 3
- 14–17: 1
- 18–27: 0
- 28–34: -1
- 35–45: -3
- 46+: -5

### D/ST total yards allowed

- Under 100: 5
- 100–199: 3
- 200–299: 2
- 300–349: 0
- 350–399: -1
- 400–449: -3
- 450–499: -5
- 500–549: -6
- 550+: -7

---

## 5. Core Product Goal

BayesianDraft should answer:

> Given the current draft state, which available player should the user draft to maximize expected championship probability?

This is different from asking:

> Which available player is projected to score the most fantasy points?

The system should optimize a roster-level utility function.

A conceptual objective:

```text
DraftValue(player | state)
=
ExpectedUtility(after drafting player)
-
ExpectedUtility(best alternative)
```

Long-term utility should include:

- Expected weekly points
- Starting-lineup quality
- Bench depth
- Position strength
- Bye-week resilience
- Injury resilience
- Playoff probability
- Championship probability
- Downside risk
- Upside distribution

---

## 6. Product Modes

The final application should contain three major modes.

### 6.1 Draft Room

Used during the live ESPN draft.

Required capabilities:

- Show current round
- Show current overall pick
- Show manager on the clock
- Show number of picks until the user
- Show the user's next pick
- Show primary recommendation
- Show top alternative recommendations
- Show recommendation confidence
- Show explanation
- Show probability each player survives to the next the user pick
- Show available-player list
- Filter by position
- Search players
- Record a pick manually
- Default the selected manager to the manager on the clock
- Undo
- Redo
- Edit a prior pick
- Save draft state
- Restore draft state
- Autosave
- Track all manager rosters
- Show the user's roster
- Show position runs
- Show tier breaks
- Show stale-data warnings
- Show ESPN sync status if synchronization exists

The interface must remain usable without ESPN synchronization.

### 6.2 Rankings

Required views:

- Overall model ranking
- Position-specific rankings
- ESPN ADP comparison
- Underdog ADP comparison
- Sleeper ranking
- Fade ranking
- Tier assignments
- Projection floor
- Projection median
- Projection ceiling
- Injury and uncertainty indicators
- Expected availability at each the user pick
- Value over replacement
- Value above starter
- Roster-aware live rank

### 6.3 Simulator

Required capabilities:

- Run complete mock drafts
- Compare RB-first versus WR-first
- Compare Hero RB, Zero RB, balanced, elite-QB, and elite-TE strategies
- Force a player or position at 1.08
- Compare two candidate players
- Lock picks for particular managers
- Simulate remaining rounds
- Review resulting roster distributions
- Compare playoff probability
- Compare championship probability
- Export results
- Reproduce results from a seed

---

## 7. Signature Features

### 7.1 Draft-State Engine

The model understands the full evolving draft state rather than ranking players independently.

Inputs include:

- Completed picks
- Available players
- All manager rosters
- Round
- Overall pick
- Manager on the clock
- the user's future picks
- Position runs
- Tier depletion
- League scoring
- Roster requirements
- Current projections
- Market rankings

### 7.2 Player Availability Model

For every realistic candidate, estimate:

```text
P(player is available at the user's next pick | current draft state)
```

This is central to deciding whether to draft now or wait.

### 7.3 Monte Carlo Draft Simulator

For each candidate player:

1. Add candidate to the user's roster.
2. Simulate the rest of the draft many times.
3. Simulate resulting rosters.
4. Simulate weekly outcomes and seasons.
5. Estimate expected roster utility.
6. Estimate playoff probability.
7. Estimate championship probability.

### 7.4 Explainable Recommendation Engine

Every recommendation must answer:

1. Why this player?
2. Why this position?
3. Why now?
4. What is likely to remain later?
5. What happens if another candidate is selected?

Example:

> This WR is the final player in the current tier and has only a 9% chance of reaching 4.07. Two similarly projected RBs have greater than 60% probability of remaining available, so WR now preserves more future options.

### 7.5 Recommendation Tree

The tool should eventually display likely branches:

```text
Take Player A now
├── If Manager 08 takes Player B, target Player C next
├── If Manager 10 starts a QB run, delay QB
└── If Tier 3 RB collapses, pivot to Player D
```

### 7.6 Decision Audit

Record:

- Draft state
- Data snapshot
- Model version
- Simulation seed
- Candidate scores
- Recommendation
- User's actual selection
- Explanation shown at the time

Post-draft analysis must distinguish:

- Ex-ante recommendation quality
- Retrospective results
- Information known at draft time
- Information learned later

---

## 8. Machine Learning Architecture

The system should be a collection of specialized models rather than one monolithic model.

### 8.1 Player projection models

Build separate position-specific models for:

- QB
- RB
- WR
- TE
- K
- D/ST

Predict distributions, not only means.

Outputs:

- Expected season points
- Expected weekly points
- Floor
- Median
- Ceiling
- Volatility
- Games-played distribution
- Missed-game probability
- Upside probability
- Downside probability

Recommended initial model families:

- Linear baselines
- Historical average baselines
- CatBoost
- LightGBM
- Quantile regression
- Survival analysis
- Calibrated ensembles

### 8.2 Injury and availability model

Estimate:

- Probability of missing at least one game
- Expected games played
- Short-term injury risk
- Return timetable where known
- Uncertainty in return date
- Durability signal

The system must not claim medical certainty.

### 8.3 Market and ADP model

Track:

- ESPN ADP
- ESPN rank
- Underdog ADP
- Underdog rank
- Expert consensus rank if permitted
- ADP movement over time
- Expected selection range
- Position-specific ADP distribution

Separate player quality from draft cost.

### 8.4 Opponent selection model

Initially use league-wide probabilistic behavior.

Later personalize each manager using:

- Historical drafts
- Position timing
- Early-QB tendency
- TE strategy
- ADP adherence
- Favorite teams
- Favorite players
- Reaction to positional runs
- Current roster needs

Estimate:

```text
P(manager selects player | current state)
```

### 8.5 Availability model

Estimate:

```text
P(player survives to future pick | current state)
```

Inputs may include:

- ADP distribution
- Number of picks remaining
- Position demand
- Opponent roster needs
- Recent position run
- Manager tendencies
- Player news
- Tier scarcity

### 8.6 Draft optimizer

At each the user pick:

1. Generate a shortlist of realistic candidates.
2. Score each candidate with a fast heuristic.
3. Run seeded Monte Carlo rollouts for the top candidates.
4. Simulate complete remaining drafts.
5. Simulate seasons.
6. Estimate candidate utility.
7. Compare alternatives.
8. Return primary pick, backups, confidence, and explanation.

### 8.7 Season simulator

For every simulated week:

1. Sample player outcomes.
2. Apply injuries and missed-game probabilities.
3. Respect bye weeks.
4. Optimize legal starting lineups.
5. Score all teams.
6. Simulate head-to-head matchups.
7. Update standings.
8. Determine playoff qualification.
9. Simulate playoffs.
10. Record champion.

---

## 9. Player and Team Features

### Player identity and context

- Player ID
- Name
- Position
- NFL team
- Age
- Experience
- Height
- Weight
- Draft year
- Draft round
- Draft pick
- Contract status where available
- Depth-chart position
- Rookie status
- Bye week
- Injury status
- Injury history

### Passing features

- Attempts
- Completions
- Passing yards
- Passing touchdowns
- Interceptions
- Sack rate
- EPA per dropback
- Completion percentage over expected
- Air yards
- Deep attempts
- Red-zone attempts
- Goal-line usage
- Designed rushing attempts
- Scramble rate

### Rushing features

- Carries
- Rushing yards
- Rushing touchdowns
- Yards per carry
- Rush share
- Goal-line carries
- Red-zone carries
- Missed tackles forced
- Yards after contact
- Explosive rush rate
- Stuff rate
- Snap share
- Route participation
- Target share

### Receiving features

- Targets
- Receptions
- Receiving yards
- Receiving touchdowns
- Target share
- Route participation
- Routes run
- Yards per route run
- Air yards
- Air-yard share
- First-read target share
- Red-zone targets
- End-zone targets
- Yards after catch
- Average depth of target
- Drop rate
- Contested-target rate

### Weekly and season features

- Weekly fantasy points
- Season fantasy points
- Points per game
- Median weekly score
- Weekly standard deviation
- Floor games
- Ceiling games
- Games played
- Games started
- Games missed
- Position rank
- Consistency metrics
- Trend features

### Team context

- Offensive pace
- Plays per game
- Neutral pass rate
- Neutral rush rate
- Red-zone pass rate
- Red-zone rush rate
- Team scoring projection
- Offensive line quality
- Quarterback quality
- Coaching tendencies
- Strength of schedule
- Personnel changes
- Vacated targets
- Vacated carries
- Team injury context

### Schedule features

- Opponent
- Home/away
- Bye week
- Rest days
- Defensive matchup strength
- Weather where relevant and available
- Dome/outdoor
- Travel distance where useful

### Fantasy market features

- ESPN ADP
- Underdog ADP
- Expert consensus rank
- Projection consensus
- Position rank
- Tier
- ADP trend
- ADP volatility
- Draft percentage
- Best-ball exposure where permitted

---

## 10. Required Data Schemas

Create `docs/data-schema.md`.

Each schema should document:

- Purpose
- Primary key
- Foreign keys
- Required fields
- Optional fields
- Data types
- Validation rules
- Source fields
- Versioning
- Example record
- Known limitations

### 10.1 Player

Suggested fields:

- player_id
- full_name
- first_name
- last_name
- position
- nfl_team_id
- status
- age
- height
- weight
- experience
- rookie
- draft_year
- draft_round
- draft_pick
- bye_week
- source_player_ids
- valid_from
- valid_to

### 10.2 Team

- team_id
- abbreviation
- full_name
- conference
- division
- season
- coach
- stadium
- offensive_context
- defensive_context

### 10.3 Game

- game_id
- season
- week
- game_type
- date
- home_team_id
- away_team_id
- venue
- weather
- final_score
- source

### 10.4 WeeklyStats

- player_id
- game_id
- season
- week
- passing fields
- rushing fields
- receiving fields
- kicking fields
- return fields
- snaps
- routes
- fantasy_points
- source_snapshot_id

### 10.5 SeasonStats

- player_id
- season
- games
- starts
- aggregate counting stats
- per-game stats
- advanced efficiency
- fantasy_points
- volatility metrics

### 10.6 Projection

- projection_id
- player_id
- season
- week or season scope
- mean
- median
- lower_quantile
- upper_quantile
- games_played_mean
- model_version
- data_snapshot_id
- generated_at

### 10.7 ADP

- adp_id
- player_id
- source
- format
- scoring
- date
- overall_adp
- position_adp
- rank
- sample_size if available
- snapshot_id

### 10.8 Injury

- injury_id
- player_id
- report_date
- body_part
- status
- practice_participation
- expected_return
- source
- source_timestamp
- confidence

### 10.9 DraftPick

- draft_id
- overall_pick
- round
- round_pick
- manager_id
- player_id
- timestamp
- source
- manually_entered
- corrected
- prior_pick_reference

### 10.10 Roster

- manager_id
- player_ids
- starting_slots
- bench_slots
- ir_slots
- positional_counts
- vacancies
- strength_summary

### 10.11 DraftState

- draft_id
- current_pick
- current_round
- manager_on_clock
- completed_picks
- available_player_ids
- rosters
- user_future_picks
- undo_stack
- redo_stack
- model_version
- data_snapshot_id
- simulation_seed
- updated_at

### 10.12 Recommendation

- recommendation_id
- draft_state_id
- candidate_player_id
- rank
- expected_utility
- playoff_probability
- championship_probability
- next_pick_availability
- confidence
- explanation_components
- model_version
- simulation_seed
- generated_at

### 10.13 SimulationResult

- simulation_id
- draft_state_id
- candidate_player_id
- simulation_count
- seed
- expected_roster_value
- playoff_probability
- championship_probability
- downside_metric
- runtime
- model_versions
- snapshot_id

### 10.14 LeagueConfig

- platform
- season
- team_count
- draft_type
- draft_order
- roster_slots
- scoring
- waiver_rules
- trade_rules
- playoff_rules
- flex_eligibility
- user_manager_id

### 10.15 DataSnapshot

- snapshot_id
- dataset_name
- source
- retrieval_timestamp
- season
- checksum
- raw_path
- processed_path
- schema_version
- preprocessing_version
- license_notes
- source_url
- row_count

---

## 11. Data Sources and Governance

Create `docs/data-sources.md`.

### Primary source categories

#### NFL performance data

Prefer:

- nflverse
- Official NFL/team data where accessible and permitted
- Documented public datasets

Expected content:

- Play-by-play
- Weekly statistics
- Rosters
- Schedules
- Participation
- Snap counts
- Advanced usage features
- Team context

#### Market data

Potential sources:

- ESPN rankings and ADP
- Underdog ADP
- FantasyPros consensus rankings or projections if access and terms permit

#### Context data

- Injury reports
- Practice reports
- Depth charts
- Transactions
- Suspensions
- Coaching changes
- Offensive-line changes
- Team projections

### Governance requirements

Every dataset must include:

- Source name
- Source URL
- Retrieval timestamp
- Season
- Snapshot ID
- File checksum
- Schema version
- Preprocessing version
- Licensing or usage notes
- Raw immutable copy
- Processed derived copy
- Known limitations

Do not silently scrape or use undocumented proprietary data.

Do not commit large raw datasets to normal Git.

Use a reproducible download script and a data manifest.

---

## 12. Validation and Backtesting

Create `docs/backtesting.md` and `docs/testing.md`.

### Time-based validation

For a historical season:

- Train only on information available before that season's draft.
- Use ADP as it existed before that draft.
- Use injuries and depth-chart information known at the time.
- Evaluate against actual future outcomes.

Never use random train/test splits across time-sensitive player seasons when that would leak future information.

### Projection metrics

- MAE
- RMSE
- Pinball loss
- Calibration error
- Prediction interval coverage
- Games-played prediction error
- Position-specific error
- Rank correlation

### Availability metrics

- Brier score
- Log loss
- Calibration curves
- Availability prediction by pick distance
- Error by player tier
- Error by position

### Draft and roster metrics

- Value gained versus ADP
- Starter points
- Total roster points
- Bench utility
- Weekly team points
- Playoff rate
- Championship rate
- Draft regret
- Expected utility
- Runtime

### Baselines

Compare against:

- ESPN ADP
- Underdog ADP
- Expert consensus
- Projected points
- VORP
- Static tiers
- Simple roster-need heuristic
- Hero RB
- Zero RB
- WR-first
- Balanced
- Early-QB
- Late-QB

Retain complex models only when they beat simpler baselines out of sample.

---

## 13. User Interface Requirements

Create `docs/ui.md`.

### Draft Room layout

#### Top bar

- Current round
- Current overall pick
- Manager on the clock
- the user's pick position
- Picks until the user
- Next the user pick
- Draft sync status
- Data freshness

#### Available players panel

Columns:

- Rank
- Player
- Position
- Team
- Model score
- ESPN ADP
- Underdog ADP
- Tier
- Probability available next pick
- Injury flag

Controls:

- Search
- Position filters
- Tier filters
- Hide drafted
- Sort
- Quick draft action

#### Recommendation panel

Show:

- Primary player
- Position
- Team
- Model rank
- Expected utility
- Championship probability impact
- Availability next pick
- Confidence
- Main explanation
- Top alternatives
- Emergency backup

#### Draft board panel

Show every manager and pick by round.

Managers must be named exactly as configured.

#### Roster panel

Show:

- Starting slots
- Bench
- IR
- Empty positions
- Excess depth
- Position grades
- Bye-week overlap
- Weak spots

### Keyboard shortcuts

Recommended:

- Up/down: navigate
- Enter: open player
- D: mark drafted
- U: undo
- R: redo
- Slash: search
- Q: QB
- B: RB
- W: WR
- T: TE
- K: K
- S: D/ST
- 1–4: select recommendation

### Low-time emergency mode

When the user's clock is nearly expired:

- Show only primary pick
- Show backup pick
- Show critical availability warning
- Reduce detail
- Keep confirmation fast

---

## 14. Local-First Architecture

Preferred stack:

### Frontend

- React
- TypeScript
- Vite
- Vitest
- React Testing Library

### Backend

- Python 3.12
- FastAPI
- Pydantic
- Polars
- DuckDB or SQLite
- pytest
- Ruff
- mypy where practical

### Modeling

- scikit-learn
- CatBoost
- LightGBM
- Optuna
- MLflow only if justified

### Storage

Local storage should support:

- League configuration
- Draft sessions
- Pick history
- Player snapshots
- Rankings
- Model artifacts
- Simulation results
- Recommendation audit logs

The application must continue to function in manual mode without a remote server.

---

## 15. Proposed Repository Structure

```text
BayesianDraft/
├── apps/
│   ├── api/
│   │   ├── src/
│   │   └── tests/
│   └── web/
│       ├── src/
│       └── tests/
├── bayesiandraft/
│   ├── config/
│   ├── domain/
│   ├── scoring/
│   ├── draft/
│   ├── rankings/
│   ├── recommendations/
│   ├── simulation/
│   ├── projections/
│   ├── opponents/
│   ├── season/
│   ├── data/
│   └── audit/
├── configs/
│   └── leagues/
│       └── espn_2026.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── snapshots/
│   ├── manifests/
│   └── fixtures/
├── models/
│   ├── artifacts/
│   ├── metadata/
│   └── registry/
├── notebooks/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── simulation/
│   └── backtesting/
├── docs/
│   ├── product-spec.md
│   ├── architecture.md
│   ├── modeling.md
│   ├── data-schema.md
│   ├── data-sources.md
│   ├── scoring.md
│   ├── draft-engine.md
│   ├── simulation.md
│   ├── backtesting.md
│   ├── testing.md
│   ├── api.md
│   ├── model-registry.md
│   ├── ui.md
│   ├── roadmap.md
│   ├── engineering-workflow.md
│   └── decisions/
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── .env.example
├── .editorconfig
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
└── package.json
```

Codex may improve this structure, but it must explain material deviations.

---

## 16. Engineering Principles

- Prefer correctness over premature complexity.
- Prefer reproducible behavior.
- Use seeded simulations.
- Keep scoring pure and heavily tested.
- Keep league settings configurable.
- Separate domain logic from UI.
- Separate data ingestion from modeling.
- Separate modeling from recommendation orchestration.
- Do not hide uncertainty.
- Do not make unsupported claims.
- Prevent historical leakage.
- Version all model artifacts.
- Version all data snapshots.
- Keep manual fallback for critical live-draft behavior.
- Build complete vertical slices.
- Keep the repository runnable after each milestone.
- Make small coherent commits.
- Document important decisions with ADRs.

---

## 17. Initial Codex Task

When this document is first provided to Codex:

1. Read the complete specification.
2. Inspect the repository.
3. Do not immediately build the full application.
4. Create or update:
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
5. Identify unresolved assumptions.
6. Identify legal or licensing risks.
7. Propose the final repository structure.
8. Propose ADRs.
9. Wait before implementing major production features.
10. Summarize files created, decisions made, and open questions.
