import type {
  Application,
  ColliderUser,
  AppPermission,
  MainContext,
  TabContext,
} from "~/types";

class ContextManager {
  private context: MainContext = {
    user: null,
    applications: [],
    permissions: [],
    activeTabId: null,
    tabs: new Map(),
  };

  get user(): ColliderUser | null {
    return this.context.user;
  }

  get applications(): Application[] {
    return this.context.applications;
  }

  get activeTab(): TabContext | undefined {
    if (this.context.activeTabId === null) return undefined;
    return this.context.tabs.get(this.context.activeTabId);
  }

  setUser(user: ColliderUser): void {
    this.context.user = user;
    this.persist();
  }

  setApplications(apps: Application[]): void {
    this.context.applications = apps;
    this.persist();
  }

  setPermissions(permissions: AppPermission[]): void {
    this.context.permissions = permissions;
    this.persist();
  }

  setActiveTab(tabId: number): void {
    this.context.activeTabId = tabId;
    this.persist();
  }

  updateTabContext(tabId: number, update: Partial<TabContext>): void {
    const existing = this.context.tabs.get(tabId) ?? {
      tabId,
      url: "",
      title: "",
    };
    this.context.tabs.set(tabId, { ...existing, ...update });
    this.persist();
  }

  removeTab(tabId: number): void {
    this.context.tabs.delete(tabId);
    if (this.context.activeTabId === tabId) {
      this.context.activeTabId = null;
    }
    this.persist();
  }

  getSerializableContext(): Record<string, unknown> {
    return {
      user: this.context.user,
      applications: this.context.applications,
      permissions: this.context.permissions,
      activeTabId: this.context.activeTabId,
      tabs: Object.fromEntries(this.context.tabs),
    };
  }

  private persist(): void {
    chrome.storage.session
      .set({ colliderContext: this.getSerializableContext() })
      .catch(console.error);
  }

  async restore(): Promise<void> {
    const result = await chrome.storage.session.get("colliderContext");
    if (result.colliderContext) {
      const saved = result.colliderContext as Record<string, unknown>;
      this.context.user = (saved.user as ColliderUser) ?? null;
      this.context.applications =
        (saved.applications as Application[]) ?? [];
      this.context.permissions =
        (saved.permissions as AppPermission[]) ?? [];
      this.context.activeTabId =
        (saved.activeTabId as number) ?? null;
      const tabs = (saved.tabs as Record<string, TabContext>) ?? {};
      this.context.tabs = new Map(
        Object.entries(tabs).map(([k, v]) => [Number(k), v])
      );
    }
  }
}

export const contextManager = new ContextManager();
