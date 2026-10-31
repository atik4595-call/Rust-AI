# ==========================================
# Movie Dubbing Pipeline Web UI (Gradio) - Live Stream Enabled
# ==========================================
import os
import sys
import subprocess
import gradio as gr

print("🚀 Movie Dubbing Web UI চালু হচ্ছে...")

def process_movie_pipeline(video_file):
    if video_file is None:
        return "❌ দয়া করে একটি ভিডিও ফাইল আপলোড করুন!", "রিপোর্ট পাওয়া যায়নি।"
    
    video_path = video_file.name if hasattr(video_file, "name") else video_file
    
    logs = "=== পাইপলাইন প্রসেসিং শুরু হয়েছে ===\n"
    yield logs, "প্রসেসিং চলছে..."
    
    # Step 01 (Demucs) ফাইল পাথ চেক করে রান করা
    step01_path = os.path.join("tools", "step01_demucs.py")
    if not os.path.exists(step01_path):
        yield f"❌ এরর: {step01_path} ফাইলটি পাওয়া যায়নি!", "রিপোর্ট পাওয়া যায়নি।"
        return
    
    logs += f"▶️ Step 01 (Demucs) রান করা হচ্ছে...\n"
    yield logs, "প্রসেসিং চলছে..."
    
    # পাইথন কোডের ভেতর থেকে Demucs ফাংশনটি কল করার জন্য ইম্পোর্ট করা
    sys.path.append(os.path.abspath("tools"))
    try:
        from step01_demucs import run_demucs_pipeline
        music_path, vocal_path = run_demucs_pipeline(video_path)
        logs += f"✅ Step 01 সফল!\n- BGM: {music_path}\n- Vocal: {vocal_path}\n\n"
        yield logs, "প্রসেসিং চলছে..."
    except Exception as e:
        import traceback
        error_msg = logs + f"❌ Step 01 এ ত্রুটি:\n{traceback.format_exc()}"
        yield error_msg, "রিপোর্ট পাওয়া যায়নি।"
        return
    
    # Step 02 (Whisper & Diarization) রান করা (Live Popen Stream সহ)
    logs += f"▶️ Step 02 (Whisper & Diarization) শুরু হচ্ছে...\n"
    yield logs, "প্রসেসিং চলছে..."
    
    step02_path = os.path.join("tools", "step02_whisper.py")
    
    if os.path.exists(step02_path):
        try:
            # -u ফ্লাগ ব্যবহার করা হয়েছে যাতে পাইথন কোনো বাফারিং না করে
            process = subprocess.Popen(
                [sys.executable, "-u", step02_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # লাইভ আউটপুট রিড করে Gradio লগে যোগ করা
            for line in process.stdout:
                print(line, end="") # কোলাব কনসোলেও দেখাবে
                logs += line
                yield logs, "প্রসেসিং চলছে..."
                
            process.wait()
            
            if process.returncode == 0:
                logs += "\n✅ Step 02 সফলভাবে শেষ হয়েছে!\n\n"
            else:
                logs += f"\n❌ Step 02 এ কোনো ত্রুটি হয়েছে (Exit code: {process.returncode})\n"
                
        except Exception as e:
            logs += f"\n❌ Step 02 সাবপ্রসেস ত্রুটি: {str(e)}\n"
    else:
        logs += f"❌ এরর: {step02_path} ফাইলটি পাওয়া যায়নি!\n"
        
    yield logs, "প্রসেসিং চলছে..."

    # রিপোর্ট ফাইলের পাথ খোঁজা
    result_dir = os.path.join("output_dubbing", "transcription_speakers")
    report_content = "রিপোর্ট ফাইল পাওয়া যায়নি।"
    
    if os.path.exists(result_dir):
        reports = [os.path.join(result_dir, f) for f in os.listdir(result_dir) if f.endswith(".txt")]
        if reports:
            latest_report = max(reports, key=os.path.getmtime)
            logs += f"\n📄 ফাইনাল রিপোর্ট ফাইল: {latest_report}\n"
            with open(latest_report, "r", encoding="utf-8") as rf:
                report_content = rf.read()
                
    yield logs, report_content

# Gradio Interface ডিজাইন (yield ব্যবহার করার জন্য `outputs` এ লাইভ আপডেট সাপোর্ট করবে)
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 Ultimate Movie Dubbing & Diarization Pipeline")
    gr.Markdown("ভিডিও আপলোড করুন এবং Demucs দিয়ে ভোকাল আলাদা করে স্বয়ংক্রিয়ভাবে Whisper ও Diarization রিপোর্ট তৈরি করুন।")
    
    with gr.Row():
        with gr.Column():
            video_input = gr.File(label="ভিডিও ফাইল আপলোড করুন (.mp4, .mkv ইত্যাদি)", file_types=[".mp4", ".mkv", ".avi", ".mov"])
            submit_btn = gr.Button("🚀 পাইপলাইন রান করুন", variant="primary")
            
        with gr.Column():
            output_logs = gr.Textbox(label="প্রসেসিং লাইভ লগ (Live Logs)", lines=15)
            
    with gr.Row():
        output_report = gr.Textbox(label="ডাবিং ও স্পিকার রিপোর্ট (Final Transcript Report)", lines=12)

    submit_btn.click(fn=process_movie_pipeline, inputs=video_input, outputs=[output_logs, output_report])

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
