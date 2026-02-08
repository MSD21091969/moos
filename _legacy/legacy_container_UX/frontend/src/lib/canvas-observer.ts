/**
 * Canvas State Observer for Chat Agent
 * Allows the agent to "see" visual state (selections, menus, positions)
 */

import { useWorkspaceStore } from './workspace-store';

export interface CanvasState {
  selectedSessions: Array<{
    id: string;
    title: string;
    position: { x: number; y: number };
    themeColor: string;
    status: string;
  }>;
  totalSessions: number;
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
  marqueeActive: boolean;
  contextMenuVisible: boolean;
  recentOperations: string[];
}

export interface UIInteraction {
  type: 'right-click' | 'marquee-select' | 'create-session' | 'delete-nodes';
  position?: { x: number; y: number };
  selectedIds?: string[];
  result?: any;
}

class CanvasObserver {
  private interactions: UIInteraction[] = [];
  private maxHistorySize = 50;

  /**
   * Get current canvas state (what the agent can "see")
   */
  getCanvasState(): CanvasState {
    try {
      console.log('🔍 Getting canvas state...');
      const state = useWorkspaceStore.getState();
      console.log('📦 Store state:', {
        nodesCount: state.nodes.length,
        selectedCount: state.selectedNodeIds.length,
        containersCount: state.containers.length,
      });

      const selectedSessions = state.nodes
        .filter((n) => n.type === 'session' && state.selectedNodeIds.includes(n.id))
        .map((n) => {
          const data = n.data as any;
          return {
            id: n.id,
            title: data.label || data.title || 'Untitled',
            position: n.position,
            themeColor: data.themeColor || '#3b82f6',
            status: data.status || 'active',
          };
        });

      console.log('✅ Canvas state retrieved:', { selectedSessions: selectedSessions.length });

      return {
        selectedSessions,
        totalSessions: state.containers.length,
        viewport: state.viewport,
        marqueeActive: false,
        contextMenuVisible: false,
        recentOperations: this.interactions.slice(-5).map((i) => i.type),
      };
    } catch (error) {
      console.error('❌ Error getting canvas state:', error);
      return {
        selectedSessions: [],
        totalSessions: 0,
        viewport: { x: 0, y: 0, zoom: 1 },
        marqueeActive: false,
        contextMenuVisible: false,
        recentOperations: [],
      };
    }
  }

  /**
   * Generate natural language description of canvas state
   */
  describeCanvasState(): string {
    const state = this.getCanvasState();
    const parts: string[] = [];

    if (state.selectedSessions.length > 0) {
      const sessionNames = state.selectedSessions.map((s) => `"${s.title}"`).join(', ');
      parts.push(
        `${state.selectedSessions.length} session${
          state.selectedSessions.length > 1 ? 's' : ''
        } selected: ${sessionNames}`
      );
      parts.push(`Blue borders visible on selected sessions`);
    } else {
      parts.push('No sessions currently selected');
    }

    parts.push(`Total sessions on canvas: ${state.totalSessions}`);
    parts.push(`Viewport zoom: ${(state.viewport.zoom * 100).toFixed(0)}%`);

    if (this.interactions.length > 0) {
      const lastOp = this.interactions[this.interactions.length - 1];
      parts.push(`Last UI action: ${lastOp.type}`);
    }

    return parts.join('\n');
  }

  /**
   * Record a UI interaction (for agent to observe)
   */
  recordInteraction(interaction: UIInteraction): void {
    this.interactions.push({
      ...interaction,
      result: interaction.result,
    });

    // Keep history bounded
    if (this.interactions.length > this.maxHistorySize) {
      this.interactions.shift();
    }
  }

  /**
   * Simulate right-click menu at position
   * This makes the agent trigger the actual UI flow
   */
  async simulateRightClick(position: { x: number; y: number }): Promise<void> {
    this.recordInteraction({
      type: 'right-click',
      position,
    });

    // Dispatch custom event that GameCanvas can listen to
    window.dispatchEvent(
      new CustomEvent('agent-right-click', {
        detail: { position },
      })
    );
  }

  /**
   * Simulate marquee selection
   */
  async simulateMarqueeSelect(bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  }): Promise<string[]> {
    const state = useWorkspaceStore.getState();

    // Find sessions within bounds
    const selectedIds = state.nodes
      .filter((n) => {
        if (n.type !== 'session') return false;
        const inX = n.position.x >= bounds.x && n.position.x <= bounds.x + bounds.width;
        const inY = n.position.y >= bounds.y && n.position.y <= bounds.y + bounds.height;
        return inX && inY;
      })
      .map((n) => n.id);

    // Update selection in store
    state.setSelectedNodes(selectedIds);

    this.recordInteraction({
      type: 'marquee-select',
      selectedIds,
      result: `Selected ${selectedIds.length} sessions`,
    });

    return selectedIds;
  }

  /**
   * Get agent-friendly context menu options for current selection
   */
  getContextMenuOptions(): string[] {
    const state = this.getCanvasState();

    if (state.selectedSessions.length > 0) {
      return [
        `Duplicate (${state.selectedSessions.length} sessions)`,
        `Edit session`,
        `Delete (${state.selectedSessions.length} sessions)`,
        'Move to zone',
        'Change color',
      ];
    }

    return ['Create new session', 'Create tool node', 'Paste'];
  }

  /**
   * Get recent interaction history
   */
  getInteractionHistory(limit: number = 10): UIInteraction[] {
    return this.interactions.slice(-limit);
  }

  /**
   * Clear interaction history
   */
  clearHistory(): void {
    this.interactions = [];
  }
}

// Singleton instance
export const canvasObserver = new CanvasObserver();
