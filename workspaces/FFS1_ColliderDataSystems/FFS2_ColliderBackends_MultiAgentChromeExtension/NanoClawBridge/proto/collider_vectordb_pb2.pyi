from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ToolIndexRequest(_message.Message):
    __slots__ = ("tool_name", "description", "origin_node_id", "owner_user_id", "params_schema_json")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMS_SCHEMA_JSON_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    description: str
    origin_node_id: str
    owner_user_id: str
    params_schema_json: str
    def __init__(self, tool_name: _Optional[str] = ..., description: _Optional[str] = ..., origin_node_id: _Optional[str] = ..., owner_user_id: _Optional[str] = ..., params_schema_json: _Optional[str] = ...) -> None: ...

class ToolIndexResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class ToolSearchRequest(_message.Message):
    __slots__ = ("query", "limit", "owner_user_id")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OWNER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    query: str
    limit: int
    owner_user_id: str
    def __init__(self, query: _Optional[str] = ..., limit: _Optional[int] = ..., owner_user_id: _Optional[str] = ...) -> None: ...

class ToolMatch(_message.Message):
    __slots__ = ("tool_name", "description", "score", "origin_node_id")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    description: str
    score: float
    origin_node_id: str
    def __init__(self, tool_name: _Optional[str] = ..., description: _Optional[str] = ..., score: _Optional[float] = ..., origin_node_id: _Optional[str] = ...) -> None: ...

class ToolSearchResponse(_message.Message):
    __slots__ = ("matches",)
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[ToolMatch]
    def __init__(self, matches: _Optional[_Iterable[_Union[ToolMatch, _Mapping]]] = ...) -> None: ...
