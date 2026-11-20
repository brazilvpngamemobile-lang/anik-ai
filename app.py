from flask import Flask, request, render_template, send_file, jsonify
import subprocess
import os
import re

app = Flask(__name__, template_folder='templates')

SHERPA_CMD = "./sherpa-onnx-v1.12.21-linux-x64-shared/bin/sherpa-onnx-offline-tts"

# Ultra-Realistic Studio Filters:
# ১. aecho: হালকা রুম রিভার্ব (যেমনটা বাস্তবে শোনা যায়)
# ২. equalizer: মানুষের কণ্ঠের ওয়ার্মথ এবং ক্ল্যারিটি বাড়ানো
# ৩. compand: ভলিউমের ওঠানামা নিয়ন্ত্রণ করা
STUDIO_FILTER = (
    "highpass=f=85, lowpass=f=11000, "
    "equalizer=f=200:t=q:w=1:g=2.5, "
    "equalizer=f=3500:t=q:w=1.5:g=1, "
    "compand=attacks=0.05:decays=0.2:points=-80/-80|-20/-15|0/-6, "
    "aecho=0.8:0.88:20:0.1" 
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
    
    # ডিফল্ট স্পিড ০.৮ করা হলো (খুব বেশি ধীরে ও স্বাভাবিক)
    speed = float(data.get('speed', 0.8)) 
    speed = max(0.5, min(1.2, speed)) 
    
    # কমা বা দাঁড়ির পর ন্যাচারাল শ্বাস নেওয়ার জন্য স্পেস
    text = re.sub(r'([.,!?])', r'\1 ', text)
    
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
    
    # --vits-noise-scale এবং --vits-noise-scale-w যোগ করা হলো রোবটিক ভাব কাটানোর জন্য
    cmd = [
        SHERPA_CMD, 
        f'--vits-model={model_path}', 
        f'--vits-tokens={tokens_path}', 
        f'--vits-data-dir={data_dir}', 
        '--vits-lexicon=./lexicon-en-us.txt', 
        '--vits-noise-scale=0.8',
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
        
        # -ar 44100 দিয়ে CD কোয়ালিটি নিশ্চিত করা হয়েছে
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
