# Roadmap

BayesianDraft is already usable as a local draft-room tool, but there are a few clear places where it can become easier to use and more statistically serious.

## Working Now

- Config-driven full-PPR scoring and 14-team snake draft settings.
- Deterministic draft state with rosters, availability, undo/redo, edits, save, and load.
- Synthetic fixture data for public tests.
- Public/user-provided snapshot import paths.
- Baseline rankings with VORP, tiers, ADP deltas, sleeper/fade signals, and exports.
- Explainable recommendations with roster need, value, tier pressure, market value, and next-pick risk.
- Path-bank support for faster draft-day opportunity-cost context.
- Seeded draft simulations, strategy comparisons, roster balance reports, and rehearsal scenarios.
- Local terminal UI, FastAPI app, and browser draft room.
- Privacy scan, docs index check, local CI helper, and preflight scripts.

## Next Improvements

- Make live pick entry even faster and harder to mess up.
- Add clearer saved-session recovery for draft day.
- Improve public data snapshot setup so new users can get real-ish data faster.
- Add better visual examples for the TUI and web draft room.
- Tighten documentation around path-bank generation and when it is worth running.

## Larger Ideas

- Backtest recommendations against historical draft and season results.
- Validate projection ranges against real outcomes instead of relying on simple baselines.
- Add personalized opponent tendencies from user-provided draft history.
- Add opt-in ESPN sync after the manual workflow is boringly reliable.
- Convert draft recommendations into season-level playoff and championship probability estimates.

## Non-Goals For Now

- No committed private league data.
- No required ESPN login for the main workflow.
- No black-box model replacing the explainable baseline until it clearly beats it in validation.
