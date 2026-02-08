import { useState } from 'react';
import { useWorkspaceStore } from '../lib/workspace-store';
import { SessionVisualState } from '../lib/types';
import { HexColorPicker } from 'react-colorful';
import { X, Check, ChevronRight } from 'lucide-react';
import { FORM_STYLES, FORM_LAYOUT } from '../lib/form-system';
import {
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
} from './ui/ContextMenu';

interface SessionQuickEditFormProps {
  sessionId: string;
  onClose: () => void;
}

export function SessionQuickEditForm({ sessionId, onClose }: SessionQuickEditFormProps) {
  const { 
    nodes, 
    updateNodeData, 
    updateContainer, 
    activeContainerId, 
    userSessionId, 
    containerRegistry, 
    updateResourceLink 
  } = useWorkspaceStore();
  const sessionNode = nodes.find((n) => n.id === sessionId);
  const sessionData = sessionNode?.data as SessionVisualState | undefined;

  const [title, setTitle] = useState(sessionData?.title || '');
  const [description, setDescription] = useState(sessionData?.description || '');
  const [sessionType, setSessionType] = useState<'chat' | 'analysis' | 'workflow' | 'simulation'>(sessionData?.sessionType || 'chat');
  const [status, setStatus] = useState<'active' | 'completed' | 'expired' | 'archived'>(sessionData?.status || 'active');
  const [tags, setTags] = useState<string[]>(sessionData?.tags || []);
  const [tagInput, setTagInput] = useState('');
  const [themeColor, setThemeColor] = useState(sessionData?.themeColor || '#3b82f6');

  const handleSave = async () => {
    if (!sessionData) return;

    // Add any pending tag in the input
    const finalTags = [...tags];
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      finalTags.push(tagInput.trim());
    }

    const updates: Partial<SessionVisualState> = {
      title,
      description,
      sessionType,
      status,
      tags: finalTags,
      themeColor,
      updatedAt: new Date().toISOString(),
    };

    // Update both Node and Session store to keep them in sync
    updateNodeData(sessionId, { ...sessionData, ...updates });
    await updateContainer(sessionId, updates);

    // ALSO Update ResourceLink in parent container (for color/metadata sync)
    // This ensures the color persists in the parent's list of resources
    const parentId = activeContainerId || userSessionId;
    if (parentId && containerRegistry[parentId]) {
        const resource = containerRegistry[parentId].resources.find(r => r.instance_id === sessionId || r.resource_id === sessionId);
        if (resource && resource.link_id) {
            // Merge new color into metadata
            const newMetadata = { ...(resource.metadata as any), color: themeColor };
            await updateResourceLink(parentId, resource.link_id, { 
                description, 
                metadata: newMetadata 
            });
        }
    }
    
    onClose();
  };

  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!tags.includes(tagInput.trim())) {
        setTags([...tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  // Prevent menu closing when interacting with form
  const stopPropagation = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
  };

  return (
    <div 
      className={`${FORM_LAYOUT.container}`}
      onClick={stopPropagation}
      onKeyDown={stopPropagation}
    >
      {/* Title */}
      <div className={FORM_STYLES.fieldContainer}>
        <label className={FORM_STYLES.label}>Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={FORM_STYLES.input}
          placeholder="Session Title"
          autoFocus
        />
      </div>

      {/* Description */}
      <div className={FORM_STYLES.fieldContainer}>
        <label className={FORM_STYLES.label}>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={FORM_STYLES.textarea}
          rows={2}
          placeholder="Add a description..."
        />
      </div>

      {/* Type & Status Row */}
      <div className={FORM_STYLES.fieldGrid}>
        <div className={FORM_STYLES.fieldContainer}>
          <label className={FORM_STYLES.label}>Type</label>
          <div className="relative">
            <select
              value={sessionType}
              onChange={(e) => setSessionType(e.target.value as any)}
              className={FORM_STYLES.select}
              aria-label="Session Type"
            >
              <option value="chat">Chat</option>
              <option value="analysis">Analysis</option>
              <option value="workflow">Workflow</option>
              <option value="simulation">Simulation</option>
            </select>
            <ChevronRight className={FORM_STYLES.selectIcon} />
          </div>
        </div>

        <div className={FORM_STYLES.fieldContainer}>
          <label className={FORM_STYLES.label}>Status</label>
          <div className="relative">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as any)}
              className={FORM_STYLES.select}
              aria-label="Session Status"
            >
              <option value="active">Active</option>
              <option value="completed">Done</option>
              <option value="archived">Archived</option>
            </select>
            <ChevronRight className={FORM_STYLES.selectIcon} />
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className={FORM_STYLES.fieldContainer}>
        <label className={FORM_STYLES.label}>Tags</label>
        <div className={FORM_STYLES.tagContainer}>
          {tags.map(tag => (
            <span key={tag} className={FORM_STYLES.tag}>
              {tag}
              <button onClick={() => removeTag(tag)} className="hover:text-white" title="Remove tag">
                <X className="w-2.5 h-2.5" />
              </button>
            </span>
          ))}
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleAddTag}
            className={FORM_STYLES.tagInput}
            placeholder={tags.length === 0 ? "Add tag..." : ""}
          />
        </div>
      </div>

      {/* Color Picker - 3rd Level Submenu */}
      <ContextMenuSub>
        <ContextMenuSubTrigger className="flex items-center gap-2 justify-between px-2 py-1.5 hover:bg-slate-700/50 rounded transition-colors">
          <span className={FORM_STYLES.label}>Color</span>
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded border border-slate-600"
              ref={(el) => { if (el) el.style.backgroundColor = themeColor; }}
            />
            <button
              type="button"
              onClick={handleSave}
              className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              aria-label="Save Color"
            >
              <Check className="w-3 h-3" />
            </button>
          </div>
        </ContextMenuSubTrigger>
        <ContextMenuSubContent className="p-0 bg-[rgba(15,23,42,0.85)] border-slate-700">
          <div className="p-3">
            <HexColorPicker color={themeColor} onChange={setThemeColor} />
            <div className="mt-2 text-xs text-slate-400 text-center">{themeColor}</div>
          </div>
        </ContextMenuSubContent>
      </ContextMenuSub>
    </div>
  );
}

