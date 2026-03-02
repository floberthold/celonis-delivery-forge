chrome.runtime.onInstalled.addListener(() => {
  console.log("Foundry companion extension installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "foundry.ping") {
    return;
  }
  sendResponse({ ok: true, source: "background", tabId: sender.tab?.id ?? null });
});
