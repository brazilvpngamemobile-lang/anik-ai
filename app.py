from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os
import gc

app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"
STUDIO_FILTER = "highpass=f=85, lowpass=f=11000, equalizer=f=200:t=q:w=1:g=2.5, compand=attacks=0.05:decays=0.2:points=-80/-80|-20/-15|0/-6"
VOICE_EFFECTS = {"Deep Male": "asetrate=22050*0.92,atempo=1.08", "News Anchor": "volume=1.1,equalizer=f=4000:t=q:w=1:g=2", "Whispering": "volume=0.4,highpass=f=1000"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text', '').strip()
    voice_type = data.get('voice', 'Professional Female')
    speed = float(data.get('speed', 0.9))
    
    # 🚀 সার্ভার সুরক্ষার জন্য ৫০০ ক্যারেক্টার লিমিট
    if len(text) > 500:
        return jsonify({"success": False, "error": "Text is too long! Please limit to 500 characters."})
    
    if not text:
        return jsonify({"success": False, "error": "Text cannot be empty."})

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
    
    cmd = [SHERPA_CMD, f'--vits-model={model_path}', f'--vits-tokens={tokens_path}', f'--vits-data-dir={data_dir}', '--vits-lexicon=./lexicon-en-us.txt', '--vits-noise-scale=0.667', f'--output-filename={temp_wav}', text]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        filters = [STUDIO_FILTER, f"atempo={speed}"]
        if voice_type in VOICE_EFFECTS: filters.append(VOICE_EFFECTS[voice_type])
        final_filter = ", ".join(filters)
        subprocess.run(f'ffmpeg -y -i {temp_wav} -filter:a "{final_filter}" -ar 44100 {final_wav}', shell=True, check=True, capture_output=True)
        
        if os.path.exists(temp_wav): os.remove(temp_wav)
        gc.collect() # মেমোরি ক্লিয়ার করা
        return jsonify({"success": True, "audio_url": "/audio"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": "Server limit reached. Please try a slightly shorter text."})

@app.route('/audio')
def get_audio(): return send_file('output.wav', mimetype='audio/wav')

@app.route('/download')
def download_audio(): return send_file('output.wav', mimetype='audio/wav', as_attachment=True, download_name='Anik_AI_Voice.wav')

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
