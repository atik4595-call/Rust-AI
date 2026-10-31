# ==========================================
# Movie Dubbing Pipeline Web UI (Gradio)
# ==========================================
import os
import sys
import subprocess
import gradio as gr

print("🚀 Movie Dubbing Web UI চালু হচ্ছে...")

def process_movie_pipeline(video_file):
    if video_file is None:
        return "❌ দয়া করে একটি ভিডিও ফাইল আপলোড করুন!"
    
    video_path = video_file.name if hasattr(video_file, "name") else video_file
    
    logs = "=== পাইপলাইন প্রসেসিং শুরু হয়েছে ===\n"
    
    # Step 01 (Demucs) ফাইল পাথ চেক করে রান করা
    step01_path = os.path.join("tools", "step01_demucs.py")
    if not os.path.exists(step01_path):
        return f"❌ এরর: {step01_path} ফাইলটি পাওয়া যায়নি!"
    
    logs += f"▶️ Step 01 (Demucs) রান করা হচ্ছে...\n"
    
    # পাইথন কোডের ভেতর থেকে Demucs ফাংশনটি কল করার জন্য ইম্পোর্ট করা
    sys.path.append(os.path.abspath("tools"))
    try:
        from step01_demucs import run_demucs_pipeline
        music_path, vocal_path = run_demucs_pipeline(video_path)
        logs += f"✅ Step 01 সফল!\n- BGM: {music_path}\n- Vocal: {vocal_path}\n\n"
    except Exception as e:
        import traceback
        return logs + f"❌ Step 01 এ ত্রুটি:\n{traceback.format_exc()}"
    
    # Step 02 (Whisper & Diarization) রান করা
    logs += f"▶️ Step 02 (Whisper & Diarization) রান করা হচ্ছে...\n"
    step02_path = os.path.join("tools", "step02_whisper.py")
    
    if os.path.exists(step02_path):
        result = subprocess.run([sys.executable, step02_path], capture_output=True, text=True)
        if result.returncode == 0:
            logs += "✅ Step 02 সফলভাবে শেষ হয়েছে!\n\n"
            logs += result.stdout[-2000:] # শেষের আউটপুট লগ দেখাবে
        else:
            logs += f"❌ Step 02 ত্রুটি:\n{result.stderr}"
    else:
        logs += f"❌ এরর: {step02_path} ফাইলটি পাওয়া যায়নি!"
        
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
                
    return logs, report_content

# Gradio Interface ডিজাইন
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 Ultimate Movie Dubbing & Diarization Pipeline")
    gr.Markdown("ভিডিও আপলোড করুন এবং Demucs দিয়ে ভোকাল আলাদা করে স্বয়ংক্রিয়ভাবে Whisper ও Diarization রিপোর্ট তৈরি করুন।")
    
    with gr.Row():
        with gr.Column():
            video_input = gr.File(label="ট্রেস করার জন্য ভিডিও ফাইল আপলোড করুন (.mp4, .mkv ইত্যাদি)", file_types=[".mp4", ".mkv", ".avi", ".mov"])
            submit_btn = gr.Button("🚀 পাইপলাইন রান করুন", variant="primary")
            
        with gr.Column():
            output_logs = gr.Textbox(label="প্রসেসিং লগ (Logs)", lines=15)
            
    with gr.Row():
        output_report = gr.Textbox(label="ডাবিং ও স্পিকার রিপোর্ট (Final Transcript Report)", lines=12)

    submit_btn.click(fn=process_movie_pipeline, inputs=video_input, outputs=[output_logs, output_report])

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
