/**
 * TerminFinder Voice Navigation System
 * 
 * Features:
 * - Whisper API for high-quality speech recognition (99+ languages)
 * - OpenAI TTS for natural voice synthesis
 * - Automatic language detection and response in same language
 * - Navigation commands + Help chatbot integration
 * - Works in ALL browsers (no Web Speech API limitations)
 * 
 * Architecture:
 * 1. User clicks microphone → MediaRecorder records audio
 * 2. Audio sent to /api/voice-transcribe → Whisper API → {text, language}
 * 3. Text sent to /api/help-chat with language → ChatGPT response
 * 4. Response sent to /api/voice-synthesize → OpenAI TTS → Audio playback
 * 
 * @version 1.0
 * @author TerminFinder Team
 */

class VoiceNavigationSystem {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.currentAudio = null;
        this.sessionId = this.generateSessionId();
        
        // UI Elements (will be created dynamically)
        this.voiceButton = null;
        this.statusIndicator = null;
        this.transcriptDisplay = null;
        
        // Configuration
        this.config = {
            maxRecordingTime: 30000, // 30 seconds max
            apiBaseUrl: window.location.origin,
            voiceMode: true // Always use voice-friendly responses
        };
        
        // Initialize on page load
        this.init();
    }
    
    /**
     * Initialize voice navigation system
     */
    async init() {
        // Check browser compatibility
        if (!this.checkBrowserSupport()) {
            console.warn('⚠️ Voice navigation not available: MediaRecorder not supported');
            return;
        }
        
        // Create UI
        this.createVoiceUI();
        
        // Request microphone permission on first interaction
        this.voiceButton.addEventListener('click', () => this.handleVoiceButtonClick());
        
        console.log('✅ Voice Navigation System initialized');
    }
    
    /**
     * Check if browser supports required APIs
     */
    checkBrowserSupport() {
        return !!(navigator.mediaDevices && 
                  navigator.mediaDevices.getUserMedia && 
                  window.MediaRecorder);
    }
    
    /**
     * Create voice navigation UI
     */
    createVoiceUI() {
        // Voice button (floating bottom-right)
        this.voiceButton = document.createElement('button');
        this.voiceButton.id = 'voice-nav-button';
        this.voiceButton.className = 'voice-nav-btn';
        this.voiceButton.title = 'Sprachnavigation aktivieren';
        this.voiceButton.innerHTML = `
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
        `;
        
        // Status indicator
        this.statusIndicator = document.createElement('div');
        this.statusIndicator.id = 'voice-nav-status';
        this.statusIndicator.className = 'voice-nav-status';
        this.statusIndicator.style.display = 'none';
        
        // Transcript display
        this.transcriptDisplay = document.createElement('div');
        this.transcriptDisplay.id = 'voice-nav-transcript';
        this.transcriptDisplay.className = 'voice-nav-transcript';
        this.transcriptDisplay.style.display = 'none';
        
        // Container
        const container = document.createElement('div');
        container.id = 'voice-nav-container';
        container.appendChild(this.voiceButton);
        container.appendChild(this.statusIndicator);
        container.appendChild(this.transcriptDisplay);
        
        // Add to page
        document.body.appendChild(container);
        
        // Add styles
        this.injectStyles();
    }
    
    /**
     * Inject CSS styles for voice navigation UI
     */
    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #voice-nav-container {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
            }
            
            .voice-nav-btn {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: none;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .voice-nav-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            
            .voice-nav-btn.recording {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            .voice-nav-btn.processing {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                animation: spin 2s linear infinite;
            }
            
            .voice-nav-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .voice-nav-status {
                position: absolute;
                bottom: 70px;
                left: 0;
                background: white;
                padding: 12px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                white-space: nowrap;
                font-size: 14px;
                color: #333;
            }
            
            .voice-nav-transcript {
                position: absolute;
                bottom: 110px;
                left: 0;
                max-width: 300px;
                background: white;
                padding: 16px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                font-size: 14px;
                color: #333;
                line-height: 1.4;
            }
            
            .voice-nav-transcript strong {
                display: block;
                margin-bottom: 8px;
                color: #667eea;
            }
            
            @media (max-width: 768px) {
                #voice-nav-container {
                    bottom: 10px;
                    left: 10px;
                }
                
                .voice-nav-btn {
                    width: 50px;
                    height: 50px;
                }
                
                .voice-nav-transcript {
                    max-width: calc(100vw - 80px);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Handle voice button click
     */
    async handleVoiceButtonClick() {
        if (this.isRecording) {
            // Stop recording
            this.stopRecording();
        } else {
            // Start recording
            await this.startRecording();
        }
    }
    
    /**
     * Start audio recording
     */
    async startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            
            // Check supported MIME types
            const mimeType = this.getSupportedMimeType();
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            this.audioChunks = [];
            
            // Event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.voiceButton.classList.add('recording');
            this.voiceButton.title = 'Aufnahme beenden';
            this.showStatus('🎤 Aufnahme läuft...');
            
            // Auto-stop after max time
            setTimeout(() => {
                if (this.isRecording) {
                    this.stopRecording();
                }
            }, this.config.maxRecordingTime);
            
            console.log('🎤 Recording started');
            
        } catch (error) {
            console.error('❌ Microphone access denied:', error);
            this.showStatus('❌ Mikrofonzugriff verweigert', 3000);
        }
    }
    
    /**
     * Stop audio recording
     */
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            // Update UI
            this.voiceButton.classList.remove('recording');
            this.voiceButton.classList.add('processing');
            this.voiceButton.disabled = true;
            this.voiceButton.title = 'Verarbeitung...';
            this.showStatus('⏳ Verarbeitung...');
            
            console.log('🛑 Recording stopped');
        }
    }
    
    /**
     * Process recorded audio
     */
    async processRecording() {
        try {
            // Create audio blob
            const mimeType = this.mediaRecorder.mimeType;
            const audioBlob = new Blob(this.audioChunks, { type: mimeType });
            
            console.log('📦 Audio blob created:', {
                size: audioBlob.size,
                type: audioBlob.type
            });
            
            // Step 1: Transcribe with Whisper API
            const transcription = await this.transcribeAudio(audioBlob);
            
            if (!transcription.success) {
                throw new Error(transcription.error || 'Transcription failed');
            }
            
            const { text, language } = transcription;
            console.log('📝 Transcribed:', text, '(Language:', language + ')');
            
            // Show transcript
            this.showTranscript(`Sie: ${text}`);
            
            // Step 2: Process with Help Chatbot
            const chatResponse = await this.processWithChatbot(text, language);
            
            if (!chatResponse.response) {
                throw new Error('No response from chatbot');
            }
            
            console.log('💬 Chatbot response:', chatResponse.response);
            
            // Show response
            this.showTranscript(`Assistent: ${chatResponse.response}`);
            
            // Step 3: Synthesize speech with TTS
            await this.synthesizeSpeech(chatResponse.response, language);
            
            // Success
            this.showStatus('✅ Fertig!', 2000);
            
        } catch (error) {
            console.error('❌ Processing error:', error);
            this.showStatus('❌ Fehler: ' + error.message, 3000);
            
        } finally {
            // Reset UI
            this.voiceButton.classList.remove('processing');
            this.voiceButton.disabled = false;
            this.voiceButton.title = 'Sprachnavigation aktivieren';
        }
    }
    
    /**
     * Transcribe audio with Whisper API
     */
    async transcribeAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        const response = await fetch(`${this.config.apiBaseUrl}/api/voice-transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Transcription failed');
        }
        
        return await response.json();
    }
    
    /**
     * Process text with Help Chatbot
     */
    async processWithChatbot(text, language) {
        const response = await fetch(`${this.config.apiBaseUrl}/api/help-chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                current_page: window.location.pathname,
                session_id: this.sessionId,
                language: language,
                voice_mode: this.config.voiceMode
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Chatbot error');
        }
        
        return await response.json();
    }
    
    /**
     * Synthesize speech with OpenAI TTS
     */
    async synthesizeSpeech(text, language) {
        const response = await fetch(`${this.config.apiBaseUrl}/api/voice-synthesize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                language: language
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Speech synthesis failed');
        }
        
        // Get audio blob
        const audioBlob = await response.blob();
        
        // Play audio
        await this.playAudio(audioBlob);
    }
    
    /**
     * Play audio blob
     */
    async playAudio(audioBlob) {
        return new Promise((resolve, reject) => {
            // Stop current audio if playing
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }
            
            // Create audio element
            const audioUrl = URL.createObjectURL(audioBlob);
            this.currentAudio = new Audio(audioUrl);
            
            this.currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                resolve();
            };
            
            this.currentAudio.onerror = (error) => {
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                reject(error);
            };
            
            // Play
            this.currentAudio.play().catch(reject);
            
            this.showStatus('🔊 Wiedergabe...');
        });
    }
    
    /**
     * Get supported audio MIME type for MediaRecorder
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/mpeg'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return ''; // Browser will use default
    }
    
    /**
     * Show status message
     */
    showStatus(message, duration = null) {
        this.statusIndicator.textContent = message;
        this.statusIndicator.style.display = 'block';
        
        if (duration) {
            setTimeout(() => {
                this.statusIndicator.style.display = 'none';
            }, duration);
        }
    }
    
    /**
     * Show transcript (conversation)
     */
    showTranscript(text) {
        this.transcriptDisplay.innerHTML = text.split('\n').join('<br>');
        this.transcriptDisplay.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.transcriptDisplay.style.display = 'none';
        }, 10000);
    }
    
    /**
     * Generate session ID
     */
    generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.voiceNav = new VoiceNavigationSystem();
    });
} else {
    window.voiceNav = new VoiceNavigationSystem();
}
