# Opponents

`bayesiandraft.opponents` includes a transparent opponent profile baseline.

## Current Behavior

- Builds one profile per non-user manager.
- Infers observed position counts from completed draft picks.
- Applies smoothing so managers with no picks still have usable preferences.
- Estimates position preference, market timing, and a simple risk-tolerance field.
- Feeds opponent pick weights into remaining-draft simulation.

## Current Limitations

- Profiles only use the current draft's observed picks.
- No historical manager data is loaded yet.
- Roster construction style, team stacks, bye weeks, and platform-specific behavior are not modeled.
- Profile weights are heuristic and not calibrated against historical drafts.
