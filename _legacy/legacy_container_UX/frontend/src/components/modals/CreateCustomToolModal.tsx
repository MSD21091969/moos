/**
 * CreateCustomToolModal - Modal for creating user-level custom tools
 * 
 * Allows PRO/ENTERPRISE users to create custom tool configurations
 * that wrap builtin tools with preset parameters.
 */

import React, { useState } from 'react';
import { useWorkspaceStore } from '../../lib/workspace-store';
import { toast } from '../../lib/toast-store';

interface CreateCustomToolModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const BUILTIN_TOOLS = [
  { name: 'export_csv', category: 'export', description: 'Export data as CSV file' },
  { name: 'export_json', category: 'export', description: 'Export data as JSON file' },
  { name: 'regex_replace', category: 'text', description: 'Find and replace using regex patterns' },
  { name: 'text_transform', category: 'text', description: 'Transform text (uppercase, lowercase, etc.)' },
  { name: 'data_filter', category: 'transform', description: 'Filter data based on conditions' },
  { name: 'data_sort', category: 'transform', description: 'Sort data by fields' },
];

export function CreateCustomToolModal({ isOpen, onClose, onSuccess }: CreateCustomToolModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedBuiltin, setSelectedBuiltin] = useState('');
  const [configJson, setConfigJson] = useState('{}');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const createUserCustomTool = useWorkspaceStore((state) => state.createUserCustomTool);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      toast.error('Tool name is required');
      return;
    }
    
    if (!selectedBuiltin) {
      toast.error('Please select a builtin tool to wrap');
      return;
    }

    // Validate JSON config
    let config: Record<string, unknown>
    try {
      config = JSON.parse(configJson)
    } catch (err) {
      toast.error('Invalid JSON configuration')
      return
    }

    setIsSubmitting(true);
    try {
      await createUserCustomTool({
        name: name.trim(),
        description: description.trim() || `Custom ${selectedBuiltin} configuration`,
        builtin_tool_name: selectedBuiltin,
        config,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      });

      toast.success(`Tool "${name}" created successfully`);
      onSuccess?.();
      handleClose();
    } catch (error) {
      console.error('Failed to create custom tool:', error);
      // Error toast already shown by API client
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setSelectedBuiltin('');
    setConfigJson('{}');
    setTags('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[10001] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Create Custom Tool</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Wrap a builtin tool with custom configuration
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Tool Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tool Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Custom CSV Exporter"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Exports data with custom delimiter and headers"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Builtin Tool Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Builtin Tool *
            </label>
            <select
              value={selectedBuiltin}
              onChange={(e) => setSelectedBuiltin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              aria-label="Builtin Tool"
              required
            >
              <option value="">Select a tool to wrap...</option>
              {BUILTIN_TOOLS.map((tool) => (
                <option key={tool.name} value={tool.name}>
                  {tool.name} ({tool.category}) - {tool.description}
                </option>
              ))}
            </select>
          </div>

          {/* Config JSON Editor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Configuration (JSON)
            </label>
            <textarea
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              placeholder='{"delimiter": ",", "include_headers": true}'
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Tool-specific configuration as valid JSON
            </p>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="export, csv, custom"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Tier Gate Notice */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              🔒 Custom tools require <strong>PRO</strong> or <strong>ENTERPRISE</strong> tier
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
              {isSubmitting ? 'Creating...' : 'Create Tool'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
