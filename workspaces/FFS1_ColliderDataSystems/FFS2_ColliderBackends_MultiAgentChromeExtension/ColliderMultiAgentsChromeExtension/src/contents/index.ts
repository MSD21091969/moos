import type { PlasmoCSConfig } from "plasmo";

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  run_at: "document_idle",
};

// Listen for messages from the background script / sidepanel
chrome.runtime.onMessage.addListener(
  (
    message: { type: string; selector?: string; value?: string; url?: string; source?: string },
    _sender: chrome.runtime.MessageSender,
    sendResponse: (response: unknown) => void
  ) => {
    if (message.type === "DOM_QUERY") {
      const selector = message.selector ?? "body";
      try {
        const elements = document.querySelectorAll(selector);
        const results = Array.from(elements).map((el) => ({
          tagName: el.tagName,
          id: el.id,
          className: el.className,
          textContent: el.textContent?.slice(0, 200),
          innerHTML: el.innerHTML?.slice(0, 500),
        }));
        sendResponse({ success: true, data: results });
      } catch (error) {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    if (message.type === "DOM_CAPTURE") {
      try {
        const snapshot = {
          url: window.location.href,
          title: document.title,
          bodyText: document.body.innerText.slice(0, 10000),
          links: Array.from(document.querySelectorAll("a")).map((a) => ({
            href: a.href,
            text: a.textContent?.trim().slice(0, 100),
          })),
        };
        sendResponse({ success: true, data: snapshot });
      } catch (error) {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    if (message.type === "DOM_CLICK") {
      const selector = message.selector ?? "";
      try {
        const el = document.querySelector(selector);
        if (!el) {
          sendResponse({ success: false, error: `No element matches: ${selector}` });
        } else {
          (el as HTMLElement).click();
          sendResponse({ success: true, data: { clicked: selector } });
        }
      } catch (error) {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    if (message.type === "DOM_FILL") {
      const selector = message.selector ?? "";
      const value = message.value ?? "";
      try {
        const el = document.querySelector(selector);
        if (!el) {
          sendResponse({ success: false, error: `No element matches: ${selector}` });
        } else if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
          el.value = value;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.dispatchEvent(new Event("change", { bubbles: true }));
          sendResponse({ success: true, data: { filled: selector, value } });
        } else {
          sendResponse({ success: false, error: "Element is not an input or textarea" });
        }
      } catch (error) {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    if (message.type === "PAGE_NAVIGATE") {
      const url = message.url ?? "";
      try {
        window.location.href = url;
        sendResponse({ success: true, data: { navigated: url } });
      } catch (error) {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    return true;
  }
);
