// Inactivity timer variable
 let inactivityTimer = null;
 function startInactivityTimer() {
 clearInactivityTimer();
    inactivityTimer = setTimeout(() => {
      console.log("No new text prompts for 10 seconds. Stopping streaming session.");
      closeSession();
    }, 10000); // 10 seconds
  }
  function clearInactivityTimer() {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
  }

  // Global variables
  const streamingEmbed = document.getElementById('heygen-streaming-embed');
  const mediaElement = document.getElementById("mediaElement");
  const fallbackImage = document.getElementById("fallbackImage");
  const startSessionBtn = document.getElementById("startSessionBtn");
  const taskInput = document.getElementById("taskInput");
  const chatHistory = document.getElementById("chatHistory");

  let sessionInfo = null;
  let room = null;
  let mediaStream = null;
  let webSocket = null;
  let sessionToken = null;

  // Accumulate partial words from avatar
  let partialMessage = "";

  // Append chat messages to the chat history element
  function updateChatHistory(message) {
    const timestamp = new Date().toLocaleTimeString();
    chatHistory.innerHTML += `[${timestamp}] ${message}<br>`;
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // Remove emoji and trim length to 200 chars
  function sanitizeText(text) {
    return text.replace(/[\p{Emoji_Presentation}|\p{Extended_Pictographic}]/gu, '').substring(0, 200);
  }

  // Update display: if no session, always show fallback image; if session active, show video.
  function updateFallbackImage() {
    if (!sessionInfo) {
      fallbackImage.style.display = 'block';
      mediaElement.style.display = 'none';
    } else {
      fallbackImage.style.display = 'none';
      mediaElement.style.display = 'block';
    }
  }

  // Update the Start button visibility:
  // Show the button if container is expanded and no session exists.
  function updateStartButton() {
    if (streamingEmbed.classList.contains('expand') && !sessionInfo) {
      startSessionBtn.style.display = 'block';
      startSessionBtn.disabled = false;
      startSessionBtn.innerHTML = 'Start';
    } else {
      startSessionBtn.style.display = 'none';
    }
  }

  // Toggle expansion/collapse when clicking on the container (unless a control is clicked)
  streamingEmbed.addEventListener('click', function(e) {
    if (!e.target.closest('button') && !e.target.closest('input')) {
      streamingEmbed.classList.toggle('expand');
      if (streamingEmbed.classList.contains('expand')) {
        // Clear inactivity timer when expanded.
        clearInactivityTimer();
      } else {
        startInactivityTimer();
      }
      updateFallbackImage();
      updateStartButton();
    }
  });

  // Start button event: create and start session when clicked, show loading animation meanwhile.
  startSessionBtn.addEventListener('click', async function(e) {
    e.stopPropagation();
    if (!sessionInfo) {
      // Show loading state on the start button.
      startSessionBtn.disabled = true;
      startSessionBtn.innerHTML = 'Loading...';
      try {
        await createNewSession();
        await startStreamingSession();
      } catch (error) {
        console.error("Error starting session:", error);
      } finally {
        updateStartButton(); // Hide the start button if session is active.
      }
    }
  });

  // Hardcoded values for Avatar ID
  const AVATAR_ID = "Santa_Fireplace_Front_public";

  // Configuration
  const API_CONFIG = {
    serverUrl: "https://api.heygen.com",
  };



  // 1. Get session token
  async function getSessionToken() {
  try {
    const response = await fetch("/api/get-token", {
      method: "POST",
    });
    const data = await response.json();
    sessionToken = data.data.token;
    console.log("Session token obtained");
  } catch (err) {
    console.error("Error obtaining session token", err);
  }
}


  // 2. Connect WebSocket and process messages from the avatar
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

  // 3. Create a new streaming session
  async function createNewSession() {
    if (!sessionToken) {
      await getSessionToken();
    }
    try {
      const response = await fetch(`${API_CONFIG.serverUrl}/v1/streaming.new`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({
          quality: "high",
          avatar_name: AVATAR_ID,
          language: "nl",
          version: "v2",
          video_encoding: "H264",
        }),
      });
      const data = await response.json();
      sessionInfo = data.data;

      // Create LiveKit Room
      room = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
          resolution: LivekitClient.VideoPresets.h720.resolution,
        },
      });
      // Listen for data from the LiveKit room
      room.on(LivekitClient.RoomEvent.DataReceived, (rawMessage) => {
        try {
          const textData = new TextDecoder().decode(rawMessage);
          const eventData = JSON.parse(textData);
          console.log("Room message:", eventData);

          switch (eventData.type) {
            case "avatar_talking_message":
              partialMessage += (eventData.message || "");
              break;
            case "avatar_end_message":
              const finalText = partialMessage.trim();
              if (finalText) {
                console.log("Final avatar message:", finalText);
                updateChatHistory(`Imce: ${finalText}`);
              }
              partialMessage = "";
              break;
            default:
              console.log("Unhandled event type:", eventData.type);
              break;
          }
        } catch (err) {
          console.error("Error parsing incoming data:", err);
        }
      });

      // Handle media streams
      mediaStream = new MediaStream();
      room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === "video" || track.kind === "audio") {
          mediaStream.addTrack(track.mediaStreamTrack);
          if (mediaStream.getVideoTracks().length > 0 && mediaStream.getAudioTracks().length > 0) {
            mediaElement.srcObject = mediaStream;
            console.log("Media stream ready");
          }
        }
      });
      room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
        const mediaTrack = track.mediaStreamTrack;
        if (mediaTrack) {
          mediaStream.removeTrack(mediaTrack);
        }
      });
      room.on(LivekitClient.RoomEvent.Disconnected, (reason) => {
        console.log(`Room disconnected: ${reason}`);
      });

      await room.prepareConnection(sessionInfo.url, sessionInfo.access_token);
      console.log("Connection prepared");
      await connectWebSocket(sessionInfo.session_id);
      console.log("Session created successfully");
    } catch (err) {
      console.error("Error creating new session", err);
    }
  }

  // 4. Start streaming session
  async function startStreamingSession() {
    try {
      await fetch(`${API_CONFIG.serverUrl}/v1/streaming.start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({
          session_id: sessionInfo.session_id,
        }),
      });
      await room.connect(sessionInfo.url, sessionInfo.access_token);
      console.log("Connected to room");
      console.log("Streaming started successfully");
      updateFallbackImage(); // Hide fallback image when streaming starts.
    } catch (err) {
      console.error("Error starting streaming session", err);
    }
  }

  // 5. Send text to avatar and update chat history with user message
  // 5. Send text to avatar and update chat history with user message
  async function sendText(text, taskType = "talk") {
    if (!sessionInfo) {
      console.error("No active session");
      return;
    }

    const sanitized = sanitizeText(text);

    if (!sanitized || sanitized.trim().length === 0) {
      console.warn("Attempted to send empty or invalid text. Ignoring.");
      return;
    }

    const payload = {
      session_id: sessionInfo.session_id,
      text: sanitized,
      task_type: taskType,
    };

    console.log("Sending sanitized task payload to Heygen:", payload);

    try {
      updateChatHistory(`You: ${sanitized}`);
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
      }
    } catch (err) {
      console.error("Error sending text", err);
    }
  }


  // 6. Close session (triggered by inactivity or other conditions)
  async function closeSession() {
    if (!sessionInfo) {
      console.error("No active session");
      return;
    }
    try {
      await fetch(`${API_CONFIG.serverUrl}/v1/streaming.stop`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({
          session_id: sessionInfo.session_id,
        }),
      });
      if (webSocket) webSocket.close();
      if (room) room.disconnect();
      mediaElement.srcObject = null;
      sessionInfo = null;
      room = null;
      mediaStream = null;
      sessionToken = null;
      clearInactivityTimer();
      console.log("Session closed");
    } catch (err) {
      console.error("Error closing session", err);
    }
    updateFallbackImage();
    updateStartButton(); // Show the Start button again if expanded.
  }

  // Event listener for the Talk button
  document.querySelector("#talkBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    const text = taskInput.value.trim();
    if (text) {
      if (!streamingEmbed.classList.contains('expand')) {
        startInactivityTimer();
      }
      sendText(text, "talk");
      taskInput.value = "";
    }
  });

  // Send text when hitting Enter in the text field
  taskInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      document.querySelector("#talkBtn").click();
    }
  });

  // Toggle chat history display
  document.querySelector("#toggleChatBtn").addEventListener("click", (e) => {
    e.stopPropagation();
    chatHistory.style.display = (
      chatHistory.style.display === "none" || chatHistory.style.display === ""
    ) ? "block" : "none";
  });

  // Initial calls on page load
  updateFallbackImage();
  updateStartButton();