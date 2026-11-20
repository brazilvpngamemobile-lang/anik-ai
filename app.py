from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os

app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"

# 🌟 Professional Studio Master Filters
# deesser: শিসের মতো আওয়াজ দূর করে
# equalizer: গলার গভীরতা (250Hz) ও স্পষ্টতা (3500Hz) বাড়ায়
# compand & dynaudnorm: ভলিউম একদম সমান রাখে (Radio/Podcast Quality)
STUDIO_FILTER = (
    "highpass=f=80, lowpass=f=13000, "
    "deesser, "
    "equalizer=f=250:t=q:w=1:g=2.5, "
    "equalizer=f=3500:t=q:w=1.5:g=1.5, "
    "compand=attacks=0.05:decays=0.2:points=-80/-80|-20/-15|0/-5, "
    "dynaudnorm=f=150:g=10" 
)

VOICE_EFFECTS = {
    "Deep Male": "asetrate=22050*0.92,atempo=1.08", 
    "News Anchor": "volume=1.1,equalizer=f=4000:t=q:w=1:g=2", 
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
    
    # ৩. স্পিড ডিফল্ট 0.9x (স্বাভাবিক প্রফেশনাল গতি)
    speed = float(data.get('speed', 0.9)) 
    speed = max(0.6, min(1.2, speed)) 
    
    temp_wav = 'temp_output.wav'
    final_wav = 'output.wav'
    
    if "Male" in voice_type or "News Anchor" in voice_type:
        model_path = "./vits-piper-en_US-ryan-medium/en_US-ryan-medium.onnx"
        tokens_path = "./vits-piper-en_US-ryan-medium/tokens.txt"
        data_dir = "./vits-piper-en_US-ryan-medium/espeak-ng-data"
    else:
        model_path = "./vits-piper-en_US-lessac-medium/en_US-lessac-medium.onnx"
        tokens_path = "./vits-piper-en_US-lessac-medium/tokens.txt"
        data_dir = "./vits-piper-en_US-lessac-medium/espeak-ng-data"
    
    # noise-scale 0.667 হলো পাইপারের ডিফল্ট, যা সবচেয়ে ন্যাচারাল শোনায়
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
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        filters = [STUDIO_FILTER, f"atempo={speed}"]
        if voice_type in VOICE_EFFECTS: 
            filters.append(VOICE_EFFECTS[voice_type])
            
        final_filter = ", ".join(filters)
        
        # CD Quality (44100 Hz)
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
