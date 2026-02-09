export type WorkspaceType = "FILESYST" | "CLOUD" | "ADMIN" | "SIDEPANEL" | "AGENT_SEAT";

export interface AppRoute {
  app: string;
  url: string;
  packageName: string;
}

/**
 * Get the appropriate app route based on workspace domain type
 */
export function getAppRouteForContext(domain: WorkspaceType): AppRoute {
  switch (domain) {
    case "FILESYST":
      return {
        app: "FFS6",
        url: "http://localhost:3006",
        packageName: "@collider/ide-viewer",
      };
    case "ADMIN":
      return {
        app: "FFS7",
        url: "http://localhost:3007",
        packageName: "@collider/admin-viewer",
      };
    case "CLOUD":
      return {
        app: "FFS8",
        url: "http://localhost:3008",
        packageName: "@collider/cloud-viewer",
      };
    case "SIDEPANEL":
    case "AGENT_SEAT":
      return {
        app: "FFS4",
        url: "http://localhost:3004",
        packageName: "@collider/sidepanel-ui",
      };
    default:
      // Default to sidepanel
      return {
        app: "FFS4",
        url: "http://localhost:3004",
        packageName: "@collider/sidepanel-ui",
      };
  }
}

/**
 * Extract domain type from application config
 */
export function getDomainFromApp(app: any): WorkspaceType {
  const domain = app?.config?.domain;
  if (!domain) return "CLOUD";

  return domain as WorkspaceType;
}
