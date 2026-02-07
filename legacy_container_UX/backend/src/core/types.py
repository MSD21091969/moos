"""Custom types for the application."""

from typing import Annotated, NewType
from pydantic import StringConstraints

UserId = NewType("UserId", str)
SessionId = NewType("SessionId", str)
CollectionId = NewType("CollectionId", str)
ToolId = NewType("ToolId", str)

SessionIdStr = Annotated[str, StringConstraints(pattern=r"^sess_[a-f0-9]{16}$")]
UserIdStr = Annotated[str, StringConstraints(pattern=r"^user_[a-f0-9]{16}$")]
Email = Annotated[str, StringConstraints(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
