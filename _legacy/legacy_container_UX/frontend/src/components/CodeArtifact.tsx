/**
 * CodeArtifact Component
 * 
 * Renders code artifacts with Shiki syntax highlighting.
 * Supports copy, download, and apply actions.
 */

import { useEffect, useState, useCallback, memo } from 'react';
import { Copy, Download, Check, Play, FileCode } from 'lucide-react';
import type { CodeArtifact as CodeArtifactType } from '../lib/agents/types';

// Shiki imports - dynamic to avoid SSR issues
let highlighter: unknown = null;

interface CodeArtifactProps {
  artifact: CodeArtifactType;
  onApply?: (artifact: CodeArtifactType) => void;
  className?: string;
}

// Language display names
const LANGUAGE_NAMES: Record<string, string> = {
  typescript: 'TypeScript',
  javascript: 'JavaScript',
  python: 'Python',
  rust: 'Rust',
  go: 'Go',
  java: 'Java',
  cpp: 'C++',
  c: 'C',
  csharp: 'C#',
  html: 'HTML',
  css: 'CSS',
  json: 'JSON',
  yaml: 'YAML',
  markdown: 'Markdown',
  sql: 'SQL',
  bash: 'Bash',
  shell: 'Shell',
  tsx: 'TSX',
  jsx: 'JSX',
};

// Map common aliases
const LANGUAGE_ALIASES: Record<string, string> = {
  ts: 'typescript',
  js: 'javascript',
  py: 'python',
  rs: 'rust',
  cs: 'csharp',
  md: 'markdown',
  yml: 'yaml',
  sh: 'bash',
};

function normalizeLanguage(lang: string): string {
  const lower = lang.toLowerCase();
  return LANGUAGE_ALIASES[lower] ?? lower;
}

export const CodeArtifact = memo(function CodeArtifact({
  artifact,
  onApply,
  className = '',
}: CodeArtifactProps) {
  const [highlightedCode, setHighlightedCode] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const language = normalizeLanguage(artifact.language);
  const displayName = LANGUAGE_NAMES[language] ?? artifact.language;

  // Initialize Shiki and highlight code
  useEffect(() => {
    let mounted = true;

    async function highlight() {
      try {
        setIsLoading(true);
        setError(null);

        // Dynamically import shiki
        const { createHighlighter } = await import('shiki');

        // Create or reuse highlighter
        if (!highlighter) {
          highlighter = await createHighlighter({
            themes: ['github-dark', 'github-light'],
            langs: [
              'typescript',
              'javascript',
              'python',
              'rust',
              'go',
              'java',
              'cpp',
              'c',
              'csharp',
              'html',
              'css',
              'json',
              'yaml',
              'markdown',
              'sql',
              'bash',
              'tsx',
              'jsx',
            ],
          });
        }

        if (!mounted) return;

        // Detect theme
        const isDark = document.documentElement.classList.contains('dark') ||
          window.matchMedia('(prefers-color-scheme: dark)').matches;

        // Highlight the code
        const html = (highlighter as {
          codeToHtml: (code: string, options: { lang: string; theme: string }) => string;
        }).codeToHtml(artifact.content, {
          lang: language,
          theme: isDark ? 'github-dark' : 'github-light',
        });

        if (mounted) {
          setHighlightedCode(html);
        }
      } catch (err) {
        console.error('[CodeArtifact] Highlighting failed:', err);
        if (mounted) {
          setError('Failed to highlight code');
          // Fallback to plain text
          setHighlightedCode(`<pre><code>${escapeHtml(artifact.content)}</code></pre>`);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    highlight();

    return () => {
      mounted = false;
    };
  }, [artifact.content, language]);

  // Copy to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('[CodeArtifact] Copy failed:', err);
    }
  }, [artifact.content]);

  // Download as file
  const handleDownload = useCallback(() => {
    const filename = artifact.filename ?? `code.${getExtension(language)}`;
    const blob = new Blob([artifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    URL.revokeObjectURL(url);
  }, [artifact.content, artifact.filename, language]);

  // Apply artifact (handled by parent)
  const handleApply = useCallback(() => {
    onApply?.(artifact);
  }, [artifact, onApply]);

  return (
    <div className={`rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {artifact.filename ?? displayName}
          </span>
          {artifact.filename && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ({displayName})
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          {/* Apply button (if handler provided) */}
          {onApply && (
            <button
              onClick={handleApply}
              className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
              title="Apply to workspace"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          
          {/* Download button */}
          <button
            onClick={handleDownload}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>
          
          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Code content */}
      <div className="relative">
        {isLoading ? (
          <div className="p-4 bg-gray-900 dark:bg-gray-950">
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-700 rounded w-3/4" />
              <div className="h-4 bg-gray-700 rounded w-1/2" />
              <div className="h-4 bg-gray-700 rounded w-5/6" />
            </div>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        ) : (
          <div
            className="overflow-x-auto text-sm [&_pre]:p-4 [&_pre]:m-0 [&_code]:font-mono"
            dangerouslySetInnerHTML={{ __html: highlightedCode }}
          />
        )}
      </div>

      {/* Line count footer */}
      <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {artifact.content.split('\n').length} lines
        </span>
      </div>
    </div>
  );
});

// ============================================================================
// Helpers
// ============================================================================

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function getExtension(language: string): string {
  const extensions: Record<string, string> = {
    typescript: 'ts',
    javascript: 'js',
    python: 'py',
    rust: 'rs',
    go: 'go',
    java: 'java',
    cpp: 'cpp',
    c: 'c',
    csharp: 'cs',
    html: 'html',
    css: 'css',
    json: 'json',
    yaml: 'yaml',
    markdown: 'md',
    sql: 'sql',
    bash: 'sh',
    tsx: 'tsx',
    jsx: 'jsx',
  };
  return extensions[language] ?? 'txt';
}

// ============================================================================
// Export types
// ============================================================================

export type { CodeArtifactProps };
