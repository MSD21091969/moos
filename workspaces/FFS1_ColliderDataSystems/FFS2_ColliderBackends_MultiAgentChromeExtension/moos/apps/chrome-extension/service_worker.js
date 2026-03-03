chrome.runtime.onInstalled.addListener(() => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => { });
});

chrome.runtime.onStartup.addListener(() => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => { });
});

chrome.tabs.onUpdated.addListener((tabId, info, tab) => {
    if (info.status !== 'complete' || !tab.url) {
        return;
    }

    chrome.sidePanel
        .setOptions({
            tabId,
            path: 'sidepanel.html',
            enabled: true,
        })
        .catch(() => { });
});
