# Math And Methodology

BayesianDraft is designed to rank draft decisions, not only players. The engine combines player value, roster construction, draft position, market cost, availability estimates, and simulated downstream outcomes into recommendations that can be explained and reproduced.

This document describes the current methodology and the intended direction of the model. The present implementation uses transparent deterministic and seeded baseline models. More advanced Bayesian and machine-learning components should replace these baselines only after they beat them in historical validation.

## Notation

The notation table uses HTML subscripts and Unicode symbols so it renders cleanly in Markdown tables.

| Symbol | Meaning |
| --- | --- |
| P | Set of all players in the current player pool |
| A<sub>t</sub> ⊆ P | Players available before pick t |
| M | Set of draft managers |
| m<sub>u</sub> ∈ M | Configured user manager |
| R<sub>m</sub>(t) | Roster for manager m before pick t |
| x<sub>p</sub> | Feature vector for player p |
| μ<sub>p</sub> | Projected mean season points for player p |
| q<sub>p,α</sub> | Projection quantile for player p at quantile α |
| π<sub>p</sub> | Market cost for player p, represented by overall ADP |
| s<sub>p</sub> | Engine score for player p |
| S | Number of simulation samples |

The draft state at pick $t$ is:

$$
D_t = \left(A_t, \{R_m(t)\}_{m \in M}, t, \mathrm{slot}(t)\right)
$$

where $\mathrm{slot}(t)$ maps an overall pick to round, round pick, and manager on clock.

## Draft State And Snake Order

For a league with $N$ managers, the round for overall pick $t$ is:

$$
r(t) = \left\lfloor \frac{t - 1}{N} \right\rfloor + 1
$$

The zero-based index within the round is:

$$
i(t) = (t - 1) \bmod N
$$

The manager index is:

$$
j(t) =
\begin{cases}
i(t), & r(t)\ \mathrm{is\ odd} \\
N - i(t) - 1, & r(t)\ \mathrm{is\ even}
\end{cases}
$$

This makes draft transitions deterministic. Recording a pick removes the player from $A_t$, appends the pick to history, and updates the selected manager's roster:

$$
A_{t+1} = A_t \setminus \{p\}
$$

$$
R_{m}(t+1) =
\begin{cases}
R_m(t) \cup \{p\}, & m = \mathrm{manager}(t) \\
R_m(t), & \mathrm{otherwise}
\end{cases}
$$

## Player Projection Model

The current baseline starts from normalized player projection records. Each player has a mean projection, optional floor and ceiling values, and games-played assumptions.

For a player $p$, the baseline season projection is:

$$
\mu_p = E[Y_p]
$$

where $Y_p$ is season fantasy points under the configured scoring rules.

Weekly sampling uses a simple distributional approximation derived from season-level projection intervals. If floor and ceiling are available, the weekly standard deviation is approximated from the spread:

$$
\sigma_{p,w} \approx \frac{q_{p,0.85} - q_{p,0.15}}{2z_{0.85}\sqrt{G_p}}
$$

where $G_p$ is expected games played and $z_{0.85}$ is the standard normal quantile. Samples are floored at zero:

$$
Y_{p,w}^{(s)} = \max \left(0, \mathcal{N}(\mu_{p,w}, \sigma_{p,w}^2)\right)
$$

This is intentionally simple. It gives the simulator uncertainty-aware behavior without pretending the baseline is already calibrated.

## Scoring

Fantasy points are computed from stat-line components and league scoring weights. For an offensive player:

$$
\mathrm{FP}(p) =
\sum_{k \in K_{\mathrm{pass}}} w_k z_{p,k}
+ \sum_{k \in K_{\mathrm{rush}}} w_k z_{p,k}
+ \sum_{k \in K_{\mathrm{rec}}} w_k z_{p,k}
$$

where $z_{p,k}$ is a stat value and $w_k$ is the configured fantasy scoring weight.

Kicker and defense/special teams scoring use the same weighted-stat pattern plus bucketed rules. For bucketed scoring, the active bucket is selected by the observed value:

$$
\mathrm{bucket}(v) = b \quad \mathrm{such\ that} \quad l_b \le v \le u_b
$$

The implementation keeps scoring pure and configuration-driven so projections, simulations, and tests all use the same league rules.

## Replacement Value And Rankings

The ranking baseline converts projected points into value over replacement. For player $p$ at position $c$:

$$
\mathrm{VORP}_p = \mu_p - \mu_{\mathrm{replacement}(c)}
$$

where $\mu_{\mathrm{replacement}(c)}$ is the projected point total for the configured replacement rank at that position.

Value above starter is:

$$
\mathrm{VAS}_p = \mu_p - \mu_{\mathrm{starter}(c)}
$$

where $\mu_{\mathrm{starter}(c)}$ is the starter-threshold projection for the position.

Market value is represented by ADP delta:

$$
\Delta_{\mathrm{ADP},p} = \pi_p - \mathrm{rank}_p
$$

A positive $\Delta_{\mathrm{ADP},p}$ means the model ranks the player earlier than the market price. A negative value means the player is expensive relative to the model.

The baseline overall ranking is sorted by:

1. $\mathrm{VORP}_p$, descending.
2. $\mu_p$, descending.
3. Player name, ascending for deterministic ties.

## Tiering

Tiers are assigned within each position based on projection gaps. If players $p_i$ and $p_{i-1}$ are adjacent in positional rank, a new tier begins when:

$$
\mu_{p_{i-1}} - \mu_{p_i} \ge \tau_c
$$

where $\tau_c$ is the configured tier-gap threshold for position $c$.

Tiers help the recommendation engine distinguish a replaceable rank difference from a real drop-off in the player pool.

## Recommendation Score

The current baseline recommendation score is additive and explainable:

$$
s_p =
\mathrm{VORP}_p
+ N(p, R_{m_u})
+ T(p)
+ V(p)
- C(p, R_{m_u}, t)
$$

where:

| Term | Meaning |
| --- | --- |
| VORP<sub>p</sub> | Player value over replacement |
| N(p, R<sub>mᵤ</sub>) | Roster need boost |
| T(p) | Tier-quality boost |
| V(p) | Market value boost from ADP delta |
| C(p, R<sub>mᵤ</sub>, t) | Draft timing and roster-construction penalty |

The need term rewards filling starter requirements:

$$
N(p, R_{m_u}) =
\begin{cases}
\lambda_c, & \mathrm{count}(R_{m_u}, c_p) < \mathrm{starterTarget}(c_p) \\
0, & \mathrm{otherwise}
\end{cases}
$$

The market term rewards players the model likes more than the market:

$$
V(p) = \lambda_{\mathrm{adp}} \cdot \max(\Delta_{\mathrm{ADP},p}, 0)
$$

The timing penalty currently discourages early kicker and defense selections and duplicate low-flexibility roster construction:

$$
C(p, R_{m_u}, t) =
C_{\mathrm{early}}(p,t) + C_{\mathrm{duplicate}}(p, R_{m_u})
$$

This structure is deliberately readable. Every recommendation can be decomposed into value, need, tier, market, and penalty components.

## Availability

Availability estimates answer: "What is the chance this player reaches a future target pick?"

For player $p$ and target pick $k > t$, the desired probability is:

$$
P(p \in A_k \mid D_t)
$$

The baseline approximates this with seeded draft simulation:

$$
\widehat{P}(p \in A_k \mid D_t) =
\frac{1}{S}\sum_{s=1}^{S} \mathbb{1}\left[p \in A_k^{(s)}\right]
$$

Each simulated path drafts players according to a heuristic utility:

$$
u_{m,p} =
\alpha \cdot \mathrm{rankValue}_p
+ \beta \cdot \mathrm{need}_{m,p}
+ \gamma \cdot \mathrm{market}_{p}
+ \delta \cdot \mathrm{opponentPreference}_{m,p}
+ \epsilon_{s,p}
$$

where $\epsilon_{s,p}$ is seeded randomness. The same seed and state produce the same estimate.

The current model is not calibrated probability yet. It is a reproducible baseline for comparing decisions and detecting obvious availability tradeoffs.

## Opponent Profiles

Opponent behavior is represented by lightweight profiles inferred from current draft behavior. For manager $m$, the position preference for position $c$ is smoothed:

$$
\theta_{m,c} =
\frac{n_{m,c} + a_c}{\sum_{c'} n_{m,c'} + \sum_{c'} a_{c'}}
$$

where $n_{m,c}$ is the count of drafted players at position $c$, and $a_c$ is a prior smoothing weight.

The simulator can use $\theta_{m,c}$ as part of the opponent preference term:

$$
\mathrm{opponentPreference}_{m,p} = \theta_{m,c_p}
$$

Future versions should learn these profiles from historical draft behavior when user-provided history is available.

## Candidate Rollout Optimization

Candidate rollout asks: "If the user drafts player $p$ now, what roster outcomes are expected after the rest of the draft?"

For each candidate $p \in A_t$, the engine creates a copied state:

$$
D_{t+1}^{p} = \mathrm{recordPick}(D_t, p)
$$

Then it simulates the remaining draft $S$ times and evaluates the resulting user roster:

$$
Q(p) =
\frac{1}{S}\sum_{s=1}^{S}
U\left(R_{m_u}^{(s)}(T)\right)
$$

The current roster utility is based on projected points and roster VORP:

$$
U(R) = \sum_{p \in R} \mu_p + \eta \sum_{p \in R} \mathrm{VORP}_p
$$

The selected candidate is:

$$
p^* = \arg\max_{p \in C_t} Q(p)
$$

where $C_t$ is the configured candidate pool. Candidate rollouts are more expensive than the baseline recommendation score, but they better capture second-order effects such as positional scarcity and future pick timing.

## Lineup And Season Simulation

For a weekly roster $R$, lineup optimization selects eligible players into starting slots to maximize projected or sampled points:

$$
L^* =
\arg\max_{L \subseteq R}
\sum_{p \in L} Y_{p,w}
$$

subject to roster slot constraints:

$$
\mathrm{eligible}(p, q) = 1
$$

for every player $p$ assigned to slot $q$.

The current season simulator repeats this process across weeks using seeded player outcomes:

$$
\mathrm{SeasonPoints}(R) =
\sum_{w=1}^{W}
\max_{L_w \subseteq R}
\sum_{p \in L_w} Y_{p,w}
$$

This currently estimates roster scoring strength, not full league standings or playoff probability. A later model can extend the utility function to:

$$
U(R) =
E[\mathrm{Points}(R)]
+ \kappa_1 P(\mathrm{Playoffs} \mid R)
+ \kappa_2 P(\mathrm{Championship} \mid R)
$$

## Backtesting And Calibration

The engine should earn complexity through validation. Core metrics include:

Projection error:

$$
\mathrm{MAE} =
\frac{1}{n}\sum_{i=1}^{n}
\left|y_i - \hat{y}_i\right|
$$

Availability probability quality:

$$
\mathrm{Brier} =
\frac{1}{n}\sum_{i=1}^{n}
(\hat{p}_i - y_i)^2
$$

Binary log loss:

$$
\mathrm{LogLoss} =
-\frac{1}{n}\sum_{i=1}^{n}
\left[
y_i \log(\hat{p}_i) + (1-y_i)\log(1-\hat{p}_i)
\right]
$$

Draft regret for a pick can be measured as:

$$
\mathrm{Regret}_t =
U(R_T^{\mathrm{best\ available\ at}\ t}) - U(R_T^{\mathrm{actual\ pick\ at}\ t})
$$

Backtests must be time-aware. A model for a historical draft should only use information that existed before that draft.

## Current Limitations

- Fixture data is synthetic and exists to exercise the system, not to produce real draft advice.
- Baseline rankings depend on simple replacement assumptions.
- Recommendation terms are heuristic and additive.
- Availability simulation is reproducible but not calibrated.
- Opponent profiles only use observed picks in the current draft.
- Season simulation estimates roster points, not head-to-head standings or playoff odds.
- ESPN integration is dry-run only.

## Methodology Direction

The long-term engine should move from transparent baselines toward calibrated probabilistic decision optimization:

1. Replace synthetic fixtures with reproducible projection, ADP, injury, and depth-chart snapshots.
2. Validate projection distributions with historical seasons.
3. Calibrate availability probabilities against historical draft rooms.
4. Learn opponent tendencies from user-provided draft history.
5. Evaluate candidate picks by playoff and championship probability, not only projected roster points.
6. Keep every model version tied to data snapshots, validation metrics, and reproducible seeds.

The goal is not model complexity for its own sake. The goal is better draft decisions with explanations that can be audited after the season.
