import { DataServerClient } from "@collider/api-client";
import { Card } from "@collider/shared-ui";
import Link from "next/link";

const client = new DataServerClient("http://localhost:8000");

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let applications;
  try {
    applications = await client.listApps();
  } catch {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-4">Applications</h2>
        <div className="p-6 rounded-lg border border-red-500/50 bg-red-500/10 text-red-300">
          <p className="font-medium">Unable to connect to Data Server</p>
          <p className="text-sm mt-1 text-red-400">
            Make sure ColliderDataServer is running on port 8000.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Applications</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {applications.map((app) => (
          <Link key={app.app_id} href={`/apps/${app.app_id}`}>
            <Card
              appId={app.app_id}
              displayName={app.display_name}
              domain={
                (app.config as Record<string, string>)?.domain ?? "CLOUD"
              }
            />
          </Link>
        ))}
      </div>
      {applications.length === 0 && (
        <p className="text-gray-500 text-center py-12">
          No applications found. Run the seeder to populate the database.
        </p>
      )}
    </div>
  );
}
