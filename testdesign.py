from flask import Flask, render_template_string

app = Flask(__name__)


html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Imce Chat</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Overall Page Styles -->
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #74ABE2, #5563DE);
      color: #333;
    }
    header {
      background-color: #333;
      color: #fff;
      padding: 1rem 2rem;
    }
    nav ul {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
    }
    nav li {
      margin-right: 1rem;
    }
    nav a {
      color: #fff;
      text-decoration: none;
      font-weight: bold;
    }
    main {
      padding: 2rem;
      max-width: 1000px;
      margin: 2rem auto;
      background-color: #f5f5f5;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
      border-radius: 8px;
    }
    main h1 {
      margin-top: 0;
      text-align: center;
      font-size: 2.5rem;
      color: #333;
    }
    main p {
      font-size: 1.1rem;
      line-height: 1.6;
    }
    footer {
      text-align: center;
      padding: 1rem;
      background-color: #333;
      color: #fff;
    }
    /* Streaming Container (Avatar) Styles */
    #heygen-streaming-embed {
      z-index: 9999;
      position: fixed;
      right: 40px;
      bottom: 40px;
      width: 200px;
      height: 200px;
      background-color: #fff;
      border-radius: 50%;
      border: 2px solid #fff;
      box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.12);
      transition: all linear 0.2s;
      overflow: hidden;
      cursor: pointer;
    }
    /* Expanded state: container is larger and rectangular */
    #heygen-streaming-embed.expand {
      width: 480px;
      height: 300px;
      border-radius: 8px;
      border: none;
    }
    /* Hide overlay when not expanded */
    #heygen-streaming-embed:not(.expand) #overlay {
      display: none;
    }
    /* Video element fills the container */
    #mediaElement {
      width: 100%;
      height: 100%;
      object-fit: cover;
      position: absolute;
      top: 0;
      left: 0;
      display: block;
      z-index: 1;
    }
    /* Fallback image styling */
    #fallbackImage {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 2;
      /* Always visible when no session is active */
      display: block;
    }
    /* Start button (only in expanded mode when no session is active) */
    #startSessionBtn {
      display: none;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 4;
      padding: 10px 20px;
      font-size: 1rem;
      cursor: pointer;
    }
    /* Overlay for controls */
    #overlay {
      position: absolute;
      bottom: 0;
      width: 100%;
      background: rgba(0, 0, 0, 0.5);
      color: #fff;
      padding: 5px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      gap: 5px;
      z-index: 3;
    }
    /* Chat history styling (only shows chat messages) */
    #chatHistory {
      max-height: 80px;
      overflow-y: auto;
      font-size: 0.8rem;
      background: rgba(0, 0, 0, 0.7);
      padding: 5px;
      border-radius: 4px;
    }
    /* Talk section controls */
    #talk-section {
      display: flex;
      align-items: center;
    }
    #talk-section button, #talk-section input {
      padding: 5px;
      border: none;
      border-radius: 4px;
      margin-right: 5px;
      font-size: 0.9rem;
    }
    #talk-section input {
      flex-grow: 1;
      border: 1px solid #ccc;
      color: #000;
    }
    #talk-section button {
      background-color: #007bff;
      color: #fff;
      cursor: pointer;
    }
    /* Toggle chat history button style */
    #toggleChatBtn {
      background-color: #28a745;
      color: #fff;
      cursor: pointer;
    }
  </style>
  <!-- Include LiveKit Client Library -->
  <script src="https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js"></script>
</head>
<body>
  <!-- Header / Navigation -->
  <header>
    <nav>
      <ul>
        <li><a href="#">Home</a></li>
        <li><a href="#">Features</a></li>
        <li><a href="#">Contact</a></li>
      </ul>
    </nav>
  </header>

  <!-- Main Content -->
  <main>
    <h1>Voorbeeld pagina om te chatten met Imce</h1>
    <p>
      Welkom op onze website! Hier kun je kennismaken met onze interactieve avatar Imce. Imce staat voor je klaar om je te helpen en vragen te beantwoorden. Begin een gesprek en ontdek hoe Imce jouw ervaring persoonlijker maakt.
    </p>
  </main>

  <!-- Footer -->
  <footer>
    <p>&copy; 2025 MMG Waalre</p>
  </footer>

  <!-- Streaming Container (Avatar) -->
  <div id="heygen-streaming-embed">
    <!-- Fallback image is always shown when no session is active -->
    <img id="fallbackImage" src="{{ url_for('static', filename='imcepicture.jpg') }}" alt="Avatar fallback">
    <!-- The video element fills the container (hidden until session starts) -->
    <video id="mediaElement" autoplay playsinline style="display: none;"></video>
    <!-- Start button shown when expanded and no session is active -->
    <button id="startSessionBtn">Start</button>
    <!-- Overlay for chat and controls -->
    <div id="overlay">
      <!-- Chat History: shows only chat messages -->
      <div id="chatHistory" style="display:none;"></div>
      <!-- Talk Section with Toggle, Text Field, and Talk Button -->
      <div id="talk-section">
        <button id="toggleChatBtn">Toggle Chat History</button>
        <input id="taskInput" type="text" placeholder="Enter text for avatar to speak">
        <button id="talkBtn">Talk (LLM)</button>
      </div>
    </div>
  </div>

  <!-- Streaming API Script -->
  <script>
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

    // Hardcoded values for Avatar ID and Voice ID
    const AVATAR_ID = "Santa_Fireplace_Front_public";
    const VOICE_ID = ""; // Set your desired Voice ID if needed

    // Configuration
    const API_CONFIG = {
      apiKey: "MDIxZTk5N2RhOGQyNGZkOTlmM2JjOTg0MDA3Mjc0NjItMTc0MjM5NDc2NQ==",
      serverUrl: "https://api.heygen.com",
    };

    // 1. Get session token
    async function getSessionToken() {
      try {
        const response = await fetch(`${API_CONFIG.serverUrl}/v1/streaming.create_token`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Api-Key": API_CONFIG.apiKey,
          },
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
            voice: {
              voice_id: VOICE_ID,
              rate: 1.0,
            },
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
    async function sendText(text, taskType = "talk") {
      if (!sessionInfo) {
        console.error("No active session");
        return;
      }
      try {
        updateChatHistory(`You: ${text}`);
        await fetch(`${API_CONFIG.serverUrl}/v1/streaming.task`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionToken}`,
          },
          body: JSON.stringify({
            session_id: sessionInfo.session_id,
            text: text,
            task_type: taskType,
          }),
        });
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
  </script>
</body>
</html>

"""


@app.route("/")
def index():
    return render_template_string(html_content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

