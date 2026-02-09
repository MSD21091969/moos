import type { ColliderResponse } from "~/types";

export async function handleDomQuery(
  tabId: number,
  selector: string
): Promise<ColliderResponse> {
  try {
    const results = await chrome.tabs.sendMessage(tabId, {
      type: "DOM_QUERY",
      selector,
    });
    return { success: true, data: results };
  } catch (error) {
    return {
      success: false,
      error: `DOM query failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function handleDomCapture(
  tabId: number
): Promise<ColliderResponse> {
  try {
    const results = await chrome.tabs.sendMessage(tabId, {
      type: "DOM_CAPTURE",
    });
    return { success: true, data: results };
  } catch (error) {
    return {
      success: false,
      error: `DOM capture failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
