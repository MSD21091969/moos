import { User } from 'lucide-react';
import type { NodeProps } from '@xyflow/react';

export function UserStubNode({ data }: NodeProps) {
  const title = (data as any)?.title || (data as any)?.label || 'User';
  const description = (data as any)?.description;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2 shadow-sm text-left w-44">
      <div className="flex items-center gap-2 text-slate-100">
        <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center">
          <User className="h-4 w-4 text-blue-400" />
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate" title={title}>{title}</div>
          {description && (
            <div className="text-xs text-slate-400 truncate" title={description}>{description}</div>
          )}
        </div>
      </div>
      <div className="mt-2 text-[11px] uppercase tracking-wide text-slate-500">ACL Stub</div>
    </div>
  );
}
