#!/usr/bin/env bash
set -euo pipefail
apt-get update && apt-get install -y ffmpeg
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.12.21/sherpa-onnx-v1.12.21-linux-x64-shared.tar.bz2
tar -xjf sherpa-onnx-v1.12.21-linux-x64-shared.tar.bz2

# High Quality Female Model (Lessac)
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-high.tar.bz2
tar -xjf vits-piper-en_US-lessac-high.tar.bz2

# High Quality Male Model (Ryan)
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-ryan-high.tar.bz2
tar -xjf vits-piper-en_US-ryan-high.tar.bz2

wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/lexicon-en-us.txt
