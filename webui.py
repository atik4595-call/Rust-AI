# ==========================================
# Ultimate Movie Dubbing & Diarization Web UI
# ==========================================
import os
import sys
import subprocess
import gradio as gr

print("🚀 Movie Dubbing Web UI চালু হচ্ছে...")

def process_movie_pipeline(video_file):
    if video_file is None:
        yield "❌ দয়া করে একটি ভিডিও ফাইল আপলোড করুন!", None, None, "রিপোর্ট পাওয়া যায়নি।"
        return
    
    video_path = video_file.name if hasattr(video_file, "name") else video_file
    logs = "=== পাইপলাইন প্রসেসিং শুরু হয়েছে ===\n"
    yield logs, None, None, "প্রসেসিং চলছে..."
    
    # Step 01 (Demucs) রান করা
    step01_path = os.path.join("tools", "step01_demucs.py")
    if not os.path.exists(step01_path):
        yield f"❌ এরর: {step01_path} ফাইলটি পাওয়া যায়নি!", None, None, "রিপোর্ট পাওয়া যায়নি।"
        return
    
    logs += "▶️ Step 01 (Demucs & FFmpeg) দিয়ে অডিও সেপারেশন শুরু হচ্ছে...\n"
    yield logs, None, None, "প্রসেসিং চলছে..."
    
    sys.path.append(os.path.abspath("tools"))
    try:
        from step01_demucs import run_demucs_pipeline
        music_path, vocal_path = run_demucs_pipeline(video_path)
        logs += f"✅ Step 01 সফল!\n- Music (BGM): {music_path}\n- Vocal: {vocal_path}\n\n"
        yield logs, music_path, vocal_path, "প্রসেসিং চলছে..."
    except Exception as e:
        import traceback
        error_msg = logs + f"❌ Step 01 এ ত্রুটি:\n{traceback.format_exc()}"
        yield error_msg, None, None, "রিপোর্ট পাওয়া যায়নি।"
        return
    
    # Step 02 (Whisper & Diarization) রান করা (Live Popen Stream সহ)
    logs += "▶️ Step 02 (Whisper Large-v2 & Diarization) শুরু হচ্ছে...\n"
    yield logs, music_path, vocal_path, "প্রসেসিং চলছে..."
    
    step02_path = os.path.join("tools", "step02_whisper.py")
    
    if os.path.exists(step02_path):
        try:
            process = subprocess.Popen(
                [sys.executable, "-u", step02_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                print(line, end="")
                logs += line
                yield logs, music_path, vocal_path, "প্রসেসিং চলছে..."
                
            process.wait()
            
            if process.returncode == 0:
                logs += "\n✅ Step 02 সফলভাবে শেষ হয়েছে!\n\n"
            else:
                logs += f"\n❌ Step 02 এ ত্রুটি ঘটেছে (Exit code: {process.returncode})\n"
                
        except Exception as e:
            logs += f"\n❌ Step 02 সাবপ্রসেস ত্রুটি: {str(e)}\n"
    else:
        logs += f"❌ এরর: {step02_path} ফাইলটি পাওয়া যায়নি!\n"
        
    yield logs, music_path, vocal_path, "প্রসেসিং চলছে..."

    # ফাইনাল রিপোর্ট ফাইল লোড করা
    result_dir = os.path.join("output_dubbing", "transcription_speakers")
    report_content = "রিপোর্ট ফাইল পাওয়া যায়নি।"
    
    if os.path.exists(result_dir):
        reports = [os.path.join(result_dir, f) for f in os.listdir(result_dir) if f.endswith(".txt")]
        if reports:
            latest_report = max(reports, key=os.path.getmtime)
            logs += f"📄 ফাইনাল রিপোর্ট ফাইল: {latest_report}\n"
            with open(latest_report, "r", encoding="utf-8") as rf:
                report_content = rf.read()
                
    yield logs, music_path, vocal_path, report_content

# Gradio Interface ডিজাইন
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 Ultimate Movie Dubbing & Diarization Pipeline")
    gr.Markdown("ভিডিও আপলোড করুন। এটি স্বয়ংক্রিয়ভাবে BGM (Music) ও Vocal আলাদা করবে এবং Whisper ও Diarization রিপোর্ট জেনারেট করবে।")
    
    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.File(label="ভিডিও ফাইল আপলোড করুন (.mp4, .mkv ইত্যাদি)", file_types=[".mp4", ".mkv", ".avi", ".mov"])
            submit_btn = gr.Button("🚀 পাইপলাইন রান করুন", variant="primary")
            
            gr.Markdown("### 🎵 সেপারেট অডিও আউটপুট")
            music_output = gr.Audio(label="Background Music (No Vocals)", type="filepath")
            vocal_output = gr.Audio(label="Isolated Vocals", type="filepath")
            
        with gr.Column(scale=1):
            output_logs = gr.Textbox(label="প্রসেসিং লাইভ লগ (Live Terminal Logs)", lines=18)
            
    with gr.Row():
        output_report = gr.Textbox(label="📝 Step 02 ডাবিং ও স্পিকার ডায়রাইজেশন রিপোর্ট (Transcript Report)", lines=12)

    submit_btn.click(
        fn=process_movie_pipeline, 
        inputs=video_input, 
        outputs=[output_logs, music_output, vocal_output, output_report]
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
