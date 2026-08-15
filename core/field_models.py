from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class FieldValidationError(ValueError):
    pass


@dataclass
class Field:
    id: str
    label: str
    type: str = "text"
    default: Any = ""
    options: list[str] = field(default_factory=list)
    min: float | None = None
    max: float | None = None
    required: bool = False
    help: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Field":
        field_id = str(data.get("id", "")).strip()
        if not field_id:
            raise FieldValidationError("A field is missing its id.")
        return cls(
            id=field_id,
            label=str(data.get("label", field_id)),
            type=str(data.get("type", "text")),
            default=data.get("default", ""),
            options=[str(o) for o in data.get("options", [])],
            min=data.get("min"),
            max=data.get("max"),
            required=bool(data.get("required", False)),
            help=str(data.get("help", "")),
        )

    def validate(self, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            if self.required:
                raise FieldValidationError(f"{self.label} is required.")
            value = self.default

        if self.type == "select":
            if value not in self.options:
                raise FieldValidationError(
                    f"{self.label}: '{value}' is not one of the choices."
                )
        elif self.type == "color":
            value = str(value).strip()
            if not _COLOR_RE.match(value):
                raise FieldValidationError(
                    f"{self.label} must be a color like #FF6B35."
                )
        elif self.type == "number":
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise FieldValidationError(f"{self.label} must be a number.")
            if self.min is not None and value < self.min:
                raise FieldValidationError(f"{self.label} must be at least {self.min}.")
            if self.max is not None and value > self.max:
                raise FieldValidationError(f"{self.label} must be at most {self.max}.")
        else:
            value = str(value)
            if len(value) > 2000:
                raise FieldValidationError(f"{self.label} is too long.")

        return value
