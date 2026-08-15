# Math And Methodology

BayesianDraft ranks draft decisions, not just players.

A player can be great and still be the wrong pick if your roster already has that position covered, if a similar player should come back later, or if another position is about to run out. The engine combines those draft-day tradeoffs into one recommendation and shows the pieces behind it.

The current engine is intentionally simple and explainable. It uses projections, roster rules, ADP, tiers, availability estimates, and saved simulations. More advanced modeling should only replace these pieces when testing proves it makes better recommendations.

## The Main Question

For each available player, BayesianDraft asks whether the player is valuable, fills a roster need, sits near a tier drop, is cheaper than ADP, is unlikely to come back, or creates a bad timing problem. The best recommendation is the player with the strongest combined answer.

## Draft State

The engine tracks the live draft board: available players, every manager's roster, the current pick, the manager on clock, and the user's next pick.

In a snake draft, the order reverses each round. For example, in a 14-team league, Manager 14 picks at 14 and 15 because the second round runs backward.

After every recorded pick, BayesianDraft removes that player from the board, adds them to the correct roster, advances the clock, and recalculates the recommendation.

## Projections And Scoring

Each player starts from a snapshot with projected points, position, team, bye, ADP, and optional floor/ceiling or stat projections.

If stat projections are available, points come from the league scoring rules. For example, in full PPR:

```text
90 catches * 1.0
+ 1200 receiving yards * 0.1
+ 8 receiving touchdowns * 6.0
= 258 points
```

That same scoring config is used across rankings, simulations, exports, and tests.

## VORP

VORP means value over replacement.

```text
VORP = player projected points - replacement player projected points
```

This helps compare players across positions. A quarterback might score more raw points than a running back, but that does not automatically make the quarterback more valuable.

Example:

```text
RB A: 300 projected points - 210 replacement RB points = 90 VORP
QB A: 340 projected points - 300 replacement QB points = 40 VORP
```

QB A scores more total points, but RB A creates more value compared with the players you could replace him with.

## ADP And Market Value

ADP is average draft position, or roughly where the market usually takes a player.

```text
ADP delta = ADP - BayesianDraft rank
```

Positive ADP delta usually means value:

```text
Model rank: 25
ADP:        40
Delta:     +15
```

The model likes that player 15 picks earlier than the market. Negative ADP delta means the market is taking the player earlier than the model would. ADP is not treated as truth; it is just a price signal.

## Tiers

Tiers group players who are close in projected value.

```text
WR 1: 285 points
WR 2: 283 points
WR 3: 281 points
WR 4: 260 points
```

The first three are probably one tier. WR 4 is a drop. If only one player remains in a strong tier, the engine gives that position more urgency. Tier pressure means: if I skip this position now, will the next option be meaningfully worse?

## Roster Need

Roster need keeps the model from building an incomplete team.

If your roster needs 2 RBs and you have none, RB gets a need boost. If you already have two RBs but Flex is still open, RB can still get some need credit because RB is Flex-eligible.

Need changes by draft phase. Early on, value still matters most. In the middle, need and value are balanced. Late in the draft, need becomes stronger so the roster gets completed.

## Availability

Availability estimates whether a player can make it back to your next pick.

The engine simulates the picks between now and your next pick, then counts how often the player survives:

```text
100 simulated paths
18 paths where the player is still available
= 18% estimated availability
```

This is like expected value for dice. Since each die roll has a 1/6 chance:

```text
1/6 * 1 + 1/6 * 2 + 1/6 * 3 + 1/6 * 4 + 1/6 * 5 + 1/6 * 6 = 3.5
```

The draft simulator uses the same averaging idea, but over possible draft paths instead of die rolls.

## Path Banks

A path bank is a saved set of simulated drafts built before draft time. The TUI can use it quickly during the draft instead of rerunning thousands of simulations after every pick.

It helps answer things like "if I wait on QB, how much value do I usually lose?" or "which position gets more expensive to skip?"

```text
Opportunity: RB +8 | WR +2 | QB +14 | TE +1
```

That means the saved paths think waiting on QB is more costly than waiting on WR or TE. It does not force a QB pick, but it pushes the recommendation that way if player value supports it.

## Recommendation Score

Each available player gets a score from understandable pieces:

```text
Total score =
  player value
+ roster need
+ tier quality
+ tier drop pressure
+ opportunity cost
+ next-pick risk
+ market value
- penalties
```

The TUI shows the pieces like this:

```text
need +24.5 | value +90.2 | tier +24.0 | opp +8.4 | risk +17.6 | market +1.2 | penalty 0.0
```

Quick translation: `value` is points over replacement, `need` is roster fit, `tier` and `drop` cover positional scarcity, `opp` is path-bank cost of waiting, `risk` is chance the player does not come back, `market` is ADP value, and `penalty` is timing or roster-construction concern.

## Example Decision

Without path-bank context, the engine might see:

```text
Player   Pos   Value   Need   Tier   Risk   Market   Total
RB A     RB     90      25     20     15      2       152
QB A     QB     55      10     18     30      8       121
WR A     WR     70      20     15     10      5       120
```

RB A wins because the mix of value, need, and tier strength is best.

But if saved paths show QBs dry up before your next pick, opportunity cost can change the answer:

```text
Player   Base Score   Opportunity Cost   New Total
RB A        152              +1             153
QB A        121             +35             156
WR A        120              +4             124
```

Now QB A can become the better strategic pick. This is the type of decision the path bank is meant to catch.

## Simulations

Simulated drafts do not simply take the top ranked player every time. They include roster needs, ADP, seeded randomness, and basic opponent behavior.

Opponent behavior is still lightweight. If a manager already has several wide receivers, the simulator can reduce that manager's need for another WR. If a manager still has no quarterback later in the draft, QB becomes more likely.

Candidate rollouts are the slower version of this idea. They ask:

> If I take this player now, what does my final roster usually look like?

The engine pretends you took a candidate, simulates the rest of the draft many times, scores the final rosters, and averages the outcomes.

## Limits And Direction

The current limits are straightforward: fixture data is synthetic, replacement assumptions are simple, recommendation terms are heuristic, availability is not fully calibrated against real drafts yet, opponent profiles only use observed picks, and season simulation estimates roster strength rather than playoff odds.

The long-term goal is not more complexity for its own sake. It is better draft decisions that are still easy to explain. The next modeling improvements should focus on better data snapshots, calibrated availability estimates, stronger opponent behavior, and candidate comparisons based on final roster outcomes.
