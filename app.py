from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"
STUDIO_FILTER = "highpass=f=85, lowpass=f=11000, equalizer=f=200:t=q:w=1:g=2.5, compand=attacks=0.05:decays=0.2:points=-80/-80|-20/-15|0/-6"

VOICE_EFFECTS = {
    "Deep Male": "asetrate=22050*0.92,atempo=1.08",
    "News Anchor": "volume=1.1,equalizer=f=4000:t=q:w=1:g=2",
    "Whispering": "volume=0.4,highpass=f=1000"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid request body. Please try again."
        }), 400

    text = str(data.get('text', '')).strip()
    voice_type = str(data.get('voice', 'Professional Female'))

    try:
        speed = float(data.get('speed', 0.9))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Invalid speed value."
        }), 400

    if len(text) > 300:
        return jsonify({
            "success": False,
            "error": "Text is too long! Please limit to 300 characters."
        }), 400

    if not text:
        return jsonify({
            "success": False,
            "error": "Text cannot be empty."
        }), 400

    speed = max(0.7, min(1.1, speed))

    temp_wav = 'temp_output.wav'
    final_wav = 'output.wav'

    if "Male" in voice_type or "News Anchor" in voice_type:
        model_path = "./vits-piper-en_US-ryan-high/en_US-ryan-high.onnx"
        tokens_path = "./vits-piper-en_US-ryan-high/tokens.txt"
        data_dir = "./vits-piper-en_US-ryan-high/espeak-ng-data"
    else:
        model_path = "./vits-piper-en_US-lessac-high/en_US-lessac-high.onnx"
        tokens_path = "./vits-piper-en_US-lessac-high/tokens.txt"
        data_dir = "./vits-piper-en_US-lessac-high/espeak-ng-data"

    cmd = [
        SHERPA_CMD,
        f'--vits-model={model_path}',
        f'--vits-tokens={tokens_path}',
        f'--vits-data-dir={data_dir}',
        '--vits-lexicon=./lexicon-en-us.txt',
        '--vits-noise-scale=0.667',
        f'--output-filename={temp_wav}',
        text
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        filters = [STUDIO_FILTER, f"atempo={speed}"]

        if voice_type in VOICE_EFFECTS:
            filters.append(VOICE_EFFECTS[voice_type])

        final_filter = ", ".join(filters)

        subprocess.run(
            [
                'ffmpeg', '-y',
                '-i', temp_wav,
                '-filter:a', final_filter,
                '-ar', '44100',
                final_wav
            ],
            check=True,
            capture_output=True,
            timeout=60
        )

        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        return jsonify({
            "success": True,
            "audio_url": "/audio"
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Voice generation timed out. Please try a shorter text."
        }), 504

    except subprocess.CalledProcessError as e:
        app.logger.error('TTS command failed: %s', e.stderr)

        return jsonify({
            "success": False,
            "error": "Voice generation failed on the server. Please try again."
        }), 500

    except Exception:
        app.logger.exception('Unexpected voice generation error')

        return jsonify({
            "success": False,
            "error": "An unexpected server error occurred. Please try again."
        }), 500


@app.route('/audio')
def get_audio():
    audio_path = BASE_DIR / 'output.wav'

    if not audio_path.is_file():
        return jsonify({
            "success": False,
            "error": "No generated audio is available yet."
        }), 404

    return send_file(audio_path, mimetype='audio/wav')


@app.route('/download')
def download_audio():
    audio_path = BASE_DIR / 'output.wav'

    if not audio_path.is_file():
        return jsonify({
            "success": False,
            "error": "Generate a voice before downloading."
        }), 404

    return send_file(
        audio_path,
        mimetype='audio/wav',
        as_attachment=True,
        download_name='Anik_AI_Voice.wav'
    )


@app.errorhandler(404)
def handle_not_found(error):
    if request.path.startswith('/generate') or request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": "API endpoint not found. Check the Render service deployment and start command."
        }), 404

    return error


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
