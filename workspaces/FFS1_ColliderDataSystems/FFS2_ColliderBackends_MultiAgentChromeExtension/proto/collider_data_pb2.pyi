from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ContextRequest(_message.Message):
    __slots__ = ("node_id", "user_id", "application_id", "path")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    APPLICATION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    user_id: str
    application_id: str
    path: str
    def __init__(self, node_id: _Optional[str] = ..., user_id: _Optional[str] = ..., application_id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class SetContextRequest(_message.Message):
    __slots__ = ("application_id", "path", "user_id", "container_json")
    APPLICATION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_JSON_FIELD_NUMBER: _ClassVar[int]
    application_id: str
    path: str
    user_id: str
    container_json: bytes
    def __init__(self, application_id: _Optional[str] = ..., path: _Optional[str] = ..., user_id: _Optional[str] = ..., container_json: _Optional[bytes] = ...) -> None: ...

class ContextResponse(_message.Message):
    __slots__ = ("node_id", "application_id", "path", "container_json")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    APPLICATION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_JSON_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    application_id: str
    path: str
    container_json: bytes
    def __init__(self, node_id: _Optional[str] = ..., application_id: _Optional[str] = ..., path: _Optional[str] = ..., container_json: _Optional[bytes] = ...) -> None: ...

class ToolRegistration(_message.Message):
    __slots__ = ("tool_name", "origin_node_id", "owner_user_id", "params_schema_json", "code_ref", "visibility")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMS_SCHEMA_JSON_FIELD_NUMBER: _ClassVar[int]
    CODE_REF_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    origin_node_id: str
    owner_user_id: str
    params_schema_json: bytes
    code_ref: str
    visibility: str
    def __init__(self, tool_name: _Optional[str] = ..., origin_node_id: _Optional[str] = ..., owner_user_id: _Optional[str] = ..., params_schema_json: _Optional[bytes] = ..., code_ref: _Optional[str] = ..., visibility: _Optional[str] = ...) -> None: ...

class ToolRegistrationResponse(_message.Message):
    __slots__ = ("success", "tool_name", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    tool_name: str
    message: str
    def __init__(self, success: bool = ..., tool_name: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ContextFilter(_message.Message):
    __slots__ = ("application_id", "user_id", "node_ids")
    APPLICATION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    application_id: str
    user_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, application_id: _Optional[str] = ..., user_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ContextEvent(_message.Message):
    __slots__ = ("event_type", "node_id", "path", "container_json", "timestamp_ms")
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_JSON_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    event_type: str
    node_id: str
    path: str
    container_json: bytes
    timestamp_ms: int
    def __init__(self, event_type: _Optional[str] = ..., node_id: _Optional[str] = ..., path: _Optional[str] = ..., container_json: _Optional[bytes] = ..., timestamp_ms: _Optional[int] = ...) -> None: ...
