/**
 * AddToolInstanceModal - Modal for adding tool instances to sessions
 * 
 * Allows users to attach system or custom tools to a specific session
 * with optional config overrides.
 */

import React, { useState, useEffect } from 'react';
import { useWorkspaceStore } from '../../lib/workspace-store';
import { toast } from '../../lib/toast-store';

interface AddToolInstanceModalProps {
  isOpen: boolean;
  sessionId: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export function AddToolInstanceModal({ isOpen, sessionId, onClose, onSuccess }: AddToolInstanceModalProps) {
  const [selectedToolId, setSelectedToolId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [configJson, setConfigJson] = useState('{}');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    availableTools,
    userCustomTools,
    loadAvailableTools,
    loadUserCustomDefinitions,
    addResourceLink,
    userIdentity
  } = useWorkspaceStore();

  // Load tools on mount
  useEffect(() => {
    if (isOpen) {
      loadAvailableTools();
      loadUserCustomDefinitions(userIdentity?.id || 'user');
    }
  }, [isOpen, loadAvailableTools, loadUserCustomDefinitions, userIdentity]);

  const allTools = [
    ...availableTools.map(t => ({ id: t.name, name: t.name, category: t.category, type: 'system' as const })),
    ...userCustomTools.map(t => ({ id: t.tool_id, name: t.name, category: 'custom', type: 'custom' as const })),
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedToolId) {
      toast.error('Please select a tool');
      return;
    }

    if (!displayName.trim()) {
      toast.error('Display name is required');
      return;
    }

    // Validate JSON config
    let configOverrides: Record<string, unknown> | undefined
    try {
      const parsed = JSON.parse(configJson)
      configOverrides = Object.keys(parsed).length > 0 ? parsed : undefined
    } catch (err) {
      toast.error('Invalid JSON configuration')
      return
    }

    setIsSubmitting(true);
    try {
      await addResourceLink(sessionId, {
        resource_type: 'tool',
        resource_id: selectedToolId,
        description: displayName.trim(),
        preset_params: configOverrides,
      });

      toast.success(`Tool "${displayName}" added to session`);
      onSuccess?.();
      handleClose();
    } catch (error) {
      console.error('Failed to add tool instance:', error);
      // Error toast already shown by API client
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedToolId('');
    setDisplayName('');
    setConfigJson('{}');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[10001] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Add Tool to Session</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Attach a tool instance to this session
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Tool Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tool *
            </label>
            <select
              value={selectedToolId}
              onChange={(e) => {
                setSelectedToolId(e.target.value);
                const tool = allTools.find(t => t.id === e.target.value);
                if (tool && !displayName) {
                  setDisplayName(tool.name);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              aria-label="Tool"
              required
            >
              <option value="">Select a tool...</option>
              <optgroup label="System Tools">
                {allTools.filter(t => t.type === 'system').map((tool) => (
                  <option key={tool.id} value={tool.id}>
                    {tool.name} ({tool.category})
                  </option>
                ))}
              </optgroup>
              <optgroup label="Your Custom Tools">
                {allTools.filter(t => t.type === 'custom').map((tool) => (
                  <option key={tool.id} value={tool.id}>
                    {tool.name} (custom)
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Display Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Display Name *
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="CSV Exporter #1"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              How this tool instance will appear in the session
            </p>
          </div>

          {/* Config Overrides */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Config Overrides (JSON)
            </label>
            <textarea
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              placeholder='{"param": "value"}'
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Optional: Override default tool configuration for this session
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Adding...' : 'Add Tool'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
