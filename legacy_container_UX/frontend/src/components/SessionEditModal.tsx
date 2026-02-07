/**
 * Session Edit Modal - SIMPLIFIED
 *
 * Modal dialog for editing session METADATA ONLY (title, description, tags, type, status)
 * Tools/Agents/Datasources are managed as nodes inside SessionSpace, not here.
 */

import { Tag, X, FileText, Settings, Activity } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from '../lib/toast-store';
import { useWorkspaceStore } from '../lib/workspace-store';
import { UI_STYLES } from '../lib/ui-styles';
import {
  inputClasses,
  labelClasses,
  modalClasses,
  statusButtonClasses,
} from '../lib/workspace-theme';
import type { SessionVisualState } from '../lib/types';
import { FileBrowser } from './FileBrowser';
import { DataFlowVisualizer } from './DataFlowVisualizer';

interface SessionEditModalProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function SessionEditModal({ sessionId, isOpen, onClose }: SessionEditModalProps) {
  const { nodes, updateNodeData, editingSessionTab, setEditingSessionId } = useWorkspaceStore();
  const sessionNode = nodes.find((n) => n.id === sessionId && n.type === 'session');
  const sessionData = sessionNode?.data as SessionVisualState | undefined;

  const [activeTab, setActiveTab] = useState<'details' | 'files' | 'dataflow'>('details');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [sessionType, setSessionType] = useState<'chat' | 'analysis' | 'workflow'>('chat');
  const [status, setStatus] = useState<'active' | 'completed' | 'expired' | 'archived'>('active');
  const [isSaving, setIsSaving] = useState(false);

  // Sync with global store tab state
  useEffect(() => {
    if (isOpen) {
      setActiveTab(editingSessionTab || 'details');
    }
  }, [isOpen, editingSessionTab]);

  // Update global store when local tab changes
  const handleTabChange = (tab: 'details' | 'files' | 'dataflow') => {
    setActiveTab(tab);
    setEditingSessionId(sessionId, tab);
  };

  // Load session data when modal opens
  useEffect(() => {
    if (isOpen && sessionData) {
      setTitle(sessionData.title ?? 'Untitled Session');
      setDescription(sessionData.description ?? '');
      setTags(sessionData.tags ?? []);
      const allowedTypes = ['chat', 'analysis', 'workflow'] as const;
      const typeValue = sessionData.sessionType;
      setSessionType(
        allowedTypes.includes(typeValue as any)
          ? (typeValue as 'chat' | 'analysis' | 'workflow')
          : 'chat'
      );
      setStatus(sessionData.status ?? 'active');
    }
  }, [isOpen, sessionData]);

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error('Title is required');
      return;
    }

    setIsSaving(true);
    try {
      const updates: Partial<SessionVisualState> = {
        title: title.trim(),
        description: description.trim() || undefined,
        tags,
        sessionType,
        status,
        updatedAt: new Date().toISOString(),
      };

      const mergedData = { ...sessionData, ...updates } as SessionVisualState & Record<string, unknown>;
      updateNodeData(sessionId, { ...mergedData });
      toast.success('Session updated');
      onClose();
    } catch (error) {
      console.error('Failed to save session:', error);
      toast.error('Failed to save session');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={modalClasses.overlay}>
      <div className={`${UI_STYLES.modal.full} max-w-2xl w-full h-[70vh] flex flex-col p-6`}>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-700 shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-white">Session Details</h2>
            <div className="flex bg-slate-800 rounded-lg p-1">
              <button
                onClick={() => handleTabChange('details')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === 'details'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                <Settings className="w-4 h-4" />
                Details
              </button>
              <button
                onClick={() => handleTabChange('files')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === 'files'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                <FileText className="w-4 h-4" />
                Files
              </button>
              <button
                onClick={() => handleTabChange('dataflow')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === 'dataflow'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                <Activity className="w-4 h-4" />
                Data Flow
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
            title="Close session editor"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden py-6">
          {activeTab === 'details' && (
            <div className="space-y-6 h-full overflow-y-auto pr-2">
              {/* Title */}
              <div>
                <label className={labelClasses}>
                  Title <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={inputClasses}
                  placeholder="Session title"
                  autoFocus
                />
              </div>

              {/* Description */}
              <div>
                <label className={labelClasses}>Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={inputClasses}
                  placeholder="Session description"
                  rows={3}
                />
              </div>

              {/* Session Type */}
              <div>
                <label className={labelClasses}>Session Type</label>
                <select
                  value={sessionType}
                  onChange={(e) => setSessionType(e.target.value as typeof sessionType)}
                  className={inputClasses}
                  aria-label="Select session type"
                >
                  <option value="chat">Chat</option>
                  <option value="analysis">Analysis</option>
                  <option value="workflow">Workflow</option>
                </select>
              </div>

              {/* Status */}
              <div>
                <label className={labelClasses}>Status</label>
                <div className="flex gap-2">
                  {(['active', 'completed', 'expired', 'archived'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => setStatus(s)}
                      className={
                        status === s
                          ? statusButtonClasses[s].selected
                          : statusButtonClasses[s].default
                      }
                    >
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className={labelClasses}>Tags</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-blue-600 dark:hover:text-blue-400"
                        title={`Remove ${tag} tag`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className={`flex-1 ${inputClasses}`}
                    placeholder="Add tag and press Enter"
                  />
                  <button onClick={handleAddTag} className={UI_STYLES.button.primary}>
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'files' && (
            <div className="h-full">
              <FileBrowser />
            </div>
          )}

          {activeTab === 'dataflow' && (
            <div className="h-full">
              <DataFlowVisualizer sessionId={sessionId} />
            </div>
          )}
        </div>

        {/* Footer Buttons (Only for Details tab) */}
        {activeTab === 'details' && (
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700 shrink-0">
            <button
              onClick={onClose}
              className={UI_STYLES.button.secondary}
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className={UI_STYLES.button.primary}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

