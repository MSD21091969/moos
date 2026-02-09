export function AgentDirectoryView() {
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold text-blue-400 mb-3">.agent Directory</h2>
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 p-2 bg-gray-800 rounded">
          <span className="text-blue-400">📄</span>
          <span>manifest.json</span>
        </div>
        <div className="flex items-center gap-2 p-2 bg-gray-800 rounded">
          <span className="text-blue-400">📄</span>
          <span>config.json</span>
        </div>
        <div className="flex items-center gap-2 p-2 bg-gray-800 rounded">
          <span className="text-blue-400">📁</span>
          <span>knowledge/</span>
        </div>
      </div>
      <div className="mt-4 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span>Synced with backend</span>
        </div>
      </div>
    </div>
  );
}
