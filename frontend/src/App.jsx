// frontend/src/App.jsx
import { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Connecting...');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const websocketRef = useRef(null);
  const audioRef = useRef(null);

  // Function to play audio from base64 data
  const playAudio = (base64Audio) => {
    try {
      // Convert base64 to audio blob
      const byteCharacters = atob(base64Audio);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const audioBlob = new Blob([byteArray], { type: 'audio/wav' });
      
      // Create audio URL and play
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Clear any previous audio
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
      
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      // Update status when audio starts playing
      audio.onplay = () => {
        setStatus('AI is speaking...');
        setIsProcessing(true);
      };
      
      audio.play();
      
      // Clean up after playback and reset status
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setStatus('Ready to listen');
        setIsProcessing(false); // This is the critical fix
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setStatus('Audio playback failed');
        setIsProcessing(false); // Reset on error too
      };
      
    } catch (error) {
      console.error('Error playing audio:', error);
      setStatus('Error playing audio response');
      setIsProcessing(false); // Reset on error
    }
  };

  // Add useEffect to handle WebSocket connection
  useEffect(() => {
    // Function to connect to the WebSocket
    const connectWebSocket = () => {
      try {
        // Connect to the correct WebSocket endpoint
        const socket = new WebSocket('ws://localhost:8000/ws');
        websocketRef.current = socket;

        socket.onopen = () => {
          console.log('WebSocket connection established');
          setStatus('Ready to listen');
        };

        socket.onmessage = async (event) => {
          console.log('Received from server:', event.data);
          
          try {
            // Try to parse as JSON (which contains audio)
            const data = JSON.parse(event.data);
            if (data.text && data.audio) {
              setStatus(`AI: ${data.text}`);
              // Play the audio
              playAudio(data.audio);
            }
          } catch {
            // Fallback to text-only handling
            if (event.data.startsWith('AI_RESPONSE:')) {
              const responseText = event.data.replace('AI_RESPONSE:', '');
              setStatus(`AI: ${responseText}`);
              setIsProcessing(false); // Reset processing state
            } else if (event.data.startsWith('CRISIS_RESPONSE:')) {
              setStatus(`CRISIS: ${event.data.replace('CRISIS_RESPONSE:', '')}`);
              setIsProcessing(false); // Reset processing state
            } else if (event.data.startsWith('ERROR:')) {
              setStatus(`Error: ${event.data.replace('ERROR:', '')}`);
              setIsProcessing(false); // Reset processing state on error
            } else {
              setStatus(`Server: ${event.data}`);
              setIsProcessing(false); // Reset processing state
            }
          }
        };

        socket.onclose = () => {
          console.log('WebSocket connection closed');
          setStatus('Connection closed - Refresh to reconnect');
          setIsProcessing(false); // Reset processing state
        };

        socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setStatus('Connection error - Check backend server');
          setIsProcessing(false); // Reset processing state on error
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setStatus('Failed to connect to server');
        setIsProcessing(false); // Reset processing state
      }
    };

    connectWebSocket();

    // Clean up on component unmount
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (audioRef.current) {
        audioRef.current.pause();
        if (audioRef.current.src) {
          URL.revokeObjectURL(audioRef.current.src);
        }
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setStatus('Requesting microphone permission...');
      console.log("Requesting microphone access");
      
      // Request access to the user's microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          sampleSize: 16,
        } 
      });
      console.log("Microphone access granted");
      
      // Create a new MediaRecorder instance
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Event handler for when data is available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log("Audio chunk received:", event.data.size, "bytes");
        }
      };

      // Event handler for when recording stops
      mediaRecorder.onstop = () => {
        if (isProcessing) {
          console.log("Already processing, skipping duplicate");
          return;
        }
        
        setIsProcessing(true);
        // Create a blob from the recorded audio chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Final audio blob created:', audioBlob.size, 'bytes');
        setStatus('Processing your speech...');
        
        // Check if WebSocket is connected and ready
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          console.log("Sending audio to server...");
          websocketRef.current.send(audioBlob);
          setStatus('Processing your message...');
        } else {
          console.error('WebSocket is not connected. Ready state:', websocketRef.current?.readyState);
          setStatus('Failed to send. Not connected.');
          setIsProcessing(false);
        }
        
        // Stop all audio tracks from the microphone stream
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      };

      // Start recording (NO time interval parameter)
      mediaRecorder.start();
      setIsRecording(true);
      setStatus('Recording... Speak now.');
      console.log("Recording started");

    } catch (error) {
      console.error('Error accessing microphone:', error);
      if (error.name === 'NotAllowedError') {
        setStatus('Permission denied. Please allow microphone access.');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        setStatus('No microphone found. Please check your device.');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        setStatus('Microphone is already in use by another application.');
      } else {
        setStatus(`Error: ${error.message}`);
      }
      setIsProcessing(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop(); // This triggers the 'onstop' event
      setIsRecording(false);
      setStatus('Finishing recording...');
    }
  };

  const PrivacyNotice = () => (
  <div style={{
    fontSize: '12px', 
    color: '#666', 
    textAlign: 'center', 
    marginTop: '20px',
    padding: '10px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    maxWidth: '400px',
    margin: '20px auto'
  }}>
    <strong>🔒 Your Privacy is Protected</strong>
    <br />
    All processing happens locally on your device. 
    No conversation data is sent to cloud servers.
  </div>
);

// Then add it to your return statement:
return (
  <div className="app">
    <h1>Astra</h1>
    <p>Your Empathetic Listener</p>
    <div className="status">{status}</div>
    <button
      className={`mic-button ${isRecording ? 'recording' : ''}`}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={isProcessing || status.includes('speaking')}
    >
      {isProcessing ? '🔄 Processing' : 
       status.includes('speaking') ? '🔊 AI Speaking' :
       isRecording ? '⏹️ Stop' : '🎤 Start Talking'}
    </button>
    <PrivacyNotice />
  </div>
);
}

export default App;