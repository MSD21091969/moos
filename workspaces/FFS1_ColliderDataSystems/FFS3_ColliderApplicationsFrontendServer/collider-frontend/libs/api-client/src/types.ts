export interface NodeContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: Record<string, unknown>[];
  knowledge: string[];
  workflows: Record<string, unknown>[];
  configs: Record<string, unknown>;
}

export interface Application {
  id: string;
  app_id: string;
  owner_id: string | null;
  display_name: string | null;
  config: Record<string, unknown>;
  root_node_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppNode {
  id: string;
  application_id: string;
  parent_id: string | null;
  path: string;
  container: NodeContainer;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AppNodeTree {
  id: string;
  path: string;
  container: NodeContainer;
  metadata_: Record<string, unknown>;
  children: AppNodeTree[];
}

export interface AppPermission {
  id: string;
  user_id: string;
  application_id: string;
  can_read: boolean;
  can_write: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface ColliderUser {
  id: string;
  email: string;
  firebase_uid: string;
  profile: Record<string, unknown>;
  container: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  id: string;
  document: string;
  distance: number;
  metadata: Record<string, unknown>;
}
