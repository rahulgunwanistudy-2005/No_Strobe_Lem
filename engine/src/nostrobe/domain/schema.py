"""Deterministic JSON Schema serialization."""

import json
from pathlib import Path

from nostrobe.domain.models import HazardTrack


def schema_text() -> str:
    schema = HazardTrack.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def write_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(schema_text(), encoding="utf-8")
