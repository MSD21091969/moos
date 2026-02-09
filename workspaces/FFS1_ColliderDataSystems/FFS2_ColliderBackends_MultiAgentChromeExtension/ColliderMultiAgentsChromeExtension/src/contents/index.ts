import type { PlasmoCSConfig } from "plasmo";

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  run_at: "document_idle",
};

// Listen for messages from the background script
chrome.runtime.onMessage.addListener(
  (
    message: { type: string; selector?: string },
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

    return true;
  }
);
