import { DataServerClient } from "@collider/api-client";
import type { AppNodeTree } from "@collider/api-client";
import Link from "next/link";
import { notFound } from "next/navigation";

const client = new DataServerClient("http://localhost:8000");

export const dynamic = "force-dynamic";

function TreeView({
  nodes,
  depth = 0,
}: {
  nodes: AppNodeTree[];
  depth?: number;
}) {
  return (
    <div>
      {nodes.map((node) => (
        <div key={node.id}>
          <div
            className="flex items-center gap-2 py-1.5 px-2 hover:bg-gray-800 rounded text-sm"
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
          >
            {node.children.length > 0 && (
              <span className="text-gray-500 text-xs">&#9660;</span>
            )}
            <span className="font-mono text-gray-300">
              {node.path === "/" ? "/" : node.path.split("/").pop()}
            </span>
            <span className="text-xs text-gray-600 ml-auto font-mono">
              {node.id.slice(0, 8)}
            </span>
          </div>
          {node.children.length > 0 && (
            <TreeView nodes={node.children} depth={depth + 1} />
          )}
        </div>
      ))}
    </div>
  );
}

export default async function AppDetailPage({
  params,
}: {
  params: Promise<{ appId: string }>;
}) {
  const { appId } = await params;

  let app;
  let tree: AppNodeTree[] = [];

  try {
    app = await client.getApp(appId);
    tree = await client.getAppTree(appId);
  } catch {
    notFound();
  }

  const domain =
    (app.config as Record<string, string>)?.domain ?? "CLOUD";

  const DOMAIN_BADGE_COLORS: Record<string, string> = {
    CLOUD: "border-green-500 text-green-400",
    FILESYST: "border-blue-500 text-blue-400",
    ADMIN: "border-red-500 text-red-400",
    SIDEPANEL: "border-purple-500 text-purple-400",
    AGENT_SEAT: "border-yellow-500 text-yellow-400",
  };

  const badgeColor =
    DOMAIN_BADGE_COLORS[domain] ?? "border-gray-500 text-gray-400";

  return (
    <div>
      <Link
        href="/"
        className="text-sm text-gray-500 hover:text-gray-300 mb-4 inline-block"
      >
        &larr; Back to Applications
      </Link>

      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-2xl font-bold">
          {app.display_name ?? app.app_id}
        </h2>
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded-full border ${badgeColor}`}
        >
          {domain}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <h3 className="text-lg font-semibold mb-3">Node Tree</h3>
          <div className="border border-gray-800 rounded-lg p-2">
            {tree.length > 0 ? (
              <TreeView nodes={tree} />
            ) : (
              <p className="text-gray-500 text-sm p-4">
                No nodes found for this application.
              </p>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-3">Details</h3>
          <div className="border border-gray-800 rounded-lg p-4 space-y-3 text-sm">
            <div>
              <span className="text-gray-500">App ID:</span>
              <span className="ml-2 font-mono">{app.app_id}</span>
            </div>
            <div>
              <span className="text-gray-500">Domain:</span>
              <span className="ml-2">{domain}</span>
            </div>
            <div>
              <span className="text-gray-500">Root Node:</span>
              <span className="ml-2 font-mono text-xs">
                {app.root_node_id?.slice(0, 12) ?? "none"}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Created:</span>
              <span className="ml-2 text-xs">
                {new Date(app.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
