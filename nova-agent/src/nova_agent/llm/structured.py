import json
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(ValueError):
    pass


def parse_json(text: str, model: Type[T]) -> T:
    """Parse `text` as JSON and validate against the given pydantic model.

    The VLM may emit prose around the JSON; extract the first {...} block.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise StructuredOutputError(f"No JSON object found in: {text[:200]!r}")
    raw = text[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise StructuredOutputError(f"Invalid JSON: {e}; raw={raw[:200]!r}") from e
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise StructuredOutputError(f"Schema mismatch: {e}; raw={raw[:200]!r}") from e
