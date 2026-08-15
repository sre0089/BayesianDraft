# Data Folder

This repo only commits small public-safe data files.

## Committed

- `fixtures/`: synthetic player data and rehearsal scenarios used by tests and demos.
- `manifests/`: checksum metadata for committed fixture snapshots.
- `.gitkeep` files in `raw/`, `processed/`, and `snapshots/` so the local folder layout exists after clone.

## Local Only

These folders are ignored except for `.gitkeep`:

- `raw/`: downloaded source files.
- `processed/`: imported snapshots, path banks, draft saves, and local reports.
- `snapshots/`: larger validated data snapshots.

Do not commit private league exports, raw scraped/downloaded data, draft saves, or path-bank files. They can be large and may contain private league context.
