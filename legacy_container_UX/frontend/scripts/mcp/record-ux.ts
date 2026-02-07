/**
 * UX Recorder (Phase 1)
 *
 * A single, long-running recorder for fast-paced UX debugging.
 *
 * - Attaches to Edge via CDP (http://localhost:9222)
 * - Ensures the Vite tab exists (prefers localhost:5174, then 5173-5179)
 * - Injects an in-page observer (CLICK/NAV/STATE/ERROR/etc) if missing
 * - Records:
 *    - console messages (including structured args)
 *    - page errors + unhandled rejections
 *    - navigation events
 *    - optional network (default: off)
 *    - periodic minimal Zustand snapshots (throttled + change-detected)
 * - Writes JSONL + a short summary to frontend/test-results/mcp/
 *
 * Usage:
 *   npx tsx scripts/mcp/record-ux.ts
 *   npx tsx scripts/mcp/record-ux.ts --duration=10
 *   npx tsx scripts/mcp/record-ux.ts --network
 */

import { chromium, type Browser, type BrowserContext, type ConsoleMessage, type JSHandle, type Page, type Request, type Response } from 'playwright';
import { createWriteStream } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

type LogEvent = {
  ts: string;
  runId: string;
  seq: number;
  type:
    | 'meta'
    | 'console'
    | 'pageerror'
    | 'unhandledrejection'
    | 'navigation'
    | 'request'
    | 'response'
    | 'snapshot'
    | 'observer';
  level: LogLevel;
  page: {
    url: string;
    title?: string;
    contextIndex: number;
  };
  data: unknown;
};

type CliOptions = {
  cdpUrl: string;
  vitePorts: number[];
  enableNetwork: boolean;
  snapshotIntervalMs: number;
  durationMs?: number;
  noInject: boolean;
};

const DEFAULT_VITE_PORTS = [5174, 5173, 5175, 5176, 5177, 5178, 5179];

function tryUnrefTimer(timer: unknown) {
  if (typeof timer !== 'object' || timer === null) return;
  const maybe = timer as { unref?: () => void };
  if (typeof maybe.unref === 'function') maybe.unref();
}

const OBSERVER_SCRIPT = `
(function() {
  const VERSION = 'ux-recorder-2025-12-15';

  try {
    if (window.__MCP_OBSERVER__ && typeof window.__MCP_OBSERVER__.cleanup === 'function') {
      window.__MCP_OBSERVER__.cleanup();
    }
  } catch (e) {
    console.warn('[OBSERVER] Failed to cleanup prior observer:', e);
  }

  window.__MCP_OBSERVER_ACTIVE__ = true;
  window.__MCP_OBSERVER_VERSION__ = VERSION;

  console.log('[OBSERVER] ✅ MCP Observer injected', { version: VERSION });

  const state = {
    lastUrl: location.href,
    urlObserver: null,
    modalObserver: null,
    handlers: {},
  };

  window.__MCP_OBSERVER__ = {
    version: VERSION,
    cleanup: () => {
      try {
        const h = state.handlers;
        if (h.onClick) document.removeEventListener('click', h.onClick, true);
        if (h.onContextMenu) document.removeEventListener('contextmenu', h.onContextMenu, true);
        if (h.onDblClick) document.removeEventListener('dblclick', h.onDblClick, true);
        if (h.onKeyDown) document.removeEventListener('keydown', h.onKeyDown, true);
        if (h.onPopState) window.removeEventListener('popstate', h.onPopState, true);
        if (state.urlObserver) state.urlObserver.disconnect();
        if (state.modalObserver) state.modalObserver.disconnect();
        if (typeof window.__MCP_ZUSTAND_UNSUB__ === 'function') window.__MCP_ZUSTAND_UNSUB__();
      } catch (e) {
        console.warn('[OBSERVER] Cleanup error:', e);
      }
    }
  };

  state.handlers.onClick = (e) => {
    const target = e.target;
    const tag = target?.tagName?.toLowerCase?.() || 'unknown';
    const text = (target?.textContent || '').slice(0, 80).trim();
    const classList = Array.from(target?.classList || []).join('.');
    const id = target?.id ? '#' + target.id : '';
    const dataAction = target?.getAttribute?.('data-ai-action') || '';

    console.log('[CLICK]', {
      element: tag + id + (classList ? '.' + classList : ''),
      text: text || '(no text)',
      action: dataAction || '(none)',
      x: e.clientX,
      y: e.clientY
    });
  };
  document.addEventListener('click', state.handlers.onClick, true);

  state.handlers.onContextMenu = (e) => {
    const target = e.target;
    console.log('[CONTEXT]', {
      element: target?.tagName?.toLowerCase?.() || 'unknown',
      x: e.clientX,
      y: e.clientY
    });
  };
  document.addEventListener('contextmenu', state.handlers.onContextMenu, true);

  state.handlers.onDblClick = (e) => {
    const target = e.target;
    const text = (target?.textContent || '').slice(0, 80).trim();
    console.log('[DBLCLICK]', {
      element: target?.tagName?.toLowerCase?.() || 'unknown',
      text: text || '(no text)'
    });
  };
  document.addEventListener('dblclick', state.handlers.onDblClick, true);

  state.handlers.onKeyDown = (e) => {
    if (e.key === 'Escape' || e.key === 'Enter' || e.key === 'Delete' || e.ctrlKey || e.metaKey) {
      console.log('[KEY]', {
        key: e.key,
        ctrl: e.ctrlKey,
        meta: e.metaKey,
        shift: e.shiftKey
      });
    }
  };
  document.addEventListener('keydown', state.handlers.onKeyDown, true);

  state.urlObserver = new MutationObserver(() => {
    if (location.href !== state.lastUrl) {
      console.log('[NAV]', {
        from: state.lastUrl,
        to: location.href,
        path: location.pathname
      });
      state.lastUrl = location.href;
    }
  });
  state.urlObserver.observe(document.body, { childList: true, subtree: true });

  state.handlers.onPopState = () => {
    console.log('[NAV]', { type: 'popstate', path: location.pathname });
  };
  window.addEventListener('popstate', state.handlers.onPopState, true);

  const attachZustand = () => {
    const storeHook = window.__workspaceStore || window.__ZUSTAND_STORE__ || window.__workspace_store__;
    if (!storeHook?.subscribe || !storeHook?.getState) return false;

    try {
      if (typeof window.__MCP_ZUSTAND_UNSUB__ === 'function') window.__MCP_ZUSTAND_UNSUB__();
    } catch (_) {}

    window.__MCP_ZUSTAND_UNSUB__ = storeHook.subscribe((next, prev) => {
      const changes = {};
      const nextActive = next.activeContainerId ?? next.activeSessionId;
      const prevActive = prev?.activeContainerId ?? prev?.activeSessionId;
      if (nextActive !== prevActive) changes.activeContainerId = nextActive;
      if (next.activeContainerType !== prev?.activeContainerType) changes.activeContainerType = next.activeContainerType;

      const nextContainers = next.containers || next.sessions;
      const prevContainers = prev?.containers || prev?.sessions;
      if ((nextContainers?.length || 0) !== (prevContainers?.length || 0)) changes.containersCount = nextContainers?.length || 0;
      if ((next.nodes?.length || 0) !== (prev?.nodes?.length || 0)) changes.nodesCount = next.nodes?.length || 0;
      if ((next.selectedNodeIds?.length || 0) !== (prev?.selectedNodeIds?.length || 0)) changes.selectedCount = next.selectedNodeIds?.length || 0;

      if (Object.keys(changes).length > 0) console.log('[STATE]', changes);
    });

    console.log('[OBSERVER] Zustand subscription active');
    return true;
  };

  if (!attachZustand()) {
    console.warn('[OBSERVER] Zustand store not found - retrying in 1s');
    setTimeout(() => {
      if (!attachZustand()) console.warn('[OBSERVER] Zustand store still not found after retry');
      else console.log('[OBSERVER] Zustand subscription active (delayed)');
    }, 1000);
  }

  state.modalObserver = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node?.nodeType === 1) {
          const el = node;
          if (el.getAttribute?.('role') === 'dialog' || el.classList?.contains?.('modal') || el.querySelector?.('[role="dialog"]')) {
            console.log('[MODAL]', { action: 'open' });
          }
        }
      }
      for (const node of mutation.removedNodes) {
        if (node?.nodeType === 1) {
          const el = node;
          if (el.getAttribute?.('role') === 'dialog' || el.classList?.contains?.('modal')) {
            console.log('[MODAL]', { action: 'close' });
          }
        }
      }
    }
  });
  state.modalObserver.observe(document.body, { childList: true, subtree: true });

  const storeHook = window.__workspaceStore || window.__ZUSTAND_STORE__ || window.__workspace_store__;
  const s = storeHook?.getState?.();
  const containers = s?.containers || s?.sessions || [];
  console.log('[OBSERVER] Initial state', {
    url: location.pathname,
    activeContainer: s?.activeContainerId ?? s?.activeSessionId ?? null,
    nodes: s?.nodes?.length || 0,
    containers: containers?.length || 0
  });
})();
`;

function parseCli(argv: string[]): CliOptions {
  const options: CliOptions = {
    cdpUrl: 'http://localhost:9222',
    vitePorts: [...DEFAULT_VITE_PORTS],
    enableNetwork: false,
    snapshotIntervalMs: 1500,
    durationMs: undefined,
    noInject: false,
  };

  for (const raw of argv) {
    if (raw === '--network') options.enableNetwork = true;
    if (raw === '--no-inject') options.noInject = true;
    if (raw.startsWith('--snapshot=')) {
      const n = Number(raw.split('=')[1]);
      if (Number.isFinite(n) && n >= 200) options.snapshotIntervalMs = Math.floor(n);
    }
    if (raw.startsWith('--duration=')) {
      const n = Number(raw.split('=')[1]);
      if (Number.isFinite(n) && n > 0) options.durationMs = Math.floor(n * 1000);
    }
    if (raw.startsWith('--cdp=')) {
      options.cdpUrl = raw.split('=')[1] || options.cdpUrl;
    }
  }

  return options;
}

function nowIso() {
  return new Date().toISOString();
}

function timestampId(d = new Date()) {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function isViteUrl(url: string) {
  return /^(https?:\/\/)(localhost|127\.0\.0\.1):517\d\b/.test(url);
}

function redactSecrets(value: unknown, depth = 0): unknown {
  if (depth > 4) return '[Truncated]';

  if (typeof value === 'string') {
    // very basic token redaction
    const s = value;
    if (/\bBearer\s+\S+/i.test(s)) return s.replace(/\bBearer\s+\S+/gi, 'Bearer [REDACTED]');
    return s.length > 4000 ? `${s.slice(0, 4000)}…(truncated)` : s;
  }

  if (typeof value !== 'object' || value === null) return value;

  if (Array.isArray(value)) {
    const sliced = value.slice(0, 50);
    return sliced.map((v) => redactSecrets(v, depth + 1));
  }

  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    if (/token|authorization|cookie|set-cookie|password|secret/i.test(k)) {
      out[k] = '[REDACTED]';
    } else {
      out[k] = redactSecrets(v, depth + 1);
    }
  }
  return out;
}

async function serializeHandle(handle: JSHandle): Promise<{ kind: string; value?: unknown; preview?: string }> {
  try {
    const v = await handle.jsonValue();
    return { kind: 'json', value: redactSecrets(v) };
  } catch {
    // Fallback: keep a stable preview
    return { kind: 'handle', preview: handle.toString() };
  }
}

async function serializeConsoleMessage(msg: ConsoleMessage) {
  const args = await Promise.all(msg.args().map(serializeHandle));
  const location = msg.location();

  return {
    consoleType: msg.type(),
    text: msg.text(),
    location,
    args,
  };
}

async function ensureVitePage(context: BrowserContext, ports: number[]): Promise<Page> {
  const pages = context.pages();
  const vitePages = pages.filter((p) => isViteUrl(p.url())).sort((a, b) => a.url().length - b.url().length);
  if (vitePages.length > 0) return vitePages[0];

  const page = await context.newPage();
  for (const port of ports) {
    const url = `http://localhost:${port}/workspace`;
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 8000 });
      return page;
    } catch {
      // keep trying
    }
  }

  for (const port of ports) {
    const url = `http://localhost:${port}/`;
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 8000 });
      return page;
    } catch {
      // keep trying
    }
  }

  return page;
}

function classifyConsoleImportance(text: string, consoleType: string) {
  const importantPrefixes = ['[CLICK]', '[DBLCLICK]', '[CONTEXT]', '[KEY]', '[NAV]', '[STATE]', '[MODAL]', '[ERROR]', '[OBSERVER]'];
  if (consoleType === 'error' || consoleType === 'warning') return 'important';
  return importantPrefixes.some((p) => text.startsWith(p)) ? 'important' : 'misc';
}

async function getMinimalSnapshot(page: Page) {
  return await page.evaluate(() => {
    type AnyRecord = Record<string, unknown>;

    const w = globalThis as unknown as AnyRecord;
    const storeHook = (w['__workspaceStore'] ?? w['__ZUSTAND_STORE__'] ?? w['__workspace_store__']) as unknown;

    let s: AnyRecord | undefined;
    if ((typeof storeHook === 'object' || typeof storeHook === 'function') && storeHook !== null) {
      const rec = storeHook as AnyRecord;
      const getState = rec.getState;
      if (typeof getState === 'function') {
        s = (getState as () => unknown)() as AnyRecord;
      }
    }

    let breadcrumb: string[] | null = null;
    const nav = document.querySelector('nav[aria-label="breadcrumb"]');
    if (nav) {
      const links = nav.querySelectorAll('a, span');
      const parts: string[] = [];
      for (let i = 0; i < links.length; i++) {
        const t = links[i]?.textContent?.trim();
        if (t) parts.push(t);
      }
      breadcrumb = parts;
    }

    if (!s) {
      return {
        ok: false,
        url: location.href,
        path: location.pathname,
        title: document.title,
        breadcrumb,
      };
    }

    const containers = (s?.containers ?? s?.sessions) as unknown;
    const containersCount = Array.isArray(containers) ? containers.length : 0;

    const nodes = s?.nodes as unknown;
    const nodesCount = Array.isArray(nodes) ? nodes.length : 0;

    const selected = s?.selectedNodeIds as unknown;
    const selectedCount = Array.isArray(selected) ? selected.length : 0;

    const activeContainerId = (s?.activeContainerId ?? s?.activeSessionId ?? null) as string | null;

    const storeBreadcrumbs: string[] = [];
    const rawBreadcrumbs = s?.breadcrumbs as unknown;
    if (Array.isArray(rawBreadcrumbs)) {
      const list = rawBreadcrumbs.slice(0, 50);
      for (let i = 0; i < list.length; i++) {
        const b = list[i] as unknown;
        if (typeof b === 'object' && b !== null) {
          const br = b as AnyRecord;
          const title = br.title;
          const id = br.id;
          if (typeof title === 'string' && title.trim()) {
            storeBreadcrumbs.push(title);
            continue;
          }
          if (typeof id === 'string' && id.trim()) {
            storeBreadcrumbs.push(id);
            continue;
          }
        }
        storeBreadcrumbs.push(String(b));
      }
    }

    return {
      ok: true,
      url: location.href,
      path: location.pathname,
      title: document.title,
      breadcrumb,
      zustand: {
        activeContainerId,
        activeContainerType: (s?.activeContainerType ?? null) as string | null,
        userSessionId: (s?.userSessionId ?? null) as string | null,
        containersCount,
        nodesCount,
        selectedCount,
        breadcrumbs: storeBreadcrumbs,
      },
    };
  });
}

async function main() {
  const options = parseCli(process.argv.slice(2));
  const startedAt = Date.now();
  const runId = `ux-${timestampId()}`;
  const outDir = join(process.cwd(), 'test-results', 'mcp');
  const outJsonlPath = join(outDir, `${runId}.jsonl`);
  const outSummaryPath = join(outDir, `${runId}.summary.md`);

  await mkdir(outDir, { recursive: true });

  const stream = createWriteStream(outJsonlPath, { flags: 'a', encoding: 'utf8' });

  let seq = 0;
  const counts: Record<string, number> = {
    console: 0,
    pageerror: 0,
    unhandledrejection: 0,
    navigation: 0,
    request: 0,
    response: 0,
    snapshot: 0,
    observer: 0,
    droppedConsole: 0,
  };

  let browser: Browser | null = null;
  let stopped = false;
  let lastUrl = '';
  let lastSnapshotHash = '';
  let lastMiscConsoleAt = 0;

  const writeEvent = (
    event: Omit<LogEvent, 'ts' | 'runId' | 'seq' | 'page'>,
    pageUrl: string,
    pageTitle: string | undefined,
    contextIndex: number
  ) => {
    const row: LogEvent = {
      ts: nowIso(),
      runId,
      seq: ++seq,
      type: event.type,
      level: event.level,
      page: { url: pageUrl, title: pageTitle, contextIndex },
      data: redactSecrets(event.data),
    };

    stream.write(`${JSON.stringify(row)}\n`);
    counts[event.type] = (counts[event.type] || 0) + 1;
  };

  const stop = async (reason: string) => {
    if (stopped) return;
    stopped = true;

    const endedAt = Date.now();
    const durationMs = endedAt - startedAt;

    const summary = [
      `# UX Recorder Summary`,
      ``,
      `- Run ID: \`${runId}\``,
      `- Reason: ${reason}`,
      `- Started: ${new Date(startedAt).toISOString()}`,
      `- Ended: ${new Date(endedAt).toISOString()}`,
      `- Duration: ${(durationMs / 1000).toFixed(1)}s`,
      `- Output (JSONL): \`${outJsonlPath}\``,
      `- Output (Summary): \`${outSummaryPath}\``,
      `- Last URL: ${lastUrl || '(unknown)'}`,
      ``,
      `## Counts`,
      ``,
      ...Object.entries(counts).map(([k, v]) => `- ${k}: ${v}`),
      ``,
      `## Tips`,
      `- Search the JSONL for: "[CLICK]", "[NAV]", "[STATE]", "pageerror", "unhandledrejection".`,
    ].join('\n');

    try {
      await mkdir(dirname(outSummaryPath), { recursive: true });
      await writeFile(outSummaryPath, summary, 'utf8');
    } catch {
      // ignore
    }

    try {
      stream.end();
    } catch {
      // ignore
    }

    try {
      await browser?.close();
    } catch {
      // ignore
    }

    // Always print paths as the final line for easy copying.
    console.warn(`\n✅ UX Recorder finished.`);
    console.warn(`📝 JSONL: ${outJsonlPath}`);
    console.warn(`🧾 Summary: ${outSummaryPath}`);
  };

  process.on('SIGINT', () => {
    void stop('SIGINT');
  });
  process.on('SIGTERM', () => {
    void stop('SIGTERM');
  });

  const durationMs = options.durationMs;
  if (typeof durationMs === 'number') {
    const t = setTimeout(() => {
      void stop(`--duration=${Math.round(durationMs / 1000)}s`);
    }, durationMs);
    tryUnrefTimer(t);
  }

  console.warn(`🎥 UX Recorder starting…`);
  console.warn(`   CDP: ${options.cdpUrl}`);
  console.warn(`   Ports: ${options.vitePorts.join(', ')}`);
  console.warn(`   Snapshot: ${options.snapshotIntervalMs}ms`);
  console.warn(`   Network: ${options.enableNetwork ? 'ON' : 'OFF'}`);
  console.warn(`   Output: ${outJsonlPath}`);

  browser = await chromium.connectOverCDP(options.cdpUrl);
  const contexts = browser.contexts();
  if (contexts.length === 0) {
    console.error('❌ No browser contexts found. Is Edge running with --remote-debugging-port=9222?');
    await stop('no-contexts');
    return;
  }

  const contextIndex = 0;
  const context = contexts[contextIndex];
  const page = await ensureVitePage(context, options.vitePorts);

  const pageTitle = await page.title().catch(() => undefined);
  lastUrl = page.url();
  console.warn(`✅ Attached to: ${lastUrl}${pageTitle ? ` — ${pageTitle}` : ''}`);

  // Meta event
  writeEvent(
    {
      type: 'meta',
      level: 'info',
      data: {
        message: 'ux-recorder-attached',
        options,
        tabs: await Promise.all(
          context.pages().slice(0, 10).map(async (p, i) => ({
            i,
            url: p.url(),
            title: await p.title().catch(() => ''),
          }))
        ),
      },
    },
    lastUrl,
    pageTitle,
    contextIndex
  );

  // Inject observer (optional)
  if (!options.noInject) {
    try {
      const isInjected = await page.evaluate(() => {
        const w = globalThis as unknown as Record<string, unknown>;
        return Boolean(w['__MCP_OBSERVER_ACTIVE__']);
      });
      if (!isInjected) {
        await page.evaluate(OBSERVER_SCRIPT);
        writeEvent(
          { type: 'observer', level: 'info', data: { action: 'inject', ok: true } },
          page.url(),
          pageTitle,
          contextIndex
        );
      } else {
        writeEvent(
          { type: 'observer', level: 'debug', data: { action: 'inject', ok: true, alreadyActive: true } },
          page.url(),
          pageTitle,
          contextIndex
        );
      }
    } catch (e) {
      writeEvent(
        { type: 'observer', level: 'warn', data: { action: 'inject', ok: false, error: e instanceof Error ? e.message : String(e) } },
        page.url(),
        pageTitle,
        contextIndex
      );
    }
  }

  // Console
  page.on('console', async (msg) => {
    if (stopped) return;

    const importance = classifyConsoleImportance(msg.text(), msg.type());
    const now = Date.now();

    if (importance === 'misc') {
      // Rate-limit misc console spam to reduce overhead.
      if (now - lastMiscConsoleAt < 200) {
        counts.droppedConsole += 1;
        return;
      }
      lastMiscConsoleAt = now;
    }

    const payload = await serializeConsoleMessage(msg);
    const url = page.url();
    lastUrl = url;
    const title = await page.title().catch(() => undefined);

    writeEvent(
      {
        type: 'console',
        level: msg.type() === 'error' ? 'error' : msg.type() === 'warning' ? 'warn' : 'info',
        data: payload,
      },
      url,
      title,
      contextIndex
    );

    // Optional: lightweight live feedback for high-signal observer events.
    if (payload.text?.startsWith('[ERROR]') || payload.consoleType === 'error') {
      console.warn(`🧨 console:error ${payload.text}`);
    }
  });

  // Errors
  page.on('pageerror', (err) => {
    if (stopped) return;
    lastUrl = page.url();
    writeEvent(
      { type: 'pageerror', level: 'error', data: { message: err?.message, stack: err?.stack } },
      lastUrl,
      undefined,
      contextIndex
    );
    console.error(`🧨 pageerror: ${err?.message}`);
  });

  page.on('crash', () => {
    void stop('page-crash');
  });

  // Navigation
  let lastNavUrl = page.url();
  page.on('framenavigated', (frame) => {
    if (stopped) return;
    if (frame !== page.mainFrame()) return;

    const to = frame.url();
    const from = lastNavUrl;
    lastNavUrl = to;
    lastUrl = to;

    writeEvent(
      { type: 'navigation', level: 'info', data: { from, to } },
      to,
      undefined,
      contextIndex
    );
  });

  // Optional network
  if (options.enableNetwork) {
    const shouldTrack = (url: string) => url.includes('localhost') || url.includes('127.0.0.1');

    page.on('request', (req: Request) => {
      if (stopped) return;
      const url = req.url();
      if (!shouldTrack(url)) return;
      writeEvent(
        {
          type: 'request',
          level: 'debug',
          data: {
            method: req.method(),
            url,
            resourceType: req.resourceType(),
          },
        },
        page.url(),
        undefined,
        contextIndex
      );
    });

    page.on('response', async (res: Response) => {
      if (stopped) return;
      const url = res.url();
      if (!shouldTrack(url)) return;

      const status = res.status();
      // Only keep non-2xx/3xx for speed
      if (status < 400) return;

      writeEvent(
        {
          type: 'response',
          level: 'warn',
          data: {
            url,
            status,
            ok: res.ok(),
            request: {
              method: res.request().method(),
              resourceType: res.request().resourceType(),
            },
          },
        },
        page.url(),
        undefined,
        contextIndex
      );
    });
  }

  // Periodic snapshots
  const snapshotTimer = setInterval(async () => {
    if (stopped) return;
    try {
      const snap = await getMinimalSnapshot(page);
      const hash = JSON.stringify(snap);
      if (hash === lastSnapshotHash) return;
      lastSnapshotHash = hash;
      lastUrl = page.url();

      writeEvent(
        { type: 'snapshot', level: 'info', data: snap },
        lastUrl,
        undefined,
        contextIndex
      );
    } catch (e) {
      writeEvent(
        { type: 'snapshot', level: 'warn', data: { ok: false, error: e instanceof Error ? e.message : String(e) } },
        page.url(),
        undefined,
        contextIndex
      );
    }
  }, options.snapshotIntervalMs);
  tryUnrefTimer(snapshotTimer);

  // Keep process alive.
  await new Promise<void>((resolve) => {
    const check = setInterval(() => {
      if (stopped) {
        clearInterval(check);
        resolve();
      }
    }, 250);
    tryUnrefTimer(check);
  });
}

main().catch(async (e) => {
  const msg = e instanceof Error ? e.stack || e.message : String(e);
  console.error('❌ UX Recorder failed:', msg);
  // Best-effort: write a crash marker
  try {
    const outDir = join(process.cwd(), 'test-results', 'mcp');
    await mkdir(outDir, { recursive: true });
    await writeFile(join(outDir, `ux-recorder-crash-${timestampId()}.txt`), msg, 'utf8');
  } catch {
    // ignore
  }
  process.exitCode = 1;
});
