export function CloudNodeTree() {
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold text-green-400 mb-3">Cloud Applications</h2>
      <div className="space-y-2 text-sm">
        <div className="p-3 bg-gray-800 rounded">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">my-tiny-data-collider</div>
            <span className="px-2 py-1 text-xs bg-green-600 rounded">Active</span>
          </div>
          <div className="text-xs text-gray-500">
            <div>Deployment: production</div>
            <div>Containers: 3</div>
          </div>
        </div>
        <div className="p-3 bg-gray-800 rounded">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">data-processor-v2</div>
            <span className="px-2 py-1 text-xs bg-yellow-600 rounded">Pending</span>
          </div>
          <div className="text-xs text-gray-500">
            <div>Deployment: staging</div>
            <div>Containers: 2</div>
          </div>
        </div>
      </div>
    </div>
  );
}
