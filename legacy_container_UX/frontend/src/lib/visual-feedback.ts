/**
 * Visual Feedback System for AI Operations
 * Provides visual cues when AI operates frontend tools
 */

export interface MenuOperation {
  menu: 'session' | 'agent' | 'tool' | 'api';
  action: string;
  timestamp: number;
  duration?: number;
}

export interface NodeHighlight {
  nodeIds: string[];
  color: string;
  duration: number;
  label?: string;
}

class VisualFeedbackManager {
  private menuCallbacks: Set<(menu: string | null) => void> = new Set();
  private highlightCallbacks: Set<(highlights: NodeHighlight[]) => void> = new Set();
  private activeHighlights: NodeHighlight[] = [];
  private currentMenu: string | null = null;
  private operationQueue: MenuOperation[] = [];

  /**
   * Subscribe to menu highlight changes
   */
  onMenuHighlight(callback: (menu: string | null) => void): () => void {
    this.menuCallbacks.add(callback);
    return () => this.menuCallbacks.delete(callback);
  }

  /**
   * Subscribe to node highlight changes
   */
  onNodeHighlight(callback: (highlights: NodeHighlight[]) => void): () => void {
    this.highlightCallbacks.add(callback);
    callback(this.activeHighlights); // Send current state
    return () => this.highlightCallbacks.delete(callback);
  }

  /**
   * Highlight a menu as if AI is operating it
   */
  async highlightMenu(menu: 'session' | 'agent' | 'tool' | 'api', duration: number = 2000): Promise<void> {
    this.currentMenu = menu;
    this.notifyMenuListeners(menu);

    // Auto-clear after duration
    await new Promise(resolve => setTimeout(resolve, duration));
    if (this.currentMenu === menu) {
      this.currentMenu = null;
      this.notifyMenuListeners(null);
    }
  }

  /**
   * Open a menu programmatically (AI operation)
   */
  async openMenu(
    menu: 'session' | 'agent' | 'tool' | 'api',
    action: string,
    setOpenMenu: (menu: 'session' | 'agent' | 'tool' | 'api' | null) => void,
    duration: number = 1500
  ): Promise<void> {
    // Record operation
    this.operationQueue.push({
      menu,
      action,
      timestamp: Date.now(),
      duration,
    });

    // Visual feedback sequence
    await this.highlightMenu(menu, 500); // Brief highlight
    setOpenMenu(menu); // Open the menu
    await new Promise(resolve => setTimeout(resolve, duration)); // Keep open
    setOpenMenu(null); // Close menu
  }

  /**
   * Highlight nodes on canvas
   */
  highlightNodes(nodeIds: string[], color: string = '#3b82f6', duration: number = 2000, label?: string): void {
    const highlight: NodeHighlight = {
      nodeIds,
      color,
      duration,
      label,
    };

    this.activeHighlights.push(highlight);
    this.notifyHighlightListeners();

    // Auto-remove after duration
    setTimeout(() => {
      this.activeHighlights = this.activeHighlights.filter(h => h !== highlight);
      this.notifyHighlightListeners();
    }, duration);
  }

  /**
   * Clear all node highlights
   */
  clearHighlights(): void {
    this.activeHighlights = [];
    this.notifyHighlightListeners();
  }

  /**
   * Get recent operations (for debugging/logging)
   */
  getRecentOperations(limit: number = 10): MenuOperation[] {
    return this.operationQueue.slice(-limit);
  }

  private notifyMenuListeners(menu: string | null): void {
    this.menuCallbacks.forEach(cb => cb(menu));
  }

  private notifyHighlightListeners(): void {
    this.highlightCallbacks.forEach(cb => cb([...this.activeHighlights]));
  }
}

// Singleton instance
export const visualFeedback = new VisualFeedbackManager();
