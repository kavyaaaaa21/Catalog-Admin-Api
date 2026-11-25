from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, StringConstraints, ValidationInfo, field_validator

MAX_ID = 2_147_483_647  # keeps ids inside what the DB can store (no 500s on huge ints)
Id = Annotated[int, Field(le=MAX_ID)]

# lowercase letters, digits and hyphens only (no leading/trailing/double hyphens)
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=1, max_length=120)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class PartialUpdate(BaseModel):
    """Base for Update schemas: every field optional, but an explicit null is
    rejected unless the field is listed in `nullable_fields`."""

    nullable_fields: ClassVar[set[str]] = set()

    @field_validator("*", mode="after")
    @classmethod
    def _reject_null(cls, value, info: ValidationInfo):
        if value is None and info.field_name not in cls.nullable_fields:
            raise ValueError("field cannot be null")
        return value
