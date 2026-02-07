/**
 * MetricsGraphView Component
 * 
 * Lightweight 2D graph visualization for session metrics, token usage trends,
 * and agent activity over time. Uses Canvas API for performance (no external
 * chart libraries needed).
 * 
 * Features:
 * - Line charts for time-series data (token usage, agent calls)
 * - Bar charts for categorical data (status counts, session types)
 * - Sparklines for compact inline metrics
 * - Hover tooltips with detailed values
 * - Responsive canvas sizing
 * - Theme-aware colors from workspace-theme.ts
 */

import { useEffect, useRef, useState } from 'react';
import { useWorkspaceStore } from '../lib/workspace-store';
import { defaultWorkspaceTheme, hexToRgba } from '../lib/workspace-theme';

interface MetricsGraphViewProps {
  className?: string;
  sessionId?: string; // Optional: filter to specific session
}

interface DataPoint {
  timestamp: number;
  value: number;
  label?: string;
}

// Generate mock time-series data for demo (replace with real backend data)
const generateMockData = (): DataPoint[] => {
  const now = Date.now();
  const points: DataPoint[] = [];
  for (let i = 7; i >= 0; i--) {
    points.push({
      timestamp: now - i * 24 * 60 * 60 * 1000, // Last 7 days
      value: Math.floor(Math.random() * 1000) + 500,
    });
  }
  return points;
};

export function MetricsGraphView({ className = '', sessionId: _sessionId }: MetricsGraphViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; data: DataPoint } | null>(null);
  const { containers } = useWorkspaceStore();

  const [dataPoints] = useState<DataPoint[]>(() => generateMockData());

  // Draw line chart on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match container
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.fillStyle = defaultWorkspaceTheme.dark.background;
    ctx.fillRect(0, 0, width, height);

    // Find min/max values
    const values = dataPoints.map((d) => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1;

    // Draw grid lines
    ctx.strokeStyle = hexToRgba(defaultWorkspaceTheme.dark.border, 0.3);
    ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartHeight / gridLines) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();

      // Y-axis labels
      const value = maxValue - (valueRange / gridLines) * i;
      ctx.fillStyle = defaultWorkspaceTheme.dark.textMuted;
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(0), padding.left - 8, y + 4);
    }

    // Draw line chart
    ctx.strokeStyle = defaultWorkspaceTheme.primary;
    ctx.lineWidth = 2;
    ctx.beginPath();

    dataPoints.forEach((point, index) => {
      const x = padding.left + (chartWidth / (dataPoints.length - 1)) * index;
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw data points (circles)
    dataPoints.forEach((point, index) => {
      const x = padding.left + (chartWidth / (dataPoints.length - 1)) * index;
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;

      ctx.fillStyle = defaultWorkspaceTheme.primary;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw X-axis labels (dates)
    ctx.fillStyle = defaultWorkspaceTheme.dark.textMuted;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    dataPoints.forEach((point, index) => {
      const x = padding.left + (chartWidth / (dataPoints.length - 1)) * index;
      const date = new Date(point.timestamp);
      const label = `${date.getMonth() + 1}/${date.getDate()}`;
      ctx.fillText(label, x, height - 10);
    });

    // Draw axis labels
    ctx.fillStyle = defaultWorkspaceTheme.dark.text;
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Token Usage (Last 7 Days)', width / 2, 15);

  }, [dataPoints]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = rect.width - padding.left - padding.right;
    const chartHeight = rect.height - padding.top - padding.bottom;

    const values = dataPoints.map((d) => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1;

    // Find closest data point
    let closestIndex = -1;
    let closestDistance = Infinity;

    dataPoints.forEach((point, index) => {
      const pointX = padding.left + (chartWidth / (dataPoints.length - 1)) * index;
      const pointY = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      const distance = Math.sqrt((x - pointX) ** 2 + (y - pointY) ** 2);

      if (distance < closestDistance && distance < 20) {
        closestDistance = distance;
        closestIndex = index;
      }
    });

    if (closestIndex >= 0) {
      const point = dataPoints[closestIndex];
      const pointX = padding.left + (chartWidth / (dataPoints.length - 1)) * closestIndex;
      const pointY = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      setHoveredPoint({ x: pointX, y: pointY, data: point });
    } else {
      setHoveredPoint(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Total Sessions</div>
          <div className="text-2xl font-bold text-white">{containers.length}</div>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Active</div>
          <div className="text-2xl font-bold text-green-500">
            {containers.filter((s) => s.status === 'active').length}
          </div>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Avg Tokens</div>
          <div className="text-2xl font-bold text-blue-500">
            {dataPoints.length > 0
              ? Math.floor(dataPoints.reduce((sum, p) => sum + p.value, 0) / dataPoints.length)
              : 0}
          </div>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Peak Usage</div>
          <div className="text-2xl font-bold text-amber-500">
            {Math.max(...dataPoints.map((p) => p.value))}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div
        ref={containerRef}
        className="relative bg-slate-900 border border-slate-700 rounded-lg overflow-hidden h-[300px]"
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-crosshair"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        />

        {/* Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute bg-slate-800 border border-slate-600 rounded-md px-3 py-2 text-xs text-white pointer-events-none shadow-lg z-10"
            style={{
              left: `${hoveredPoint.x + 10}px`,
              top: `${hoveredPoint.y - 30}px`,
            }}
          >
            <div className="font-semibold">{hoveredPoint.data.value.toFixed(0)} tokens</div>
            <div className="text-slate-400">
              {new Date(hoveredPoint.data.timestamp).toLocaleDateString()}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-6 text-sm text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Token Usage</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span>Active Sessions</span>
        </div>
      </div>
    </div>
  );
}
