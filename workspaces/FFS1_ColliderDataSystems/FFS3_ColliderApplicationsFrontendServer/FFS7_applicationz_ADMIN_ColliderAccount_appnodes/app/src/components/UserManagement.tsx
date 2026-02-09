export function UserManagement() {
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold text-red-400 mb-3">User Management</h2>
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between p-3 bg-gray-800 rounded">
          <div>
            <div className="font-medium">admin@collider.com</div>
            <div className="text-xs text-gray-500">Administrator</div>
          </div>
          <button className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 rounded">Edit</button>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-800 rounded">
          <div>
            <div className="font-medium">user@collider.com</div>
            <div className="text-xs text-gray-500">User</div>
          </div>
          <button className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 rounded">Edit</button>
        </div>
      </div>
      <button className="mt-3 w-full px-3 py-2 text-sm bg-red-600 hover:bg-red-700 rounded">
        + Add User
      </button>
    </div>
  );
}
