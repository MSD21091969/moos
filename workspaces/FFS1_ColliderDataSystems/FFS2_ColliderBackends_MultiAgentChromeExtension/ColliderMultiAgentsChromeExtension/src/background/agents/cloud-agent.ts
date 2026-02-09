import { GraphToolClient } from "~/background/external/graphtool";
import { searchTools } from "~/background/external/vectordb";
import type { ColliderResponse } from "~/types";

const workflowClient = new GraphToolClient("/ws/workflow");

export function initCloudAgent(): void {
  workflowClient.connect();

  workflowClient.on("workflow_result", (data) => {
    console.log("[CloudAgent] Workflow result:", data);
  });

  workflowClient.on("workflow_progress", (data) => {
    console.log("[CloudAgent] Workflow progress:", data);
  });
}

export async function executeWorkflow(
  workflowId: string,
  steps: string[]
): Promise<ColliderResponse> {
  try {
    workflowClient.send({
      type: "execute_workflow",
      workflow_id: workflowId,
      steps,
    });
    return { success: true, data: { workflowId, status: "submitted" } };
  } catch (error) {
    return {
      success: false,
      error: `Workflow execution failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function searchForTools(
  query: string
): Promise<ColliderResponse> {
  try {
    const results = await searchTools(query);
    return { success: true, data: results };
  } catch (error) {
    return {
      success: false,
      error: `Tool search failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export function disconnectCloudAgent(): void {
  workflowClient.disconnect();
}
