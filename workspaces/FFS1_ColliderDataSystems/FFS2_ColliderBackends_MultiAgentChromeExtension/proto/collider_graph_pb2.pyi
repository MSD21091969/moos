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

class ContextRequest(_message.Message):
    __slots__ = ("session_id", "node_ids", "role", "app_id", "inherit_ancestors")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    APP_ID_FIELD_NUMBER: _ClassVar[int]
    INHERIT_ANCESTORS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[str]
    role: str
    app_id: str
    inherit_ancestors: bool
    def __init__(self, session_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[str]] = ..., role: _Optional[str] = ..., app_id: _Optional[str] = ..., inherit_ancestors: bool = ...) -> None: ...

class ContextChunk(_message.Message):
    __slots__ = ("chunk_id", "sequence", "system_prompt", "skill", "tool_schema", "mcp_config", "session_meta")
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_PROMPT_FIELD_NUMBER: _ClassVar[int]
    SKILL_FIELD_NUMBER: _ClassVar[int]
    TOOL_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    MCP_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SESSION_META_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    sequence: int
    system_prompt: SystemPromptChunk
    skill: SkillChunk
    tool_schema: ToolSchemaChunk
    mcp_config: McpConfigChunk
    session_meta: SessionMetaChunk
    def __init__(self, chunk_id: _Optional[str] = ..., sequence: _Optional[int] = ..., system_prompt: _Optional[_Union[SystemPromptChunk, _Mapping]] = ..., skill: _Optional[_Union[SkillChunk, _Mapping]] = ..., tool_schema: _Optional[_Union[ToolSchemaChunk, _Mapping]] = ..., mcp_config: _Optional[_Union[McpConfigChunk, _Mapping]] = ..., session_meta: _Optional[_Union[SessionMetaChunk, _Mapping]] = ...) -> None: ...

class SystemPromptChunk(_message.Message):
    __slots__ = ("section", "content")
    SECTION_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    section: str
    content: str
    def __init__(self, section: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class SkillChunk(_message.Message):
    __slots__ = ("name", "description", "emoji", "markdown_body", "tool_ref", "user_invocable", "model_invocable", "invocation_policy", "requires_bins", "requires_env", "namespace", "version", "kind", "scope", "source_node_path", "source_node_id", "inputs", "outputs", "depends_on", "exposes_tools", "child_skills")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EMOJI_FIELD_NUMBER: _ClassVar[int]
    MARKDOWN_BODY_FIELD_NUMBER: _ClassVar[int]
    TOOL_REF_FIELD_NUMBER: _ClassVar[int]
    USER_INVOCABLE_FIELD_NUMBER: _ClassVar[int]
    MODEL_INVOCABLE_FIELD_NUMBER: _ClassVar[int]
    INVOCATION_POLICY_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_BINS_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_ENV_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    INPUTS_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    DEPENDS_ON_FIELD_NUMBER: _ClassVar[int]
    EXPOSES_TOOLS_FIELD_NUMBER: _ClassVar[int]
    CHILD_SKILLS_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    emoji: str
    markdown_body: str
    tool_ref: str
    user_invocable: bool
    model_invocable: bool
    invocation_policy: str
    requires_bins: _containers.RepeatedScalarFieldContainer[str]
    requires_env: _containers.RepeatedScalarFieldContainer[str]
    namespace: str
    version: str
    kind: str
    scope: str
    source_node_path: str
    source_node_id: str
    inputs: _containers.RepeatedScalarFieldContainer[str]
    outputs: _containers.RepeatedScalarFieldContainer[str]
    depends_on: _containers.RepeatedScalarFieldContainer[str]
    exposes_tools: _containers.RepeatedScalarFieldContainer[str]
    child_skills: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., emoji: _Optional[str] = ..., markdown_body: _Optional[str] = ..., tool_ref: _Optional[str] = ..., user_invocable: bool = ..., model_invocable: bool = ..., invocation_policy: _Optional[str] = ..., requires_bins: _Optional[_Iterable[str]] = ..., requires_env: _Optional[_Iterable[str]] = ..., namespace: _Optional[str] = ..., version: _Optional[str] = ..., kind: _Optional[str] = ..., scope: _Optional[str] = ..., source_node_path: _Optional[str] = ..., source_node_id: _Optional[str] = ..., inputs: _Optional[_Iterable[str]] = ..., outputs: _Optional[_Iterable[str]] = ..., depends_on: _Optional[_Iterable[str]] = ..., exposes_tools: _Optional[_Iterable[str]] = ..., child_skills: _Optional[_Iterable[str]] = ...) -> None: ...

class ToolSchemaChunk(_message.Message):
    __slots__ = ("name", "description", "parameters_json")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_JSON_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    parameters_json: bytes
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., parameters_json: _Optional[bytes] = ...) -> None: ...

class McpConfigChunk(_message.Message):
    __slots__ = ("name", "transport_type", "url", "command", "args")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    transport_type: str
    url: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., transport_type: _Optional[str] = ..., url: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ...) -> None: ...

class SessionMetaChunk(_message.Message):
    __slots__ = ("role", "app_id", "composed_nodes", "username")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    APP_ID_FIELD_NUMBER: _ClassVar[int]
    COMPOSED_NODES_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    role: str
    app_id: str
    composed_nodes: _containers.RepeatedScalarFieldContainer[str]
    username: str
    def __init__(self, role: _Optional[str] = ..., app_id: _Optional[str] = ..., composed_nodes: _Optional[_Iterable[str]] = ..., username: _Optional[str] = ...) -> None: ...

class DeltaSubscription(_message.Message):
    __slots__ = ("session_id", "node_ids")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, session_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class ContextDelta(_message.Message):
    __slots__ = ("delta_id", "timestamp", "operation", "system_prompt_delta", "skill_delta", "tool_schema_delta")
    DELTA_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_PROMPT_DELTA_FIELD_NUMBER: _ClassVar[int]
    SKILL_DELTA_FIELD_NUMBER: _ClassVar[int]
    TOOL_SCHEMA_DELTA_FIELD_NUMBER: _ClassVar[int]
    delta_id: str
    timestamp: str
    operation: str
    system_prompt_delta: SystemPromptDelta
    skill_delta: SkillDelta
    tool_schema_delta: ToolSchemaDelta
    def __init__(self, delta_id: _Optional[str] = ..., timestamp: _Optional[str] = ..., operation: _Optional[str] = ..., system_prompt_delta: _Optional[_Union[SystemPromptDelta, _Mapping]] = ..., skill_delta: _Optional[_Union[SkillDelta, _Mapping]] = ..., tool_schema_delta: _Optional[_Union[ToolSchemaDelta, _Mapping]] = ...) -> None: ...

class SystemPromptDelta(_message.Message):
    __slots__ = ("section", "content")
    SECTION_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    section: str
    content: str
    def __init__(self, section: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class SkillDelta(_message.Message):
    __slots__ = ("skill",)
    SKILL_FIELD_NUMBER: _ClassVar[int]
    skill: SkillChunk
    def __init__(self, skill: _Optional[_Union[SkillChunk, _Mapping]] = ...) -> None: ...

class ToolSchemaDelta(_message.Message):
    __slots__ = ("tool_schema",)
    TOOL_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    tool_schema: ToolSchemaChunk
    def __init__(self, tool_schema: _Optional[_Union[ToolSchemaChunk, _Mapping]] = ...) -> None: ...

class BootstrapResponse(_message.Message):
    __slots__ = ("session_id", "agents_md", "soul_md", "tools_md", "skills", "tool_schemas", "mcp_servers", "session_meta")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    AGENTS_MD_FIELD_NUMBER: _ClassVar[int]
    SOUL_MD_FIELD_NUMBER: _ClassVar[int]
    TOOLS_MD_FIELD_NUMBER: _ClassVar[int]
    SKILLS_FIELD_NUMBER: _ClassVar[int]
    TOOL_SCHEMAS_FIELD_NUMBER: _ClassVar[int]
    MCP_SERVERS_FIELD_NUMBER: _ClassVar[int]
    SESSION_META_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    agents_md: str
    soul_md: str
    tools_md: str
    skills: _containers.RepeatedCompositeFieldContainer[SkillChunk]
    tool_schemas: _containers.RepeatedCompositeFieldContainer[ToolSchemaChunk]
    mcp_servers: _containers.RepeatedCompositeFieldContainer[McpConfigChunk]
    session_meta: SessionMetaChunk
    def __init__(self, session_id: _Optional[str] = ..., agents_md: _Optional[str] = ..., soul_md: _Optional[str] = ..., tools_md: _Optional[str] = ..., skills: _Optional[_Iterable[_Union[SkillChunk, _Mapping]]] = ..., tool_schemas: _Optional[_Iterable[_Union[ToolSchemaChunk, _Mapping]]] = ..., mcp_servers: _Optional[_Iterable[_Union[McpConfigChunk, _Mapping]]] = ..., session_meta: _Optional[_Union[SessionMetaChunk, _Mapping]] = ...) -> None: ...
