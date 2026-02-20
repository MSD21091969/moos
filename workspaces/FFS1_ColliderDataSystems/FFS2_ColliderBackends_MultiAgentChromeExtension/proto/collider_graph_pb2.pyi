from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RegisterToolRequest(_message.Message):
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

class RegisterToolResponse(_message.Message):
    __slots__ = ("success", "tool_name", "args_schema_json", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_SCHEMA_JSON_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    tool_name: str
    args_schema_json: bytes
    message: str
    def __init__(self, success: bool = ..., tool_name: _Optional[str] = ..., args_schema_json: _Optional[bytes] = ..., message: _Optional[str] = ...) -> None: ...

class RegisterWorkflowRequest(_message.Message):
    __slots__ = ("workflow_name", "origin_node_id", "owner_user_id", "steps", "entry_point")
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    ENTRY_POINT_FIELD_NUMBER: _ClassVar[int]
    workflow_name: str
    origin_node_id: str
    owner_user_id: str
    steps: _containers.RepeatedScalarFieldContainer[str]
    entry_point: str
    def __init__(self, workflow_name: _Optional[str] = ..., origin_node_id: _Optional[str] = ..., owner_user_id: _Optional[str] = ..., steps: _Optional[_Iterable[str]] = ..., entry_point: _Optional[str] = ...) -> None: ...

class RegisterWorkflowResponse(_message.Message):
    __slots__ = ("success", "workflow_name", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    workflow_name: str
    message: str
    def __init__(self, success: bool = ..., workflow_name: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ToolDiscoveryRequest(_message.Message):
    __slots__ = ("query", "user_id", "visibility_filter", "limit")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FILTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    query: str
    user_id: str
    visibility_filter: _containers.RepeatedScalarFieldContainer[str]
    limit: int
    def __init__(self, query: _Optional[str] = ..., user_id: _Optional[str] = ..., visibility_filter: _Optional[_Iterable[str]] = ..., limit: _Optional[int] = ...) -> None: ...

class ToolEntry(_message.Message):
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

class ToolDiscoveryResponse(_message.Message):
    __slots__ = ("tools", "total_count")
    TOOLS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    tools: _containers.RepeatedCompositeFieldContainer[ToolEntry]
    total_count: int
    def __init__(self, tools: _Optional[_Iterable[_Union[ToolEntry, _Mapping]]] = ..., total_count: _Optional[int] = ...) -> None: ...

class SubgraphRequest(_message.Message):
    __slots__ = ("workflow_name", "user_id", "inputs_json")
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    INPUTS_JSON_FIELD_NUMBER: _ClassVar[int]
    workflow_name: str
    user_id: str
    inputs_json: bytes
    def __init__(self, workflow_name: _Optional[str] = ..., user_id: _Optional[str] = ..., inputs_json: _Optional[bytes] = ...) -> None: ...

class SubgraphResponse(_message.Message):
    __slots__ = ("success", "workflow_name", "result_json", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    workflow_name: str
    result_json: bytes
    error_message: str
    def __init__(self, success: bool = ..., workflow_name: _Optional[str] = ..., result_json: _Optional[bytes] = ..., error_message: _Optional[str] = ...) -> None: ...

class ToolExecutionRequest(_message.Message):
    __slots__ = ("tool_name", "user_id", "inputs_json")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    INPUTS_JSON_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    user_id: str
    inputs_json: bytes
    def __init__(self, tool_name: _Optional[str] = ..., user_id: _Optional[str] = ..., inputs_json: _Optional[bytes] = ...) -> None: ...

class ToolExecutionResponse(_message.Message):
    __slots__ = ("success", "tool_name", "result_json", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    tool_name: str
    result_json: bytes
    error_message: str
    def __init__(self, success: bool = ..., tool_name: _Optional[str] = ..., result_json: _Optional[bytes] = ..., error_message: _Optional[str] = ...) -> None: ...

class SubgraphProgress(_message.Message):
    __slots__ = ("workflow_name", "current_step", "step_index", "total_steps", "status", "partial_result_json")
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    CURRENT_STEP_FIELD_NUMBER: _ClassVar[int]
    STEP_INDEX_FIELD_NUMBER: _ClassVar[int]
    TOTAL_STEPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    workflow_name: str
    current_step: str
    step_index: int
    total_steps: int
    status: str
    partial_result_json: bytes
    def __init__(self, workflow_name: _Optional[str] = ..., current_step: _Optional[str] = ..., step_index: _Optional[int] = ..., total_steps: _Optional[int] = ..., status: _Optional[str] = ..., partial_result_json: _Optional[bytes] = ...) -> None: ...
