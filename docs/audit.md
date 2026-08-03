# Decision Audit

Milestone 21 adds post-draft decision audit helpers in `bayesiandraft.audit`.

## Current Behavior

- `DecisionAuditEvent` records selected player, recommendation context, alternatives, model versions, data snapshot ID, notes, and timestamp.
- `append_decision_event` appends events to a local JSON audit file.
- `load_decision_audit` returns an empty audit log when no file exists.

## Current Limitations

- Audit capture is available as a library helper, not yet wired into the draft room UI.
- Outcome attribution and post-season regret analysis are deferred until historical outcome data exists.
