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
      box-shadow: 0px 8px 24px 0px rgba(0, 0, 0, 0.12);
      transition: all linear 0.2s;
      overflow: hidden;
      cursor: pointer;
    }
    /* Expanded state for streaming interface */
    #heygen-streaming-embed.expand {
      width: 640px;
      height: 600px;
      border-radius: 8px;
      border: none;
    }
    /* Hide the interface when collapsed */
    #streaming-interface {
      width: 100%;
      height: 100%;
      display: none;
      flex-direction: column;
      background-color: #fff;
      padding: 10px;
      box-sizing: border-box;
    }
    /* Show interface when expanded */
    #heygen-streaming-embed.expand #streaming-interface {
      display: flex;
    }
    /* Controls styling */
    #controls {
      margin-bottom: 10px;
    }
    #controls button, #talk-section button {
      padding: 5px 10px;
      margin-right: 5px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    #controls button {
      background-color: #28a745;
      color: #fff;
    }
    #controls button#closeBtn {
      background-color: #dc3545;
    }
    #talk-section {
      margin-bottom: 10px;
    }
    #talk-section input {
      padding: 5px;
      width: calc(100% - 110px);
      margin-right: 5px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    #talk-section button {
      background-color: #007bff;
      color: #fff;
    }
    #mediaElement {
      width: 100%;
      height: auto;
      background-color: #000;
      border-radius: 4px;
    }
    #status {
      margin-top: 5px;
      padding: 5px;
      background: #f8f9fa;
      border: 1px solid #ccc;
      border-radius: 4px;
      height: 60px;
      overflow-y: auto;
      font-family: monospace;
      font-size: 0.8rem;
    }
    /* Modal Styles */
    #session-close-modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width:100%;
      height:100%;
      background: rgba(0,0,0,0.5);
      align-items: center;
      justify-content: center;
      z-index: 10000;
    }
    #session-close-modal .modal-content {
      background: #fff;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
      max-width: 300px;
      margin: auto;
    }
    #session-close-modal .modal-content button {
      padding: 5px 10px;
      margin: 10px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    #session-close-modal .modal-content button#modalYesBtn {
      background-color: #dc3545;
      color: #fff;
    }
    #session-close-modal .modal-content button#modalNoBtn {
      background-color: #28a745;
      color: #fff;
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
      Welkom op onze website! Hier kun je kennismaken met onze interactieve avatar Imce. Imce staat voor je klaar om je te helpen, vragen te beantwoorden en je door de verschillende mogelijkheden van deze site te leiden. Voel je vrij om een gesprek aan te knopen en ontdek hoe Imce jouw ervaring persoonlijker en toegankelijker maakt. We hopen dat je een inspirerende en plezierige tijd hier zult hebben!
    </p>
  </main>

  <!-- Footer -->
  <footer>
    <p>&copy; 2025 MMG Waalre</p>
  </footer>

  <!-- Streaming Container (Avatar) -->
  <div id="heygen-streaming-embed">
    <div id="streaming-interface">
      <div id="controls">
        <!-- The Start button has been removed -->
        <!-- button id="closeBtn">Close</button -->
      </div>
      <div id="talk-section">
        <input id="taskInput" type="text" placeholder="Enter text for avatar to speak">
        <button id="talkBtn">Talk (LLM)</button>
      </div>
      <video id="mediaElement" autoplay playsinline></video>
      <div id="status"></div>
    </div>
  </div>

  <!-- Modal Popup for Session Close Confirmation -->
  <div id="session-close-modal">
    <div class="modal-content">
      <p>Do you want to close the session?</p>
      <button id="modalYesBtn">Yes</button>
      <button id="modalNoBtn">No</button>
    </div>
  </div>

  <!-- Streaming API Script -->
  <script>
    // Global variables for session and auto-close timer
    let sessionInfo = null;
    let room = null;
    let mediaStream = null;
    let webSocket = null;
    let sessionToken = null;
    let autoCloseTimer = null;
    let lastTextTimestamp = Date.now();

    // DOM Elements
    const streamingEmbed = document.getElementById('heygen-streaming-embed');
    const statusElement = document.getElementById("status");
    const mediaElement = document.getElementById("mediaElement");
    const taskInput = document.getElementById("taskInput");
    const modal = document.getElementById("session-close-modal");

    // Helper function to update status
    function updateStatus(message) {
      const timestamp = new Date().toLocaleTimeString();
      statusElement.innerHTML += `[${timestamp}] ${message}<br>`;
      statusElement.scrollTop = statusElement.scrollHeight;
    }

    // Get session token
    async function getSessionToken() {
      try {
        const response = await fetch(
          `${API_CONFIG.serverUrl}/v1/streaming.create_token`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Api-Key": API_CONFIG.apiKey,
            },
          }
        );
        const data = await response.json();
        sessionToken = data.data.token;
        updateStatus("Session token obtained");
      } catch (err) {
        updateStatus("Error obtaining session token");
        console.error(err);
      }
    }

    // Connect WebSocket
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
        updateStatus(eventData);
      });
      updateStatus(eventData);
    }

    // Create new session
    async function createNewSession() {
      if (!sessionToken) {
        await getSessionToken();
      }
      try {
        const response = await fetch(
          `${API_CONFIG.serverUrl}/v1/streaming.new`,
          {
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
          }
        );
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
        room.on(LivekitClient.RoomEvent.DataReceived, (message) => {
          const data = new TextDecoder().decode(message);
          console.log("Room message:", JSON.parse(data));
        });
        // Handle media streams
        mediaStream = new MediaStream();
        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === "video" || track.kind === "audio") {
            mediaStream.addTrack(track.mediaStreamTrack);
            if (
              mediaStream.getVideoTracks().length > 0 &&
              mediaStream.getAudioTracks().length > 0
            ) {
              mediaElement.srcObject = mediaStream;
              updateStatus("Media stream ready");
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
          updateStatus(`Room disconnected: ${reason}`);
        });
        await room.prepareConnection(sessionInfo.url, sessionInfo.access_token);
        updateStatus("Connection prepared");
        await connectWebSocket(sessionInfo.session_id);
        updateStatus("Session created successfully");
      } catch (err) {
        updateStatus("Error creating new session");
        console.error(err);
      }
    }

    // Start streaming session
    async function startStreamingSession() {
      try {
        await fetch(
          `${API_CONFIG.serverUrl}/v1/streaming.start`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${sessionToken}`,
            },
            body: JSON.stringify({
              session_id: sessionInfo.session_id,
            }),
          }
        );
        await room.connect(sessionInfo.url, sessionInfo.access_token);
        updateStatus("Connected to room");
        updateStatus("Streaming started successfully");
      } catch (err) {
        updateStatus("Error starting streaming session");
        console.error(err);
      }
    }

    // Send text to avatar (updates lastTextTimestamp and cancels auto-close timer)
    async function sendText(text, taskType = "talk") {
      if (!sessionInfo) {
        updateStatus("No active session");
        return;
      }
      try {
        lastTextTimestamp = Date.now();
        if (autoCloseTimer) {
          clearTimeout(autoCloseTimer);
          autoCloseTimer = null;
        }
        await fetch(
          `${API_CONFIG.serverUrl}/v1/streaming.task`,
          {
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
          }
        );
        updateStatus(`Sent text (${taskType}): ${text}`);
      } catch (err) {
        updateStatus("Error sending text");
        console.error(err);
      }
    }

    // Close session (only triggered via the modal Yes button or auto-close timer)
    async function closeSession() {
      if (!sessionInfo) {
        updateStatus("No active session");
        return;
      }
      try {
        await fetch(
          `${API_CONFIG.serverUrl}/v1/streaming.stop`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${sessionToken}`,
            },
            body: JSON.stringify({
              session_id: sessionInfo.session_id,
            }),
          }
        );
        if (webSocket) webSocket.close();
        if (room) room.disconnect();
        mediaElement.srcObject = null;
        sessionInfo = null;
        room = null;
        mediaStream = null;
        sessionToken = null;
        updateStatus("Session closed");
      } catch (err) {
        updateStatus("Error closing session");
        console.error(err);
      }
    }

    // Show the modal asking whether to close the session when container is minimized
    function showCloseSessionModal() {
      modal.style.display = "flex";
      document.getElementById("modalYesBtn").onclick = async function(e) {
        e.stopPropagation();
        modal.style.display = "none";
        if (autoCloseTimer) {
          clearTimeout(autoCloseTimer);
          autoCloseTimer = null;
        }
        await closeSession();
      };
      document.getElementById("modalNoBtn").onclick = function(e) {
        e.stopPropagation();
        modal.style.display = "none";
        // Start auto-close timer: if no new text is sent within 5 minutes, close the session.
        if (autoCloseTimer) {
          clearTimeout(autoCloseTimer);
        }
        autoCloseTimer = setTimeout(() => {
          closeSession();
        }, 300000); // 300000 ms = 5 minutes
      };
    }

    // Hardcoded values for Avatar ID and Voice ID
    const AVATAR_ID = "Santa_Fireplace_Front_public";
    const VOICE_ID = ""; // Set your desired Voice ID if needed

    // API Configuration
    const API_CONFIG = {
      apiKey: "MDIxZTk5N2RhOGQyNGZkOTlmM2JjOTg0MDA3Mjc0NjItMTc0MjM5NDc2NQ==",
      serverUrl: "https://api.heygen.com",
    };

    // Toggle expansion/collapse of the avatar container
    streamingEmbed.addEventListener('click', async function(e) {
      if (!e.target.closest('button') && !e.target.closest('input')) {
        const wasExpanded = streamingEmbed.classList.contains('expand');
        streamingEmbed.classList.toggle('expand');
        if (!wasExpanded && streamingEmbed.classList.contains('expand')) {
          // Expanding: if no session exists, create and start it.
          if (!sessionInfo) {
            await createNewSession();
            await startStreamingSession();
          }
          // Cancel any auto-close timer when expanded.
          if (autoCloseTimer) {
            clearTimeout(autoCloseTimer);
            autoCloseTimer = null;
          }
        } else if (wasExpanded && !streamingEmbed.classList.contains('expand')) {
          // Minimizing: show the modal popup.
          showCloseSessionModal();
        }
      }
    });

    // Event listener for the Talk button
    document.querySelector("#talkBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      const text = taskInput.value.trim();
      if (text) {
        sendText(text, "talk");
        taskInput.value = "";
      }
    });

    // Event listener for the Close button (if user clicks it while expanded)
    document.querySelector("#closeBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      closeSession();
    });
  </script>
</body>
</html>



"""
@app.route("/")
def index():
    return render_template_string(html_content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

