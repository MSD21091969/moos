/**
 * System Prompt Builder - Dynamic prompt construction for Collider Host
 * 
 * Builds context-aware system prompts by combining:
 * - Static knowledge (persona, ontology, topology)
 * - Dynamic visual context (nodes, edges, viewport, selection)
 * - Session-specific state (breadcrumbs, active container)
 */

import { VisualContext } from './gemini-live-client';
import { PERSONA, buildKnowledgeInjection } from './chat/agent-context-knowledge';

// =============================================================================
// INTERACTION GUIDELINES (Gemini 3 optimized)
// =============================================================================

const INTERACTION_GUIDELINES = `
**Interaction Guidelines:**
- **Be Concise:** Spoken responses: 1-2 sentences. Text responses: 2-3 sentences max unless explaining complex concepts.
- **Tool-First:** Execute tools before explaining. Show results, then summarize.
- **Proactive:** After completing a task, offer the logical next step.
- **No Hallucination:** Only reference IDs you see in the visual context. Never invent session/node IDs.
- **Code-Fluent:** When users ask "how does this work?", explain the Pydantic model or API endpoint.
`.trim();

// =============================================================================
// SYSTEM PROMPT BUILDER
// =============================================================================

export class SystemPromptBuilder {
  /**
   * Build the complete system prompt with visual context
   */
  public static build(context: VisualContext): string {
    const visualContext = this.buildVisualContextDescription(context);
    const knowledge = buildKnowledgeInjection({
      includeOntology: true,
      includeTopology: true,
      includeApiReference: false, // Too verbose for every prompt
      includeFirestore: false,
    });

    return `
${knowledge}

---

${visualContext}

---

${INTERACTION_GUIDELINES}
`.trim();
  }

  /**
   * Build a minimal prompt for voice interactions (faster response)
   */
  public static buildMinimal(context: VisualContext): string {
    const visualContext = this.buildVisualContextDescription(context);

    return `
${PERSONA}

---

${visualContext}

**Voice Mode:** Keep responses under 2 sentences. Execute tools immediately.
`.trim();
  }

  /**
   * Build an expert prompt with full knowledge (for complex queries)
   */
  public static buildExpert(context: VisualContext): string {
    const visualContext = this.buildVisualContextDescription(context);
    const fullKnowledge = buildKnowledgeInjection({
      includeManifesto: true,
      includeOntology: true,
      includeTopology: true,
      includeApiReference: true,
      includeFirestore: true,
    });

    return `
${fullKnowledge}

---

${visualContext}

---

${INTERACTION_GUIDELINES}

**Expert Mode:** You have full API and Firestore knowledge. Explain implementation details when asked.
`.trim();
  }

  /**
   * Build visual context description from current state
   * Level-aware: describes what's visible AT CURRENT LEVEL only
   */
  private static buildVisualContextDescription(context: VisualContext): string {
    // Defensive null checks
    const nodes = context?.nodes ?? [];
    const edges = context?.edges ?? [];
    const selectedNodes = context?.selectedNodes ?? [];
    const activeSession = context?.activeSession ?? null;
    const viewport = context?.viewport ?? { x: 0, y: 0, zoom: 1 };
    const globalSessions = context?.globalSessions ?? [];
    const breadcrumbs = context?.breadcrumbs ?? [];

    // Calculate current depth level (L0=workspace, L1=inside session, L2=inside agent, etc.)
    const currentLevel = breadcrumbs.length;
    const levelLabel = currentLevel === 0 ? 'L0 - Workspace' : `L${currentLevel} - ${breadcrumbs.map(b => b.title || b.label).join(' → ')}`;

    // Build node descriptions with semantic info
    const nodeDescriptions = nodes
      .map((n) => {
        const selected = selectedNodes.includes(n.id) ? '🔵 SELECTED' : '';
        const nodeData = n.data as Record<string, unknown> | undefined;
        const label = (nodeData?.label as string) || n.type || 'Unknown';
        const tags = (nodeData?.tags as string[])?.join(', ') || '';
        const tagStr = tags ? `[${tags}]` : '';
        const typeEmoji = this.getTypeEmoji(n.type as string);
        return `  ${typeEmoji} ${label} (${n.id}) at (${Math.round(n.position.x)}, ${Math.round(n.position.y)}) ${tagStr} ${selected}`.trim();
      })
      .join('\n');

    // Build edge descriptions
    const edgeDescriptions = edges
      .slice(0, 10) // Limit to 10 edges to avoid token bloat
      .map((e) => {
        const source = nodes.find((n) => n.id === e.source);
        const target = nodes.find((n) => n.id === e.target);
        const sourceLabel = (source?.data as Record<string, unknown>)?.label || e.source;
        const targetLabel = (target?.data as Record<string, unknown>)?.label || e.target;
        return `  ${sourceLabel} → ${targetLabel}`;
      })
      .join('\n');

    // Global context only shown at L0 workspace level
    const workspaceContext = currentLevel === 0 && globalSessions.length > 0
      ? `\n**All Workspace Sticky Notes (${globalSessions.length} total):**\n${globalSessions.slice(0, 8).map(s => `  📋 ${s.title}`).join('\n')}${globalSessions.length > 8 ? `\n  ... and ${globalSessions.length - 8} more` : ''}`
      : '';

    // Count by type for UX-friendly summary
    const sessionCount = nodes.filter(n => n.type === 'session').length;
    const agentCount = nodes.filter(n => n.type === 'agent').length;
    const toolCount = nodes.filter(n => n.type === 'tool').length;
    const sourceCount = nodes.filter(n => n.type === 'source').length;
    
    // UX-friendly summary of what's at current level
    const canvasSummary = [
      sessionCount > 0 ? `${sessionCount} sticky note${sessionCount > 1 ? 's' : ''}` : null,
      agentCount > 0 ? `${agentCount} agent${agentCount > 1 ? 's' : ''}` : null,
      toolCount > 0 ? `${toolCount} tool${toolCount > 1 ? 's' : ''}` : null,
      sourceCount > 0 ? `${sourceCount} data source${sourceCount > 1 ? 's' : ''}` : null,
    ].filter(Boolean).join(', ') || 'empty canvas';

    // Breadcrumb navigation context (how user got here)
    const breadcrumbTrail = breadcrumbs.length > 0
      ? `**Navigation:** Workspace → ${breadcrumbs.map(b => b.title || b.label).join(' → ')}`
      : '**Navigation:** Workspace (top level)';

    return `
**[WHAT'S ON SCREEN - ${levelLabel}]**
${breadcrumbTrail}
**Current View:** ${activeSession ? `Inside "${activeSession}"` : 'Workspace (top level)'}
**At This Level:** ${canvasSummary}
**Viewport:** zoom ${(viewport.zoom * 100).toFixed(0)}%, pan (${Math.round(viewport.x)}, ${Math.round(viewport.y)})
**Selection:** ${selectedNodes.length > 0 ? `${selectedNodes.length} item${selectedNodes.length > 1 ? 's' : ''} selected` : 'nothing selected'}

**Items at This Level (${nodes.length}):**
${nodeDescriptions || '  (empty canvas)'}

**Connections (${edges.length}):**
${edgeDescriptions || '  (no connections)'}
${workspaceContext}
`.trim();
  }

  /**
   * Get emoji for node type
   */
  private static getTypeEmoji(type: string): string {
    const emojiMap: Record<string, string> = {
      session: '📋',  // sticky note
      agent: '🤖',
      tool: '🔧',
      source: '📊',
      user: '👤',
      object: '📦',
    };
    return emojiMap[type?.toLowerCase()] || '📌';
  }
}

