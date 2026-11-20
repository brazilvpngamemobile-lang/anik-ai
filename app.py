from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os

app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"

# কণ্ঠকে শান্ত (Calm) ও স্বাভাবিক করতে ফিল্টার
STUDIO_FILTER = (
    "highpass=f=85, lowpass=f=11000, "
    "equalizer=f=200:t=q:w=1:g=2.5, "
    "compand=attacks=0.05:decays=0.2:points=-80/-80|-20/-15|0/-6, "
    "aecho=0.8:0.88:30:0.15" 
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
    
    # ১. ডিফল্ট স্পিড আরও কমানো হলো (0.75x - ধীরে ও শান্তভাবে বলার জন্য)
    speed = float(data.get('speed', 0.75)) 
    speed = max(0.5, min(1.0, speed)) # সর্বোচ্চ ১.০ করা হলো, যাতে ইউজার দ্রুত করতে না পারে
    
    # ২. যতিচিহ্নের পর লম্বা বিরতি (Pause) যোগ করা, যাতে এআই শ্বাস নিতে পারে
    text = str(text)
    text = text.replace(",", ", , ")
    text = text.replace(".", ". . . ")
    text = text.replace("!", "! . . ")
    text = text.replace("?", "? . . ")
    
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
    
    # noise-scale কমিয়ে ০.৬ করা হলো, যাতে কণ্ঠ আরও স্ট্যাবল (শান্ত) শোনায়
    cmd = [
        SHERPA_CMD, 
        f'--vits-model={model_path}', 
        f'--vits-tokens={tokens_path}', 
        f'--vits-data-dir={data_dir}', 
        '--vits-lexicon=./lexicon-en-us.txt', 
        '--vits-noise-scale=0.6',
        '--vits-noise-scale-w=0.6',
        f'--output-filename={temp_wav}', 
        text
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        filters = [STUDIO_FILTER, f"atempo={speed}"]
        if voice_type in VOICE_EFFECTS: 
            filters.append(VOICE_EFFECTS[voice_type])
            
        final_filter = ", ".join(filters)
        
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
