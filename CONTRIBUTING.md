# Contributing

BayesianDraft is built in focused, runnable slices. Each change should keep the repository usable and avoid unrelated refactors.

## Before Starting Work

1. Read the relevant docs in `docs/`.
2. Summarize the current repository state.
3. State the change objective.
4. List files expected to change.
5. Identify tests and acceptance criteria.
6. Ask for approval when a change is large, destructive, or ambiguous.

## During Work

- Make focused changes.
- Keep public interfaces typed.
- Use deterministic seeds for simulations.
- Use synthetic fixtures instead of live services in tests.
- Do not commit secrets, credentials, cookies, ESPN tokens, local databases, virtual environments, node modules, build output, or large raw datasets.

## Before Commit

Run the relevant checks:

```bash
pytest
ruff check .
mypy bayesiandraft apps/api
npm test
npm run lint
```

If a command is not relevant to the change, note that in the change summary.

## Git

Use focused commits. Do not push rewritten history unless explicitly needed and coordinated.
