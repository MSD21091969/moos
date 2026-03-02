import {
    HttpExecutionFunctor,
    McpJsonRpcExecutionFunctor,
    ToolFirstProviderFunctor,
} from '@moos/functors';
import { fetchBootstrapContext } from './context/bootstrap-client.js';
import { runSingleTurn } from './loop/agent-loop.js';
import { SessionManager } from './session/manager.js';

const bootstrap = async (): Promise<void> => {
    const dataServerUrl = process.env.DATA_SERVER_URL ?? 'http://127.0.0.1:8000';
    const toolServerUrl = process.env.TOOL_SERVER_URL ?? 'http://127.0.0.1:8001';

    const provider = new ToolFirstProviderFunctor();
    const fallbackExecutor = new HttpExecutionFunctor(toolServerUrl);
    const executor = new McpJsonRpcExecutionFunctor(toolServerUrl, fallbackExecutor);
    const sessions = new SessionManager();

    const session = sessions.create('bootstrap-session');
    const context = await fetchBootstrapContext(dataServerUrl, ['bootstrap.morphism']);

    sessions.append(session.sessionId, 'bootstrap-started');

    const result = await runSingleTurn(provider, executor, {
        system: context.system,
        messages: [...context.messages, 'hello moos'],
        tools: [{ name: 'echo_tool', description: 'echo contract tool' }],
    });

    sessions.append(session.sessionId, result.text);

    console.log('[moos-engine] turn result:', result.text);
    console.log('[moos-engine] tools executed:', result.executedTools.length);
};

void bootstrap();
