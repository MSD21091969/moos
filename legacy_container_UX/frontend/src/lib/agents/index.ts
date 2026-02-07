/**
 * Tri-Agent Architecture
 * 
 * Export all agent modules for use in ChatAgent and other components.
 */

// Types
export * from './types';

// Agents
export { VoiceAgent, createVoiceAgent } from './voice-agent';
export { CodingAgent, createCodingAgent } from './coding-agent';
export { LocalAgent, createLocalAgent } from './local-agent';

// Orchestrator
export { AgentOrchestrator, createOrchestrator, buildAgentContext } from './orchestrator';

// Tools
export {
  allTools,
  bridgeTools,
  sessionTools,
  canvasTools,
  containerTools,
  definitionTools,
  fileTools,
  navigationTools,
  getToolByName,
  getToolsByCategory,
  getToolsForAgent,
  createToolExecutor,
  TOOL_CATEGORIES,
} from './tools';
