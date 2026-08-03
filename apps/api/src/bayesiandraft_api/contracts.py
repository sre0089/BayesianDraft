import json
from pathlib import Path

from fastapi import FastAPI


def openapi_schema(app: FastAPI) -> dict[str, object]:
    return app.openapi()


def write_openapi_schema(app: FastAPI, path: str | Path) -> None:
    schema_path = Path(path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(openapi_schema(app), indent=2) + "\n",
        encoding="utf-8",
    )
