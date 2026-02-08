import { useState } from 'react';
import { useWorkspaceStore } from '../lib/workspace-store';
import { HexColorPicker } from 'react-colorful';
import { X, Check } from 'lucide-react';
import { FORM_STYLES, FORM_LAYOUT } from '../lib/form-system';

/**
 * ContainerQuickEditForm - Unified edit form for all container types
 * 
 * Edits ResourceLink fields (persisted to Firestore):
 * - description (display title)
 * - metadata.color (theme color)
 * - preset_params (type-specific: role for agents, category for tools, source_type for sources)
 * - enabled (active/disabled)
 * 
 * Works for: Session, Agent, Tool, Source
 * 
 * NOTE: This form calls updateResourceLink which:
 * - Demo Mode: Updates Zustand locally only
 * - Dev/Prod Mode: Optimistically updates Zustand + calls backend API
 */

export type ContainerType = 'session' | 'agent' | 'tool' | 'source';

interface ContainerQuickEditFormProps {
  nodeId: string;
  containerType: ContainerType;
  onClose: () => void;
}

export function ContainerQuickEditForm({ nodeId, containerType, onClose }: ContainerQuickEditFormProps) {
  const { nodes, updateResourceLink, updateContainer } = useWorkspaceStore();
  const node = nodes.find((n) => n.id === nodeId);
  const nodeData = node?.data as Record<string, unknown> | undefined;

  // Extract current values (handling both ResourceLink and legacy formats)
  const currentTitle = (nodeData?.title || nodeData?.name || nodeData?.description || '') as string;
  const resourceId = (nodeData?.resource_id || nodeData?.id) as string;
  
  const currentColor = (
    (nodeData?.themeColor) || 
    ((nodeData?.metadata as Record<string, unknown>)?.color) || 
    '#3b82f6'
  ) as string;
  const currentEnabled = nodeData?.enabled !== false;
  
  // Type-specific fields from preset_params
  const presetParams = (nodeData?.presetParams as Record<string, unknown>) || {};
  const currentRole = (presetParams.role || nodeData?.role || '') as string;
  const currentCategory = (presetParams.category || nodeData?.category || '') as string;
  const currentSourceType = (presetParams.source_type || 'data') as string;

  const [title, setTitle] = useState(currentTitle);
  const [themeColor, setThemeColor] = useState(currentColor);
  const [enabled, setEnabled] = useState(currentEnabled);
  const [role, setRole] = useState(currentRole);
  const [category, setCategory] = useState(currentCategory);
  const [sourceType, setSourceType] = useState(currentSourceType);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (!nodeData) return;
    setIsSaving(true);

    try {
      // 1. Update Container (Title)
      // "title descr is container object field data"
      if (title !== currentTitle) {
        await updateContainer(resourceId, { title });
      }

      // 2. Update ResourceLink (Metadata, Params, Enabled)
      // "color is res. link"
      const currentMetadata = (nodeData.metadata as Record<string, unknown>) || {};
      
      const updates: {
        description?: string;
        preset_params?: Record<string, unknown>;
        metadata?: Record<string, unknown>;
        enabled?: boolean;
      } = {
        // We do NOT update description (alias) here, as we updated the container title.
        // Unless we want to enforce alias = title?
        // For now, we respect the split.
        metadata: {
          ...currentMetadata,
          color: themeColor,
        },
        enabled,
      };

      // Build preset_params based on container type
      if (containerType === 'agent') {
        updates.preset_params = { ...presetParams, role };
      } else if (containerType === 'tool') {
        updates.preset_params = { ...presetParams, category };
      } else if (containerType === 'source') {
        updates.preset_params = { ...presetParams, source_type: sourceType };
      }

      // Call the store action (handles optimistic update + backend sync)
      // updateResourceLink(containerId, linkId, updates)
      // We need the parent container ID (active session) and the link ID (which is usually the node ID or derived from it)
      // Assuming nodeId IS the linkId for now, and we are in activeContainerId
      const activeContainerId = useWorkspaceStore.getState().activeContainerId;
      if (activeContainerId) {
        await updateResourceLink(activeContainerId, nodeId, updates);
      } else {
        console.warn('Cannot update resource link: No active container');
      }
      onClose();
    } catch (error) {
      console.error('Failed to save:', error);
      // TODO: Show error toast
    } finally {
      setIsSaving(false);
    }
  };

  // Prevent menu closing when interacting with form
  const stopPropagation = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
  };

  // Field wrapper style
  const fieldStyle = FORM_STYLES.fieldContainer;

  return (
    <div 
      className={`${FORM_LAYOUT.container}`}
      onClick={stopPropagation}
      onKeyDown={stopPropagation}
    >
      {/* Title */}
      <div className={fieldStyle}>
        <label className={FORM_STYLES.label}>Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={FORM_STYLES.input}
          placeholder="Enter title..."
          autoFocus
        />
      </div>

      {/* Role (for agents) */}
      {containerType === 'agent' && (
        <div className={fieldStyle}>
          <label className={FORM_STYLES.label}>Role</label>
          <input
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className={FORM_STYLES.input}
            placeholder="e.g., Analysis, Planning, Research..."
          />
        </div>
      )}

      {/* Category (for tools) */}
      {containerType === 'tool' && (
        <div className={fieldStyle}>
          <label className={FORM_STYLES.label}>Category</label>
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className={FORM_STYLES.input}
            placeholder="e.g., Data, Travel, Development..."
          />
        </div>
      )}

      {/* Source Type (for sources) */}
      {containerType === 'source' && (
        <div className={fieldStyle}>
          <label className={FORM_STYLES.label} id="source-type-label">Source Type</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className={FORM_STYLES.select}
            aria-labelledby="source-type-label"
          >
            <option value="data">Data</option>
            <option value="api">API</option>
            <option value="database">Database</option>
            <option value="file">File</option>
            <option value="memory">Memory</option>
          </select>
        </div>
      )}

      {/* Color Picker */}
      <div className={fieldStyle}>
        <label className={FORM_STYLES.label}>Color</label>
        <div className="flex items-center gap-2">
          <div 
            className={`w-8 h-8 rounded border border-slate-600`}
            style={{ backgroundColor: themeColor }}
            aria-label={`Current color: ${themeColor}`}
          />
          <input
            type="text"
            value={themeColor}
            onChange={(e) => setThemeColor(e.target.value)}
            className={`${FORM_STYLES.input} flex-1 font-mono text-xs`}
            placeholder="#3b82f6"
          />
        </div>
        <div className="mt-2">
          <HexColorPicker color={themeColor} onChange={setThemeColor} />
        </div>
      </div>

      {/* Enabled Toggle */}
      <div className={fieldStyle}>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
          />
          <span className={FORM_STYLES.label}>Enabled</span>
        </label>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-slate-700">
        <button
          onClick={onClose}
          disabled={isSaving}
          className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-colors flex items-center gap-1 disabled:opacity-50"
        >
          <X className="w-3 h-3" />
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-wait"
        >
          <Check className="w-3 h-3" />
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  );
}
