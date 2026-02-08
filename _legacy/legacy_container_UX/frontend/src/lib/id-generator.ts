/**
 * ID Generation - Matches Backend Format
 * 
 * Backend uses: sess_{12 hex chars from UUID}
 * Pattern: ^sess_[a-f0-9]{12}$
 * 
 * This ensures demo mode IDs have same format as production,
 * making the app look/feel consistent and easier to debug.
 */

/**
 * Generate cryptographically random hex string
 * Uses Web Crypto API (available in all modern browsers)
 */
function randomHex(length: number): string {
  const bytes = new Uint8Array(Math.ceil(length / 2));
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
    .slice(0, length);
}

/**
 * Generate session ID matching backend format
 * @returns ID like "sess_abc123def456" (12 hex chars)
 */
export function generateSessionId(): string {
  return `sess_${randomHex(12)}`;
}

/**
 * Generate agent ID matching backend format
 * @returns ID like "agent_abc123def456" (12 hex chars)
 */
export function generateAgentId(): string {
  return `agent_${randomHex(12)}`;
}

/**
 * Generate tool ID matching backend format
 * @returns ID like "tool_abc123def456" (12 hex chars)
 */
export function generateToolId(): string {
  return `tool_${randomHex(12)}`;
}

/**
 * Generate datasource ID matching backend format
 * @returns ID like "source_abc123def456" (12 hex chars)
 */
export function generateSourceId(): string {
  return `source_${randomHex(12)}`;
}

/**
 * Generate generic object ID matching backend format
 * @param prefix - Type prefix (e.g., 'node', 'edge', 'user')
 * @returns ID like "prefix_abc123def456" (12 hex chars)
 */
export function generateId(prefix: string): string {
  return `${prefix}_${randomHex(12)}`;
}
