from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os

app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"

# 🎙️ Pure Natural Studio Filter
# কম্প্রেশন হালকা করা হয়েছে এবং ইকো সরিয়ে দেওয়া হয়েছে যাতে একদম ন্যাচারাল শোনায়
STUDIO_FILTER = (
    "highpass=f=80, lowpass=f=13000, "
    "dynaudnorm=f=150:g=10" 
)

VOICE_EFFECTS = {
    "Deep Male": "asetrate=22050*0.92,atempo=1.08", 
    "News Anchor": "volume=1.1", 
    "Whispering": "volume=0.4,highpass=f=1000"
}

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {str(e)}"

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text')
    voice_type = data.get('voice', 'Professional Female')
    
    speed = float(data.get('speed', 0.9)) 
    speed = max(0.7, min(1.1, speed)) # স্পিড লিমিট ০.৭ থেকে ১.১ এর মধ্যে রাখা হলো
    
    temp_wav = 'temp_output.wav'
    final_wav = 'output.wav'
    
    # High Quality মডেলের পাথ আপডেট করা হলো
    if "Male" in voice_type or "News Anchor" in voice_type:
        model_path = "./vits-piper-en_US-ryan-high/en_US-ryan-high.onnx"
        tokens_path = "./vits-piper-en_US-ryan-high/tokens.txt"
        data_dir = "./vits-piper-en_US-ryan-high/espeak-ng-data"
    else:
        model_path = "./vits-piper-en_US-lessac-high/en_US-lessac-high.onnx"
        tokens_path = "./vits-piper-en_US-lessac-high/tokens.txt"
        data_dir = "./vits-piper-en_US-lessac-high/espeak-ng-data"
    
    # Piper-এর ডিফল্ট ন্যাচারাল প্যারামিটার ব্যবহার করা হলো
    cmd = [
        SHERPA_CMD, 
        f'--vits-model={model_path}', 
        f'--vits-tokens={tokens_path}', 
        f'--vits-data-dir={data_dir}', 
        '--vits-lexicon=./lexicon-en-us.txt', 
        '--vits-noise-scale=0.667',
        '--vits-noise-scale-w=0.8',
        f'--output-filename={temp_wav}', 
        text
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        filters = [STUDIO_FILTER, f"atempo={speed}"]
        if voice_type in VOICE_EFFECTS: 
            filters.append(VOICE_EFFECTS[voice_type])
            
        final_filter = ", ".join(filters)
        
        # 44100 Hz CD Quality
        subprocess.run(f'ffmpeg -y -i {temp_wav} -filter:a "{final_filter}" -ar 44100 {final_wav}', shell=True, check=True, capture_output=True)
        
        if os.path.exists(temp_wav): 
            os.remove(temp_wav)
        return jsonify({"success": True, "audio_url": "/audio"})
        
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e.stderr)})

@app.route('/audio')
def get_audio(): 
    return send_file('output.wav', mimetype='audio/wav')

@app.route('/download')
def download_audio(): 
    return send_file('output.wav', mimetype='audio/wav', as_attachment=True, download_name='Anik_AI_Voice.wav')

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000)
