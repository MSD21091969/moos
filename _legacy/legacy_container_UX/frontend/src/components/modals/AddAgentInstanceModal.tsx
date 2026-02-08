/**
 * AddAgentInstanceModal - Modal for adding agent instances to sessions
 * 
 * Allows users to attach system or custom agents to a specific session
 * with optional model/prompt overrides and activation.
 */

import React, { useState, useEffect } from 'react';
import { useWorkspaceStore } from '../../lib/workspace-store';
import { toast } from '../../lib/toast-store';

interface AddAgentInstanceModalProps {
  isOpen: boolean;
  sessionId: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const AVAILABLE_MODELS = [
  { id: 'gpt-4', name: 'GPT-4' },
  { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus' },
  { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet' },
];

export function AddAgentInstanceModal({ isOpen, sessionId, onClose, onSuccess }: AddAgentInstanceModalProps) {
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [modelOverride, setModelOverride] = useState('');
  const [promptOverride, setPromptOverride] = useState('');
  const [setAsActive, setSetAsActive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    availableAgents,
    userCustomAgents,
    loadAvailableAgents,
    loadUserCustomDefinitions,
    addResourceLink,
    userIdentity
  } = useWorkspaceStore();

  // Load agents on mount
  useEffect(() => {
    if (isOpen) {
      loadAvailableAgents(sessionId);
      loadUserCustomDefinitions(userIdentity?.id || 'user');
    }
  }, [isOpen, sessionId, loadAvailableAgents, loadUserCustomDefinitions, userIdentity]);

  const allAgents = [
    ...availableAgents.filter(a => a.is_system).map(a => ({ 
      id: a.agent_id, 
      name: a.name, 
      description: a.description,
      type: 'system' as const 
    })),
    ...userCustomAgents.map(a => ({ 
      id: a.agent_id, 
      name: a.name, 
      description: a.description,
      type: 'custom' as const 
    })),
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedAgentId) {
      toast.error('Please select an agent');
      return;
    }

    if (!displayName.trim()) {
      toast.error('Display name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      await addResourceLink(sessionId, {
        resource_type: 'agent',
        resource_id: selectedAgentId,
        description: displayName.trim(),
        metadata: {
          model_override: modelOverride || undefined,
          system_prompt_override: promptOverride.trim() || undefined,
        },
      });

      toast.success(`Agent "${displayName}" added to session`);
      onSuccess?.();
      handleClose();
    } catch (error) {
      console.error('Failed to add agent instance:', error);
      // Error toast already shown by API client
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedAgentId('');
    setDisplayName('');
    setModelOverride('');
    setPromptOverride('');
    setSetAsActive(true);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[10001] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Add Agent to Session</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Attach an agent instance to this session
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Agent Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Agent *
            </label>
            <select
              value={selectedAgentId}
              onChange={(e) => {
                setSelectedAgentId(e.target.value);
                const agent = allAgents.find(a => a.id === e.target.value);
                if (agent && !displayName) {
                  setDisplayName(agent.name);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              aria-label="Agent"
              required
            >
              <option value="">Select an agent...</option>
              <optgroup label="System Agents">
                {allAgents.filter(a => a.type === 'system').map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Your Custom Agents">
                {allAgents.filter(a => a.type === 'custom').map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </optgroup>
            </select>
            {selectedAgentId && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {allAgents.find(a => a.id === selectedAgentId)?.description}
              </p>
            )}
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
              placeholder="Data Analyst #1"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              How this agent instance will appear in the session
            </p>
          </div>

          {/* Model Override */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Model Override (optional)
            </label>
            <select
              value={modelOverride}
              onChange={(e) => setModelOverride(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              aria-label="Model Override"
            >
              <option value="">Use agent's default model</option>
              {AVAILABLE_MODELS.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          {/* System Prompt Override */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              System Prompt Override (optional)
            </label>
            <textarea
              value={promptOverride}
              onChange={(e) => setPromptOverride(e.target.value)}
              placeholder="Leave empty to use agent's default system prompt"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Set as Active */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="setAsActive"
              checked={setAsActive}
              onChange={(e) => setSetAsActive(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label htmlFor="setAsActive" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Set as active agent for this session
            </label>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 ml-6">
            Only one agent can be active per session
          </p>

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
              {isSubmitting ? 'Adding...' : 'Add Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
