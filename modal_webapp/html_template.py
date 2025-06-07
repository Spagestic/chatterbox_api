
# Web interface HTML with WebSocket streaming support
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatterbox TTS - Real-time Streaming</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 800px;
            width: 100%;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            color: #666;
            font-size: 1.1em;
        }

        .form-group {
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }

        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
            transition: border-color 0.3s;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .char-counter {
            text-align: right;
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .generate-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }

        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .progress-container {
            margin: 20px 0;
            display: none;
        }

        .progress-bar {
            width: 100%;
            height: 10px;
            background-color: #e1e5e9;
            border-radius: 5px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s;
        }

        .status-text {
            margin-top: 10px;
            text-align: center;
            color: #666;
        }

        .audio-container {
            margin-top: 20px;
            display: none;
        }

        .audio-player {
            width: 100%;
            border-radius: 10px;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            color: white;
            font-weight: 600;
            z-index: 1000;
        }

        .connected {
            background-color: #28a745;
        }

        .disconnected {
            background-color: #dc3545;
        }

        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            display: none;
        }

        .accordion {
            margin: 20px 0;
        }

        .accordion-header {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .accordion-content {
            display: none;
            padding: 20px;
            border: 1px solid #e1e5e9;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }

        .file-input {
            width: 100%;
            padding: 10px;
            border: 2px solid #e1e5e9;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗣️ Chatterbox TTS</h1>
            <p>Real-time Text-to-Speech with Voice Cloning</p>
        </div>

        <div class="form-group">
            <label for="textInput">Text to synthesize:</label>
            <textarea id="textInput" placeholder="Enter the text you want to convert to speech (max 1000 characters)">Hello! This is a test of the Chatterbox TTS system with real-time streaming.</textarea>
            <div class="char-counter" id="charCounter">0/1000</div>
        </div>

        <div class="accordion">
            <div class="accordion-header" onclick="toggleAccordion()">
                🎤 Voice Cloning (Optional)
                <span id="accordionIcon">▼</span>
            </div>
            <div class="accordion-content" id="accordionContent">
                <input type="file" id="voiceFile" accept="audio/*" class="file-input">
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    Upload a clear audio sample (5-30 seconds) to clone a voice. Supported formats: WAV, MP3, MPEG.
                </div>
            </div>
        </div>

        <button class="generate-btn" id="generateBtn" onclick="generateSpeech()">
            🎵 Generate Speech
        </button>

        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="status-text" id="statusText">Initializing...</div>
        </div>

        <div class="error-message" id="errorMessage"></div>

        <div class="audio-container" id="audioContainer">
            <audio controls class="audio-player" id="audioPlayer"></audio>
        </div>
    </div>

    <div class="connection-status disconnected" id="connectionStatus">Disconnected</div>

    <script>
        let ws = null;
        let isConnected = false;

        // Initialize WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                isConnected = true;
                updateConnectionStatus(true);
                console.log('WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };
            
            ws.onclose = function() {
                isConnected = false;
                updateConnectionStatus(false);
                console.log('WebSocket disconnected');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                showError('WebSocket connection error');
            };
        }

        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connectionStatus');
            if (connected) {
                statusEl.textContent = 'Connected';
                statusEl.className = 'connection-status connected';
            } else {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'connection-status disconnected';
            }
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'progress') {
                updateProgress(data.progress, data.message);
            } else if (data.type === 'audio_complete') {
                handleAudioComplete(data.audio_data);
            } else if (data.type === 'error') {
                showError(data.message);
                hideProgress();
                resetButton();
            }
        }

        function handleAudioComplete(audioData) {
            hideProgress();
            
            const audioBytes = atob(audioData);
            const audioArray = new Uint8Array(audioBytes.length);
            for (let i = 0; i < audioBytes.length; i++) {
                audioArray[i] = audioBytes.charCodeAt(i);
            }
            
            const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.src = audioUrl;
            
            document.getElementById('audioContainer').style.display = 'block';
            resetButton();
        }

        function generateSpeech() {
            if (!isConnected) {
                generateSpeechHTTP();
                return;
            }

            const text = document.getElementById('textInput').value.trim();
            if (!text) {
                showError('Please enter some text to synthesize.');
                return;
            }

            if (text.length > 1000) {
                showError('Text is too long. Maximum 1000 characters allowed.');
                return;
            }

            const voiceFile = document.getElementById('voiceFile').files[0];
            
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = 'Generating...';
            document.getElementById('audioContainer').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'none';
            
            showProgress(0, 'Preparing request...');

            const message = {
                type: 'generate_tts',
                text: text
            };

            if (voiceFile) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    message.voice_prompt = e.target.result.split(',')[1];
                    ws.send(JSON.stringify(message));
                };
                reader.readAsDataURL(voiceFile);
            } else {
                ws.send(JSON.stringify(message));
            }
        }

        function generateSpeechHTTP() {
            const text = document.getElementById('textInput').value.trim();
            if (!text) {
                showError('Please enter some text to synthesize.');
                return;
            }

            if (text.length > 1000) {
                showError('Text is too long. Maximum 1000 characters allowed.');
                return;
            }

            const voiceFile = document.getElementById('voiceFile').files[0];
            
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = 'Generating...';
            document.getElementById('audioContainer').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'none';
            
            showProgress(0, 'Preparing request...');

            const formData = new FormData();
            formData.append('text', text);
            if (voiceFile) {
                formData.append('voice_prompt', voiceFile);
            }

            showProgress(30, 'Sending request...');

            fetch('/generate_streaming', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                showProgress(60, 'Receiving audio...');
                return response.blob();
            })
            .then(audioBlob => {
                showProgress(90, 'Processing audio...');
                const audioUrl = URL.createObjectURL(audioBlob);
                const audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.src = audioUrl;
                
                document.getElementById('audioContainer').style.display = 'block';
                hideProgress();
                resetButton();
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Failed to generate speech: ' + error.message);
                hideProgress();
                resetButton();
            });
        }

        function resetButton() {
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('generateBtn').textContent = '🎵 Generate Speech';
        }

        function showProgress(progress, message) {
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('statusText').textContent = message;
        }

        function updateProgress(progress, message) {
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('statusText').textContent = message;
        }

        function hideProgress() {
            document.getElementById('progressContainer').style.display = 'none';
        }

        function showError(message) {
            const errorEl = document.getElementById('errorMessage');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }

        function toggleAccordion() {
            const content = document.getElementById('accordionContent');
            const icon = document.getElementById('accordionIcon');
            
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                icon.textContent = '▲';
            } else {
                content.style.display = 'none';
                icon.textContent = '▼';
            }
        }

        // Character counter
        document.getElementById('textInput').addEventListener('input', function() {
            const text = this.value;
            const count = text.length;
            document.getElementById('charCounter').textContent = `${count}/1000`;
            
            if (count > 1000) {
                document.getElementById('charCounter').style.color = '#dc3545';
            } else {
                document.getElementById('charCounter').style.color = '#666';
            }
        });

        // Initialize character counter
        document.getElementById('textInput').dispatchEvent(new Event('input'));

        // Connect WebSocket when page loads
        connectWebSocket();
    </script>
</body>
</html>
"""

