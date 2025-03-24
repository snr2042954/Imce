// ===================== GLOBAL VARIABLES =====================

// DOM elements used for displaying the UI and capturing user input
const streamingEmbed = document.getElementById('heygen-streaming-embed');
const mediaElement = document.getElementById("mediaElement");
const fallbackImage = document.getElementById("fallbackImage");
const startSessionBtn = document.getElementById("startSessionBtn");
const taskInput = document.getElementById("taskInput");
const chatHistory = document.getElementById("chatHistory");

// Runtime state variables used during an active session
let sessionInfo = null;
let room = null;
let mediaStream = null;
let webSocket = null;
let sessionToken = null;
let partialMessage = "";

// Configuration constants for the avatar and API
const AVATAR_ID = "Santa_Fireplace_Front_public";
const API_CONFIG = {
  serverUrl: "https://api.heygen.com",
};

// ===================== UI HELPERS =====================

/**
 * Appends a new message to the chat history UI with a timestamp.
 *
 * @param {string} message - The message string to display in the chat log.
 */
function updateChatHistory(message) {
  const timestamp = new Date().toLocaleTimeString();
  chatHistory.innerHTML += `[${timestamp}] ${message}<br>`;
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Shows or hides the fallback image and media element based on session state
function updateFallbackImage() {
  const isActive = Boolean(sessionInfo);
  fallbackImage.style.display = isActive ? 'none' : 'block';
  mediaElement.style.display = isActive ? 'block' : 'none';
}

// Displays the "Start" button only if the container is expanded and no session is active
function updateStartButton() {
  const shouldShow = streamingEmbed.classList.contains('expand') && !sessionInfo;
  startSessionBtn.style.display = shouldShow ? 'block' : 'none';
  startSessionBtn.disabled = !shouldShow;
  startSessionBtn.innerHTML = shouldShow ? 'Start' : '';
}

// ===================== INACTIVITY TIMER =====================

// Starts or resets a 10-second timer that will auto-close the session if no input is received
let inactivityTimer = null;
function resetInactivityTimer() {
  clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
    console.log("No new text prompts for 10 seconds. Stopping streaming session.");
    closeSession();
  }, 10000);
}

// ===================== TOKEN AND SESSION =====================

/**
 * Retrieves a session token from your backend.
 * This token is required for all authenticated Heygen API calls.
 */
async function getSessionToken() {
  try {
    const response = await fetch("/api/get-token", { method: "POST" });
    if (!response.ok) throw new Error("Token request failed");
    const data = await response.json();
    if (!data?.data?.token) throw new Error("No token returned from backend");
    sessionToken = data.data.token;
    console.log("Session token obtained");
  } catch (err) {
    console.error("Error obtaining session token", err);
  }
}

/**
 * Creates a new Heygen streaming session and prepares the LiveKit room.
 *
 * This sets up avatar streaming, media handling, WebSocket communication, and message events.
 */
async function createNewSession() {
  if (!sessionToken) await getSessionToken();

  try {
    const response = await fetch(`${API_CONFIG.serverUrl}/v1/streaming.new`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
      },
      body: JSON.stringify({
        quality: "high",
        avatar_id: AVATAR_ID,
        language: "nl",
        version: "v2",
        video_encoding: "H264",
      }),
    });

    if (!response.ok) throw new Error("Failed to create new session");
    const data = await response.json();
    if (!data?.data?.url || !data?.data?.access_token || !data?.data?.session_id) throw new Error("Session info missing");

    sessionInfo = data.data;

    room = new LivekitClient.Room({
      adaptiveStream: true,
      dynacast: true,
      videoCaptureDefaults: { resolution: LivekitClient.VideoPresets.h720.resolution },
    });

    // Handle incoming messages from the avatar
    room.on(LivekitClient.RoomEvent.DataReceived, (rawMessage) => {
      try {
        const textData = new TextDecoder().decode(rawMessage);
        const eventData = JSON.parse(textData);
        switch (eventData.type) {
          case "avatar_talking_message":
            partialMessage += (eventData.message || "");
            break;
          case "avatar_end_message":
            const finalText = partialMessage.trim();
            if (finalText) updateChatHistory(`Imce: ${finalText}`);
            partialMessage = "";
            break;
        }
      } catch (err) {
        console.error("Error parsing incoming data:", err);
      }
    });

    // Prepare an empty media stream and add tracks when available
    mediaStream = new MediaStream();

    room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
      if (track.kind === "video" || track.kind === "audio") {
        mediaStream.addTrack(track.mediaStreamTrack);
        if (mediaStream.getVideoTracks().length && mediaStream.getAudioTracks().length) {
          mediaElement.srcObject = mediaStream;
        }
      }
    });

    room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
      mediaStream.removeTrack(track.mediaStreamTrack);
    });

    room.on(LivekitClient.RoomEvent.Disconnected, (reason) => {
      console.log(`Room disconnected: ${reason}`);
    });

    await room.prepareConnection(sessionInfo.url, sessionInfo.access_token);
    await connectWebSocket(sessionInfo.session_id);
    console.log("Session created successfully");
  } catch (err) {
    console.error("Error creating new session", err);
  }
}

/**
 * Starts the streaming avatar session after the session has been created.
 * Notifies Heygen to start rendering the avatar and connects to the media room.
 */
async function startStreamingSession() {
  try {
    if (!sessionInfo?.session_id) throw new Error("No session ID available.");

    await fetch(`${API_CONFIG.serverUrl}/v1/streaming.start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
      },
      body: JSON.stringify({ session_id: sessionInfo.session_id }),
    });

    await room.connect(sessionInfo.url, sessionInfo.access_token);
    updateFallbackImage();
    console.log("Streaming started successfully");
  } catch (err) {
    console.error("Error starting streaming session", err);
  }
}

/**
 * Opens a WebSocket connection to Heygen for real-time chat interaction.
 *
 * @param {string} sessionId - The session ID to bind the WebSocket to.
 */
async function connectWebSocket(sessionId) {
  const params = new URLSearchParams({
    session_id: sessionId,
    session_token: sessionToken,
    silence_response: false,
    opening_text: "Hallo, waar kan ik je mee helpen?",
    stt_language: "nl",
  });

  const wsUrl = `wss://${new URL(API_CONFIG.serverUrl).hostname}/v1/ws/streaming.chat?${params.toString()}`;
  webSocket = new WebSocket(wsUrl);

  webSocket.addEventListener("message", (event) => {
    const eventData = JSON.parse(event.data);
    console.log("Raw WebSocket event:", eventData);
  });
}

// ===================== COMMUNICATION =====================

/**
 * Sends a user message to the Heygen API for processing.
 * Handles input validation, updates the UI, and sends the request payload.
 *
 * @param {string} text - The user's input message to send.
 * @param {string} taskType - The type of task (e.g., "talk", "command", etc.).
 */
async function sendText(text, taskType = "talk") {
  if (!sessionInfo) return console.error("No active session");

  const sanitized = text.replace(/[😀-🛿]/gu, '').substring(0, 200).trim();
  if (!sanitized) return console.warn("Attempted to send empty or invalid text. Ignoring.");

  const payload = {
    session_id: sessionInfo.session_id,
    text: sanitized,
    task_type: taskType,
  };

  updateChatHistory(`You: ${sanitized}`);

  try {
    const response = await fetch(`${API_CONFIG.serverUrl}/v1/streaming.task`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`Heygen API responded with status ${response.status}:`, errText);

      if (response.status === 500) {
        console.warn("Retrying once after 500 error...");
        await new Promise(res => setTimeout(res, 1000));
        return sendText(text, taskType);
      }
    }
  } catch (err) {
    console.error("Error sending text", err);
  }
}

// ===================== SESSION CLEANUP =====================

/**
 * Gracefully shuts down the session and resets app state
 */
async function closeSession() {
  if (!sessionInfo) return console.error("No active session");

  try {
    await fetch(`${API_CONFIG.serverUrl}/v1/streaming.stop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`,
      },
      body: JSON.stringify({ session_id: sessionInfo.session_id }),
    });

    if (webSocket) webSocket.close();
    if (room) room.disconnect();

    mediaElement.srcObject = null;
    sessionInfo = null;
    room = null;
    mediaStream = null;
    sessionToken = null;
    clearTimeout(inactivityTimer);

    updateFallbackImage();
    updateStartButton();
    console.log("Session closed");
  } catch (err) {
    console.error("Error closing session", err);
  }
}

// ===================== EVENT LISTENERS =====================

/**
 * Initializes all event listeners for user interaction with the UI and session handling.
 */
function initEventListeners() {
  // Handles clicks on the streaming container to expand/collapse and manage UI visibility
  streamingEmbed.addEventListener('click', (e) => {
    if (!e.target.closest('button') && !e.target.closest('input')) {
      streamingEmbed.classList.toggle('expand');
      streamingEmbed.classList.contains('expand') ? clearTimeout(inactivityTimer) : resetInactivityTimer();
      updateFallbackImage();
      updateStartButton();
    }
  });

  // Handles clicks on the start button to initiate a new streaming session
  startSessionBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    if (!sessionInfo) {
      startSessionBtn.disabled = true;
      startSessionBtn.innerHTML = 'Loading...';
      try {
        await createNewSession();
        await startStreamingSession();
      } catch (error) {
        console.error("Error starting session:", error);
      } finally {
        updateStartButton();
      }
    }
  });

  // Handles the talk button click: sends text and restarts inactivity timer
  document.querySelector("#talkBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    const text = taskInput.value.trim();
    if (text) {
      if (!streamingEmbed.classList.contains('expand')) resetInactivityTimer();
      sendText(text, "talk");
      taskInput.value = "";
    }
  });

  // Allows sending text by pressing Enter in the input field
  taskInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      document.querySelector("#talkBtn").click();
    }
  });

  // Toggles chat history visibility on button click
  document.querySelector("#toggleChatBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    chatHistory.style.display = (chatHistory.style.display === "none" || chatHistory.style.display === "") ? "block" : "none";
  });
}

// ===================== INITIALIZATION =====================

// Initialize UI state and bind event listeners on page load
updateFallbackImage();
updateStartButton();
initEventListeners();
