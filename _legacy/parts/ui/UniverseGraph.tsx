import React from "react";
// This assumes React Flow or similar, but simplified for the "Kit" as a pure structure.

interface ContainerNode {
  id: string;
  name: string;
  status: "occupied" | "draft" | "shared";
  x: number;
  y: number;
  color?: string;
}

interface UniverseGraphProps {
  nodes: ContainerNode[];
  onNodeClick: (id: string) => void;
}

export function UniverseGraph({ nodes, onNodeClick }: UniverseGraphProps) {
  // Placeholder visualization using standard HTML/SVG for valid React code
  // In a real app, this would be React Flow <ReactFlow nodes={...} />

  return (
    <div className="w-full h-full relative overflow-hidden bg-slate-950">
      {/* Grid Background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative w-full h-full flex items-center justify-center p-20">
        <div className="relative w-full max-w-4xl h-[600px]">
          {nodes.map((node) => (
            <div
              key={node.id}
              onClick={() => onNodeClick(node.id)}
              className="absolute cursor-pointer transition-all hover:scale-105 active:scale-95 group"
              style={{
                left: `${node.x}%`,
                top: `${node.y}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              {/* Glow Effect */}
              <div
                className={`absolute inset-0 bg-${node.color || "blue-500"} blur-xl opacity-20 group-hover:opacity-40 transition-opacity rounded-full`}
              />

              {/* Node Body */}
              <div className="relative bg-slate-900 border border-slate-700 hover:border-slate-500 rounded-xl p-4 w-48 shadow-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`w-3 h-3 rounded-full bg-${node.color || "blue-500"}`}
                  />
                  <span className="text-slate-200 font-medium truncate">
                    {node.name}
                  </span>
                </div>
                <div className="text-xs text-slate-500 uppercase tracking-wider flex justify-between">
                  <span>{node.status}</span>
                  <span>ID: {node.id.slice(0, 4)}</span>
                </div>
              </div>
            </div>
          ))}

          {/* Central Identity Node */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-slate-800 font-bold text-9xl select-none opacity-5 pointer-events-none">
            YOU
          </div>
        </div>
      </div>

      {/* HUD Overlay (Bottom Left) */}
      <div className="absolute bottom-6 left-6 text-slate-500 text-xs font-mono">
        COORD: 104.22, -42.01 <br />
        UNIVERSE: LOCAL_DEV
      </div>
    </div>
  );
}
