from flask import Flask, render_template
from waitress import serve
from flask import Flask, render_template
import requests
import uuid

app = Flask(__name__)

def get_realtime_endpoint():
    """
    Call the Heygen /v1/streaming.new API to obtain the realtime_endpoint.
    Replace 'YOUR_API_KEY' with your actual API key.
    """
    url = "https://api.heygen.com/v1/streaming.new"  # Adjust endpoint if needed.
    headers = {
        "Authorization": "OWUxODE2ZTUxZGIxNDZjMWFkYjY3ODY4ZDViZDAzNjctMTc0MTY5OTMwOA==",  # Replace with your API key.
        "Content-Type": "application/json"
    }
    payload = {
        # Include any required parameters by the Heygen API.
        "avatar": "2fe7e0bc976c4ea1adaff91afb0c68ec",
        "scene": "default"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("realtime_endpoint", "")
    except requests.exceptions.RequestException as e:
        print("API call failed:", e)
        return ""

@app.route('/')
def index():
    realtime_endpoint = get_realtime_endpoint()
    # Fallback: simulate a session if API call fails.
    if not realtime_endpoint:
        session_id = str(uuid.uuid4())
        realtime_endpoint = f"wss://webrtc-signaling.heygen.io/v2-alpha/interactive-avatar/session/{session_id}"
    return render_template('index.html', realtime_endpoint=realtime_endpoint)

if __name__ == '__main__':
    # Serve the app on http://127.0.0.1:8000
    serve(app, host="0.0.0.0", port=8000)
