import os
import shutil
import subprocess
import sys

BASE_DIR = "output_dubbing"
MUSIC_DIR = os.path.join(BASE_DIR, "Music")
VOCAL_DIR = os.path.join(BASE_DIR, "vocal")

def setup_directories():
    for folder in [MUSIC_DIR, VOCAL_DIR]:
        os.makedirs(folder, exist_ok=True)

def run_demucs_pipeline(video_path):
    """
    ইনপুট ভিডিও থেকে Demucs ও FFmpeg এর মাধ্যমে BGM এবং Vocal আলাদা করে।
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"ভিডিও ফাইলটি পাওয়া যায়নি: {video_path}")
    
    setup_directories()
    
    filename = os.path.splitext(os.path.basename(video_path))[0]
    extracted_wav = os.path.join(BASE_DIR, "extracted_speech.wav")
    
    print("\n[১/৩] ভিডিও থেকে অডিও এক্সট্র্যাক্ট করা হচ্ছে...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", extracted_wav
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Demucs: Audio Separation
    print("[২/৩] Demucs দিয়ে মিউজিক ও ভোকাল আলাদা করা হচ্ছে...")
    demucs_out = os.path.join(BASE_DIR, "demucs_temp")
    demucs_cmd = [
        "demucs", "--two-stems=vocals", "-n", "htdemucs", 
        "-o", demucs_out, extracted_wav
    ]
    subprocess.run(demucs_cmd, check=True)
    
    htdemucs_path = os.path.join(demucs_out, "htdemucs", "extracted_speech")
    music_source = os.path.join(htdemucs_path, "no_vocals.wav")
    vocal_source = os.path.join(htdemucs_path, "vocals.wav")
    
    final_music_path = os.path.join(MUSIC_DIR, f"{filename}_bgm.wav")
    final_vocal_path = os.path.join(VOCAL_DIR, f"{filename}_vocals.wav")
    
    shutil.copy(music_source, final_music_path)
    shutil.copy(vocal_source, final_vocal_path)
    
    # [৩/৩] ফাইল ভ্যালিডেশন চেক
    print("[৩/৩] আউটপুট ফাইল ভ্যালিডেশন চেক চলছে...")
    checks = {
        "Music File (BGM)": os.path.exists(final_music_path) and os.path.getsize(final_music_path) > 0,
        "Vocal File": os.path.exists(final_vocal_path) and os.path.getsize(final_vocal_path) > 0,
    }
    
    for key, status in checks.items():
        if not status:
            raise RuntimeError(f"ফাইল তৈরিতে ত্রুটি: {key} সঠিক নয়!")
            
    print("🎉 মিউজিক এবং ভোকাল সফলভাবে সঠিক ফোল্ডারে সেভ হয়েছে!")
    print(f"- Music Path: {final_music_path}")
    print(f"- Vocal Path: {final_vocal_path}")

    # ==========================================
    # অটো Step 02 (Whisper & Diarization) কল করা
    # ==========================================
    print("\n" + "=" * 50)
    print("🚀 Step 01 সফলভাবে শেষ! এখন স্বয়ংক্রিয়ভাবে Step 02 শুরু হচ্ছে...")
    print("=" * 50)

    # সরাসরি tools ফোল্ডারের ভেতরের step02_whisper.py ফাইলের পাথ
    step02_script_path = os.path.join("tools", "step02_whisper.py")

    if os.path.exists(step02_script_path):
        # সাবপ্রসেস দিয়ে step02_whisper.py রান করা
        result = subprocess.run([sys.executable, step02_script_path])
        
        if result.returncode == 0:
            print("\n🎉 আলহামদুলিল্লাহ! Step 01 এবং Step 02 উভয় পাইপলাইন সফলভাবে শেষ হয়েছে!")
        else:
            print("\n❌ Step 02 রান করার সময় কোনো ত্রুটি হয়েছে।")
    else:
        print(f"\n❌ এরর: Step 02 ফাইলটি নির্দিষ্ট পথে পাওয়া যায়নি: {step02_script_path}")
    
    return final_music_path, final_vocal_path

if __name__ == "__main__":
    # টেস্ট করার জন্য এখানে আপনার ভিডিও ফাইলের পাথ দিয়ে রান করতে পারেন
    # run_demucs_pipeline("your_video.mp4")
    pass
