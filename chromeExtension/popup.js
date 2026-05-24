const summaryButton = document.getElementById("summarybutton");
const statusElement = document.getElementById("status");
const summaryElement = document.getElementById("summary");
const pageInfoElement = document.getElementById("pageInfo");

const backend_url = "http://127.0.0.1:5000";
const request_timeout_ms = 10 * 60 * 1000;

let currentTabId = null;
let currentTabUrl = "";

initializePopup();

async function initializePopup() {
  try {
    let queryOptions = {active: true, currentWindow: true}
    let [tab] = await chrome.tabs.query(queryOptions);

    if (!tab || typeof tab.id !== "number") { //second check incase id is undefined 
      setUnavailableState("No active tab found.");
      return;
    }

    currentTabId = tab.id;
    currentTabUrl = tab.url || "";

    if (!isYouTubeWatchPage(currentTabUrl)) {
      setUnavailableState("Open a YouTube watch page to summarize it.");
      return;
    }

    pageInfoElement.textContent = tab.title || "YouTube video detected.";
    statusElement.textContent = "Ready to summarize the current page.";
    summaryButton.disabled = false;
  } catch (error) {
    console.error(error);
    setUnavailableState("Could not read the current tab.");
  }
}

summaryButton.addEventListener("click", async () => {
  if (currentTabId === null) {
    setUnavailableState("No active YouTube tab is available.");
    return;
  }

  summaryButton.disabled = true; //to prevent the user from clicking on summarize video while it is summarizing the video
  statusElement.textContent = "Requesting summary from the server...";
  summaryElement.textContent = "Generating the summary...";

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), request_timeout_ms);
    const response = await fetch(
      `${backend_url}/api/summarize?youtube_url=${encodeURIComponent(currentTabUrl)}`,
      {
        headers: {
          Accept: "application/json"
        },
        signal: controller.signal
      }
    );
    clearTimeout(timeoutId);
    const payload = await parseResponse(response);

    if (!response.ok) {
      throw new Error(payload.error || "request to the backend failed.");
    }

    summaryElement.textContent = payload.summary || "No summary returned.";
    statusElement.textContent = "Summary generated.";
  } catch (error) {
    console.error(error);
    summaryElement.textContent = "No summary available.";
    statusElement.textContent = getRequestErrorMessage(error);
  } finally {
    summaryButton.disabled = false;
  }
});

function setUnavailableState(message) {
  pageInfoElement.textContent = "Open a YouTube video, then generate a quick summary.";
  statusElement.textContent = message;
  summaryElement.textContent = "No summary yet.";
  summaryButton.disabled = true;
}

function isYouTubeWatchPage(url) {
  try {
    const parsedUrl = new URL(url);
    return (
      parsedUrl.hostname.includes("youtube.com") &&
      parsedUrl.pathname === "/watch"
    );
  } catch {
    return false;
  }
}

function getRequestErrorMessage(error) {
  if (error.name === "AbortError") {
    return "The backend took way too long to respond.";
  }

  if (error instanceof TypeError) {
    return "Backend unreachable.";
  }

  return error.message || "Failed to summarize this page.";
}

async function parseResponse(response) {
  const rawText = await response.text();

  if (!rawText.trim()) {
    throw new Error(
      `The server returned an empty response. HTTP ${response.status || "unknown"} ${response.statusText || ""}`.trim()
    );
  }

  try {
    return JSON.parse(rawText);
  } catch {
    throw new Error(`Backend returned non-JSON output: ${rawText.slice(0, 160)}`); //slice incase error is very long
  }
}


