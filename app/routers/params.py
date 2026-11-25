from typing import Annotated

from fastapi import Path, Query

from app.schemas.common import MAX_ID

IdPath = Annotated[int, Path(le=MAX_ID)]
IdQuery = Annotated[int | None, Query(le=MAX_ID)]