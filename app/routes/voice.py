"""
Voice navigation routes for TerminFinder
Whisper API for speech-to-text
OpenAI TTS for text-to-speech
Multi-language support with auto-detection
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from app import limiter
import openai
import os
from io import BytesIO
import tempfile

voice_bp = Blueprint('voice', __name__)


def get_openai_client():
    """
    Create OpenAI client with Render.com proxy workaround
    """
    # Proxy-Variablen temporär entfernen (Render.com fix)
    proxy_vars = {}
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
        if key in os.environ:
            proxy_vars[key] = os.environ[key]
            del os.environ[key]
    
    try:
        import httpx
        
        http_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
        
        client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            http_client=http_client
        )
        
        return client
    finally:
        # Proxy-Variablen wiederherstellen
        for key, value in proxy_vars.items():
            os.environ[key] = value


@voice_bp.route('/api/voice-transcribe', methods=['POST'])
@limiter.limit("20 per minute")
def transcribe_audio():
    """
    Transcribe audio using Whisper API with automatic language detection
    Accepts: audio/webm, audio/mp4, audio/mpeg, audio/wav
    Returns: {text: string, language: string}
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Create temporary file for Whisper API (it requires a file-like object with name)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name
        
        try:
            # Get OpenAI client
            client = get_openai_client()
            
            # Transcribe with Whisper API
            with open(temp_audio_path, 'rb') as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language=None,  # Auto-detect language
                    response_format="verbose_json"  # Get language info
                )
            
            # Extract text and detected language
            text = transcript.text
            language = transcript.language if hasattr(transcript, 'language') else 'de'
            
            # Clean up temp file
            os.unlink(temp_audio_path)
            
            return jsonify({
                'text': text,
                'language': language,
                'success': True
            })
        
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            raise e
    
    except openai.OpenAIError as e:
        return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500


@voice_bp.route('/api/voice-synthesize', methods=['POST'])
@limiter.limit("20 per minute")
def synthesize_speech():
    """
    Synthesize speech using OpenAI TTS API
    Accepts: {text: string, language: string (optional)}
    Returns: audio/mpeg (MP3 file)
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        language = data.get('language', 'de')  # Default to German
        
        # Limit text length (OpenAI TTS max is 4096 characters)
        if len(text) > 4096:
            text = text[:4093] + "..."
        
        # Select voice based on language
        voice_map = {
            'de': 'alloy',   # German - neutral voice
            'en': 'echo',    # English - male voice
            'ru': 'nova',    # Russian - female voice
            'uk': 'nova',    # Ukrainian - female voice
            'ar': 'onyx',    # Arabic - deep voice
            'es': 'shimmer', # Spanish - female voice
            'fr': 'shimmer', # French - female voice
            'it': 'alloy',   # Italian - neutral voice
        }
        
        voice = voice_map.get(language, 'alloy')
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Generate speech with OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # Use tts-1-hd for higher quality
            voice=voice,
            input=text,
            response_format="mp3",
            speed=1.0
        )
        
        # Stream audio directly to client
        audio_stream = BytesIO(response.content)
        audio_stream.seek(0)
        
        return send_file(
            audio_stream,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
    
    except openai.OpenAIError as e:
        return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Speech synthesis failed: {str(e)}'}), 500


@voice_bp.route('/api/voice-navigate', methods=['POST'])
@limiter.limit("20 per minute")
def voice_navigate():
    """
    Complete voice navigation flow:
    1. Transcribe audio (Whisper)
    2. Process command with Help Chatbot (language-aware)
    3. Synthesize response (TTS)
    Returns: {text: string, audio_url: string, language: string}
    """
    try:
        # This endpoint can be used for future optimization
        # to reduce round-trips (transcribe + chat + TTS in one call)
        return jsonify({
            'message': 'Use /api/voice-transcribe and /api/voice-synthesize separately',
            'status': 'not_implemented'
        }), 501
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_bp.route('/api/voice-test', methods=['GET'])
def test_voice_api():
    """
    Test endpoint to verify Whisper and TTS API configuration
    """
    try:
        # Check if OpenAI API key is set
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'OPENAI_API_KEY not configured'
            }), 500
        
        return jsonify({
            'status': 'ready',
            'message': 'Voice API is configured',
            'endpoints': {
                'transcribe': '/api/voice-transcribe',
                'synthesize': '/api/voice-synthesize',
            },
            'supported_languages': [
                'de (German)', 'en (English)', 'ru (Russian)', 
                'uk (Ukrainian)', 'ar (Arabic)', 'es (Spanish)',
                'fr (French)', 'it (Italian)', 'auto-detect'
            ],
            'whisper_model': 'whisper-1',
            'tts_model': 'tts-1',
            'rate_limit': '20 requests/minute'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
