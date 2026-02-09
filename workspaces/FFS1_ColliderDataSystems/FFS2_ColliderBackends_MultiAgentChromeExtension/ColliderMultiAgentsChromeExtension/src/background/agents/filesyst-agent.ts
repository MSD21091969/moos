import type { ColliderResponse } from "~/types";

const NATIVE_HOST_NAME = "com.collider.agent_host";

interface NativeMessage {
  action: string;
  path?: string;
  content?: string;
}

interface NativeResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}

export async function sendNativeMessage(
  message: NativeMessage
): Promise<ColliderResponse> {
  return new Promise((resolve) => {
    chrome.runtime.sendNativeMessage(
      NATIVE_HOST_NAME,
      message,
      (response: NativeResponse) => {
        if (chrome.runtime.lastError) {
          resolve({
            success: false,
            error: chrome.runtime.lastError.message ?? "Native messaging failed",
          });
          return;
        }
        resolve({
          success: response.success,
          data: response.data,
          error: response.error,
        });
      }
    );
  });
}

export async function readFile(path: string): Promise<ColliderResponse> {
  return sendNativeMessage({ action: "read_file", path });
}

export async function writeFile(
  path: string,
  content: string
): Promise<ColliderResponse> {
  return sendNativeMessage({ action: "write_file", path, content });
}

export async function listDir(path: string): Promise<ColliderResponse> {
  return sendNativeMessage({ action: "list_dir", path });
}

export async function readAgentContext(
  path: string
): Promise<ColliderResponse> {
  return sendNativeMessage({ action: "read_agent_context", path });
}
