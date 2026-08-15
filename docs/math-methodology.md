# Math And Methodology

BayesianDraft ranks draft decisions, not just players.

That distinction matters. A player can be great in a vacuum and still be the wrong pick if your roster is already full at that position, if a similar player is likely to come back later, or if another position is about to dry up. The engine tries to combine those draft-day tradeoffs into one recommendation and then show the pieces that caused it.

This document explains the current engine in practical terms. The implementation is still a transparent baseline: mostly projections, rankings, roster rules, ADP, and seeded simulations. More complicated Bayesian or machine-learning models should only replace these pieces when they beat the simpler version in validation.

## The Big Idea

For every available player, BayesianDraft asks:

- How good is this player compared with a normal starter or replacement player?
- Does this player fill something my roster still needs?
- Is this position about to run out of strong options?
- Is the market letting this player fall farther than expected?
- If I skip this player, how likely are they to survive to my next pick?
- What do saved simulated drafts suggest I can still get later?
- Is this an awkward pick for the draft phase, like taking a kicker too early?

The recommendation is the player with the best combined answer to those questions.

## Draft State

The engine keeps a live draft state:

- the players still available
- every manager's roster
- the current pick number
- the current round
- which manager is on the clock
- the user's next pick

In a snake draft, the order reverses each round. In a 14-team league, pick 1 goes to Manager 01, pick 14 goes to Manager 14, pick 15 also goes to Manager 14, and pick 28 goes back to Manager 01.

When you record a pick, the update is simple:

1. Remove that player from the available pool.
2. Add the player to the manager who was on the clock.
3. Move the draft clock to the next pick.
4. Recalculate rankings, roster needs, recommendations, and path-bank context.

This is why the TUI can update after every pick.

## Player Projections

The starting point is a player snapshot. Each player can have:

- projected fantasy points
- floor and ceiling estimates
- position
- team
- bye week
- ADP
- optional stat projections

The main projection is the player's expected season points. In plain English, this means:

> If this season were played many times, what would this player average?

If a running back has a projection of 300 points, the engine treats 300 as the center of that player's season outcome. Floor and ceiling give the simulator a rough idea of uncertainty, but the current ranking baseline mostly uses the main projection.

## Scoring

When stat projections are available, fantasy points are calculated from league scoring rules.

For example, if a league gives:

- 1 point per reception
- 0.1 points per receiving yard
- 6 points per receiving touchdown

and a wide receiver is projected for:

- 90 catches
- 1,200 receiving yards
- 8 touchdowns

then the projected receiving score is:

```text
90 catches * 1.0
+ 1200 yards * 0.1
+ 8 touchdowns * 6.0
= 90 + 120 + 48
= 258 points
```

The same idea applies to passing, rushing, kicking, and defense settings. The important part is that scoring is configuration-driven, so the same league rules are used for rankings, simulations, exports, and tests.

## Replacement Value

Raw points are useful, but they can be misleading across positions.

A top quarterback may score more points than a top running back, but if many quarterbacks score well, the quarterback may not be as valuable relative to the other options at that position.

BayesianDraft uses value over replacement, or VORP:

```text
VORP = player projected points - replacement player projected points
```

Example:

- RB A projects for 300 points.
- The replacement-level RB projects for 210 points.
- RB A has 90 VORP.

That means RB A is worth about 90 points more than a normal fallback RB.

Another example:

- QB A projects for 340 points.
- The replacement-level QB projects for 300 points.
- QB A has 40 VORP.

Even though QB A scores more raw points than RB A, RB A is more valuable in this simplified comparison because the RB advantage over replacement is larger.

## Starter Value

The engine also tracks value above starter.

This asks:

> How far above a normal starting-caliber player is this player?

This helps separate elite players from players who are merely above replacement. It is especially useful in early rounds, where the difference between a true tier-one player and a normal starter matters more.

## ADP And Market Value

ADP means average draft position. It is the market's rough expectation of where a player usually gets picked.

BayesianDraft compares its own ranking to ADP:

```text
ADP delta = ADP - BayesianDraft rank
```

Positive ADP delta means the player may be a value.

Example:

- The model ranks a player 25th.
- The player's ADP is 40.
- ADP delta is +15.

That means the model likes the player 15 picks earlier than the market usually takes them.

Negative ADP delta means the player may be expensive.

Example:

- The model ranks a player 40th.
- The player's ADP is 25.
- ADP delta is -15.

That means the market is usually taking the player earlier than the model would.

ADP is not treated as truth. It is just a signal about price.

## Tiers

Tiers group players when their projections are close together.

For example, suppose the available wide receivers look like this:

```text
WR 1: 285 points
WR 2: 283 points
WR 3: 281 points
WR 4: 260 points
```

The first three are close enough that they probably belong in the same tier. WR 4 is a bigger drop. If only one player remains in a tier, the engine becomes more urgent about that position.

This is what tier pressure means:

> If I skip this position now, will the next option be meaningfully worse?

## Roster Need

Roster need is the part of the score that protects you from building an incomplete or lopsided roster.

If your league requires:

- 1 QB
- 2 RB
- 2 WR
- 1 TE
- 1 FLEX
- 1 DST
- 1 K

and your roster has no running backs, then RB gets a need boost. If you already have two RBs but your Flex is still open, RB can still receive some need credit because RB is Flex-eligible.

Need is draft-phase aware:

- Early draft: need matters, but the engine still prioritizes elite value.
- Middle draft: need and value are more balanced.
- Late draft: need gets stronger so the roster actually gets completed.

This keeps the engine from blindly filling positions early while still making sure the roster is not incomplete at the end.

## Availability

Availability means:

> If I do not take this player now, what is the chance they are still there at my next pick?

The engine estimates this through seeded simulations.

Here is the simple version:

1. Simulate the picks between now and your next pick many times.
2. In each simulated path, check whether the player survives.
3. Count how often the player is still available.

Example:

- The engine runs 100 simulated paths.
- A player is still available at your next pick in 18 of them.
- Estimated availability is 18%.

That does not mean the real draft has an exact 18% probability. It means that under the current simulator assumptions, this player usually does not make it back.

This is similar to expected value for dice. If each die roll has a 1 out of 6 chance, the average roll is:

```text
1/6 * 1
+ 1/6 * 2
+ 1/6 * 3
+ 1/6 * 4
+ 1/6 * 5
+ 1/6 * 6
= 3.5
```

The draft simulator uses the same kind of averaging idea, but over possible draft paths instead of die rolls.

## Path Banks

A path bank is a saved set of simulated drafts.

Instead of running thousands of simulations during the draft, BayesianDraft can build a large bank before draft time and quickly look up similar situations while you are drafting.

The path bank helps answer questions like:

- If I take RB now, what kind of WR usually comes back later?
- If I wait on QB, how much value do I usually lose?
- Which position gets more expensive to skip?
- What player is commonly still available at my next pick?

This produces the quick direction shown in the TUI.

For example:

```text
Opportunity: RB +8 | WR +2 | QB +14 | TE +1
```

This would mean the saved paths think waiting on QB is more costly than waiting on WR or TE. It does not automatically force a QB pick, but it pushes the recommendation in that direction if the player value also supports it.

## Recommendation Score

The current score is additive. That means each player gets points from several understandable pieces:

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

The TUI shows this as a compact breakdown:

```text
need +24.5 | value +90.2 | tier +24.0 | opp +8.4 | risk +17.6 | market +1.2 | penalty 0.0
```

How to read that:

- `value`: how much the player adds over replacement.
- `need`: how much the player helps fill your roster, including Flex.
- `tier`: how strong the player's tier is.
- `drop`: whether the position is close to a tier cliff.
- `opp`: opportunity cost from the path bank.
- `risk`: how unlikely the player is to reach your next pick.
- `market`: whether the player is cheaper than the model thinks they should be.
- `penalty`: draft timing or roster construction concerns.

The final recommendation is the available player with the best total score for the current draft state.

## A Simple Recommendation Example

Imagine it is your pick and the top candidates are:

```text
Player        Pos   Value   Need   Tier   Risk   Market   Total
RB A          RB     90      25     20     15      2       152
QB A          QB     55      10     18     30      8       121
WR A          WR     70      20     15     10      5       120
```

RB A wins because the engine sees a strong mix of raw value, roster need, and tier strength.

But if RBs are still likely to be available later and QBs are about to collapse, the path-bank opportunity cost could change the picture:

```text
Player        Pos   Base Score   Opportunity Cost   New Total
RB A          RB       152              +1             153
QB A          QB       121             +35             156
WR A          WR       120              +4             124
```

Now QB A can become the better strategic pick, even if RB A looked better from static rankings alone.

This is the kind of situation the path bank is meant to catch.

## Opponent Behavior

The current opponent model is intentionally lightweight.

It looks at what each manager has drafted so far and uses that to slightly adjust future simulated picks. If a manager has already taken several wide receivers, the simulator can reduce the urgency for that manager to take another one. If a manager has no quarterback later in the draft, quarterback becomes more likely.

This is not a fully learned opponent model yet. It is a transparent baseline that makes simulated drafts more realistic than simply picking the highest-ranked available player every time.

## Candidate Rollouts

The normal recommendation answers:

> Who is the best pick right now?

Candidate rollout asks a deeper question:

> If I take this player now, what does my roster usually look like by the end of the draft?

The process is:

1. Pick a candidate player.
2. Pretend you draft that player.
3. Simulate the rest of the draft many times.
4. Score your final roster in each simulation.
5. Average those outcomes.
6. Repeat for other candidate players.

This is slower than the normal recommendation, but it better captures future effects. It is useful when two players are close and you want to compare likely roster paths.

## Lineup And Season Simulation

For a completed roster, the season simulator estimates how strong the team is by choosing the best legal weekly lineup.

For example, if your roster has four running backs but only two RB slots and one Flex, the simulator does not score all four as starters. It chooses the best legal combination based on the league's lineup rules.

At the moment, this estimates roster scoring strength. It does not yet fully model head-to-head schedules, playoff brackets, or championship odds.

## Backtesting And Calibration

The engine should become more complicated only when testing proves that the added complexity helps.

The main validation ideas are:

- Projection error: how far projected points were from real points.
- Availability accuracy: whether players actually survived to later picks as often as predicted.
- Draft regret: how much value was lost by taking one player instead of another.
- Time-aware testing: historical drafts must only use information that existed before that draft happened.

For example, if the engine says a player has a 20% chance to reach your next pick, then across many similar cases, that player should actually survive about 20% of the time. If that does not happen, the availability model needs calibration.

## Current Limits

- Fixture data is synthetic and exists to test the system, not to produce real draft advice.
- Baseline rankings depend on simple replacement assumptions.
- Recommendation terms are heuristic and additive.
- Availability simulation is reproducible, but not yet calibrated against many real drafts.
- Opponent profiles only use observed picks in the current draft.
- Season simulation estimates roster points, not head-to-head standings or playoff odds.
- ESPN integration is dry-run only.

## Direction

The long-term goal is a more validated decision engine, not just a more complicated one.

The next modeling improvements should be:

1. Use reproducible projection, ADP, injury, and depth-chart snapshots.
2. Validate projection ranges against historical seasons.
3. Calibrate availability estimates against real draft rooms.
4. Learn opponent tendencies from user-provided draft history.
5. Compare candidate picks by final roster outcomes, then eventually playoff and championship probability.
6. Keep every model tied to data snapshots, validation metrics, and reproducible seeds.

The goal is better draft decisions with explanations that can still be audited later.
