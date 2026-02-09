import React from "react";
import "~/style.css";

function Popup() {
  const handleOpenSidepanel = () => {
    chrome.sidePanel
      .open({ windowId: chrome.windows.WINDOW_ID_CURRENT })
      .catch(console.error);
  };

  return (
    <div className="w-64 p-4 bg-gray-900 text-gray-100">
      <h1 className="text-lg font-semibold mb-2">Collider</h1>
      <p className="text-sm text-gray-400 mb-4">
        Multi-agent Chrome Extension for the Collider ecosystem.
      </p>
      <button
        onClick={handleOpenSidepanel}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-2 rounded"
      >
        Open Sidepanel
      </button>
      <div className="mt-3 text-xs text-gray-500">
        <div>Data Server: localhost:8000</div>
        <div>GraphTool: localhost:8001</div>
        <div>VectorDB: localhost:8002</div>
      </div>
    </div>
  );
}

export default Popup;
