function sendTabData(tab) {

    if (!tab.url) return;

    fetch("http://localhost:5000/tab", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: tab.url,
            title: tab.title,
            domain: new URL(tab.url).hostname,
            timestamp: Date.now()
        })
    }).catch(err => console.log("Server not running"));
}

chrome.tabs.onActivated.addListener(async (activeInfo) => {
    let tab = await chrome.tabs.get(activeInfo.tabId);
    sendTabData(tab);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete") {
        sendTabData(tab);
    }
});