# ==========================================
# Step 02: Movie Transcription & Diarization Pipeline (Python 3.10/3.13)
# ==========================================
import os
import sys
import subprocess

print("=" * 50)
print("🚀 Step 02: Movie Transcription & Diarization শুরু হচ্ছে...")
print("=" * 50)

# ১. প্রয়োজনীয় প্যাকেজগুলো নিরাপদ উপায়ে ইনস্টল করা
print("\n📦 [১/৪] প্রয়োজনীয় প্যাকেজ চেক ও ইনস্টল করা হচ্ছে...")
subprocess.run([sys.executable, "-m", "pip", "install", "openai-whisper", "demucs", "soundfile", "librosa", "--quiet"])
subprocess.run([sys.executable, "-m", "pip", "install", "diarize==0.1.2", "--no-cache-dir", "--quiet"])

import torch
import whisper
from diarize import diarize
import soundfile as sf
import librosa
import numpy as np

# ফোল্ডার পাথ কনফিগারেশন
BASE_DIR = "output_dubbing"
VOCAL_DIR = os.path.join(BASE_DIR, "vocal")
RESULT_DIR = os.path.join(BASE_DIR, "transcription_speakers")

def custom_load_audio(file_path, sr=16000):
    audio, sample_rate = sf.read(file_path)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    if sample_rate != sr:
        audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=sr)
    return audio.astype(np.float32)

def run_step02_pipeline():
    os.makedirs(RESULT_DIR, exist_ok=True)
    
    if not os.path.exists(VOCAL_DIR):
        print(f"❌ ভোকাল ফোল্ডার পাওয়া যায়নি: {VOCAL_DIR}")
        print(f"💡 টিপস: প্রথমে Demucs দিয়ে অডিও থেকে ভোকাল আলাদা করে 'output_dubbing/vocal' ফোল্ডারে সেভ করুন।")
        return
        
    vocal_files = [os.path.join(VOCAL_DIR, f) for f in os.listdir(VOCAL_DIR) if f.endswith(".wav")]
    if not vocal_files:
        print(f"❌ Demucs-এর কোনো ভোকাল অডিও ফাইল পাওয়া যায়নি!")
        return
        
    # Demucs ফোল্ডার থেকে লেটেস্ট ভোকাল ফাইলটি স্বয়ংক্রিয়ভাবে পিক করা
    vocal_audio_path = max(vocal_files, key=os.path.getmtime)
    base_filename = os.path.basename(vocal_audio_path)
    filename = base_filename.replace("_vocals.wav", "").replace(".wav", "")
    output_txt_path = os.path.join(RESULT_DIR, f"{filename}_step02_report.txt")
    
    print(f"\n🎯 টার্গেট অডিও ফাইল: {base_filename}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"💻 প্রসেসিং ডিভাইস: {device.upper()}")
    
    try:
        # ২. Whisper Large-v2 দিয়ে ট্রান্সক্রিপশন
        print("\n🎙️ [২/৪] Whisper Large-v2 মডেল দিয়ে ট্রান্সক্রিপশন চলছে...")
        model = whisper.load_model("large-v2", device=device)
        transcription_result = model.transcribe(vocal_audio_path)
        
        # ৩. diarize==0.1.2 দিয়ে স্পিকার ডায়রাইজেশন
        print("👥 [৩/৪] diarize প্যাকেজের মাধ্যমে স্পিকার ডায়রাইজেশন চলছে...")
        diarization_result = diarize(vocal_audio_path)
        diarization_segments = diarization_result.segments if hasattr(diarization_result, "segments") else diarization_result
        
        # ৪. টেক্সট এবং স্পিকার সেগমেন্ট মেলানো ও ফাইনাল রিপোর্ট তৈরি
        print("\n📝 [৪/৪] ফাইনাল ডাবিং রিপোর্ট তৈরি করা হচ্ছে...")
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("=== Step 02 Movie Dubbing & Diarization Report ===\n\n")
            
            segments = transcription_result.get("segments", [])
            for seg in segments:
                start = seg.get("start", 0.0)
                end = seg.get("end", 0.0)
                text = seg.get("text", "").strip()
                
                matched_speaker = "SPEAKER_00"
                for d_seg in diarization_segments:
                    d_start = d_seg.start if hasattr(d_seg, "start") else d_seg.get("start", 0.0)
                    d_end = d_seg.end if hasattr(d_seg, "end") else d_seg.get("end", 0.0)
                    d_speaker = d_seg.speaker if hasattr(d_seg, "speaker") else d_seg.get("speaker", "SPEAKER_00")
                    
                    if max(start, d_start) < min(end, d_end):
                        matched_speaker = d_speaker
                        break
                
                line = f"[{start:.2f}s - {end:.2f}s] [{matched_speaker}]: {text}"
                f.write(line + "\n")
                print(line)
                
        print(f"\n" + "=" * 50)
        print(f"🎉 Step 02 সফলভাবে সম্পূর্ণ হয়েছে!")
        print(f"📄 বিস্তারিত রিপোর্ট সংরক্ষিত হয়েছে: {output_txt_path}")
        print("=" * 50)
        
    except Exception as e:
        import traceback
        print(f"❌ প্রসেসিং ত্রুটি:")
        traceback.print_exc()

if __name__ == "__main__":
    run_step02_pipeline()
