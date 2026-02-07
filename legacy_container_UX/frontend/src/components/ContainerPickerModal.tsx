import { X, FolderPlus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { modalClasses, inputClasses, buttonClasses } from '../lib/workspace-theme';
import type { ResourceLink } from '../lib/api';

type ContainerKind = 'agent' | 'tool' | 'source';

interface ContainerPickerModalProps {
  isOpen: boolean;
  containerType: ContainerKind;
  resources: (ResourceLink & { title?: string; description?: string })[];
  onSelect: (resource: ResourceLink) => void;
  onClose: () => void;
}

export function ContainerPickerModal({ isOpen, containerType, resources, onSelect, onClose }: ContainerPickerModalProps) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const term = search.toLowerCase();
    return resources
      .filter((r) => r.resource_type === containerType)
      .filter((r) =>
        !term
          ? true
          : (r.title || '').toLowerCase().includes(term) || (r.description || '').toLowerCase().includes(term)
      );
  }, [resources, containerType, search]);

  if (!isOpen) return null;

  return createPortal(
    <div className={modalClasses.overlay}>
      <div
        className={`${modalClasses.content} max-w-xl`}
        role="dialog"
        aria-modal="true"
        aria-label={`Select ${containerType}`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <FolderPlus className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Select {containerType.charAt(0).toUpperCase() + containerType.slice(1)}</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close picker">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-3">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={inputClasses}
            placeholder={`Search ${containerType}s by title or description`}
          />

          <div className="max-h-[320px] overflow-y-auto divide-y divide-slate-800 rounded-lg border border-slate-800 bg-slate-900/60">
            {filtered.length === 0 && (
              <div className="p-4 text-sm text-slate-400">No {containerType}s available yet.</div>
            )}

            {filtered.map((res) => (
              <button
                key={res.link_id || `${res.resource_type}-${res.resource_id}`}
                className="w-full text-left p-4 hover:bg-slate-800/80 transition-colors"
                onClick={() => onSelect(res)}
              >
                <div className="text-white font-medium">{res.title || res.resource_id}</div>
                {res.description && (
                  <div className="text-sm text-slate-400 line-clamp-2">{res.description}</div>
                )}
                <div className="text-xs text-slate-500 mt-1">ID: {res.resource_id}</div>
              </button>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button onClick={onClose} className={buttonClasses.secondary}>Cancel</button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
