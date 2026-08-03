# Release Metadata

BayesianDraft exposes build and release metadata helpers.

## Current Behavior

- `bayesiandraft.release.build_info_from_env` returns package version and optional build metadata.
- `GET /version` exposes build metadata from the local API.
- `scripts/version_info.py` prints JSON build metadata.

## Environment Variables

- `BAYESIANDRAFT_VERSION`
- `BAYESIANDRAFT_COMMIT_SHA`
- `BAYESIANDRAFT_BUILD_TIMESTAMP`
