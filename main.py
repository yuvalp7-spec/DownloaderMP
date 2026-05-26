import streamlit as st
import os
import requests
import subprocess
import shutil

# הגדרות עיצוב דף
st.set_page_config(page_title="Universal Downloader 7.0", page_icon="🎬", layout="centered")

st.title("🎬 Universal Downloader 7.0")
st.write("מנוע עוקף חסימות גלובלי פעיל! בחר איכות, מהירות וחיתוך זמן.")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# בחירת פורמט הורדה ראשי
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

# בחירת איכות
if format_type == "וידאו (MP4)":
    quality = st.selectbox("📺 בחר איכות וידאו:", ["720p (HD - מומלץ ויציב)", "1080p (Full HD)", "480p"])
else:
    quality = st.selectbox("🎧 בחר איכות סאונד:", ["Best Audio (MP3)"])

# שדות לבחירת זמן (חיתוך)
col1, col2 = st.columns(2)
with col1:
    start_time = st.text_input("⏱️ זמן התחלה (שעות:דקות:שניות):", value="00:00:00")
with col2:
    end_time = st.text_input("⏱️ זמן סיום (אופציונלי):", placeholder="עד סוף הסרטון")

# בחירת מהירות סרטון
speed = st.selectbox("🚀 מהירות ניגון:", ["Normal (1.0x)", "Slow Motion (0.5x)", "Fast (1.25x)", "Faster (1.5x)", "Double Speed (2.0x)"])
speed_val = float(speed.split("(")[1].replace("x)", ""))

if url:
    if st.button("🚀 מעבד את הסרטון - לחץ כאן"):
        with st.spinner("מושך את המדיה בצינור המאובטח ומעבד בענן..."):
            temp_dir = "temp_process"
            final_output = None
            try:
                os.makedirs(temp_dir, exist_ok=True)
                ext = "mp4" if format_type == "וידאו (MP4)" else "mp3"
                downloaded_file = os.path.join(temp_dir, f"raw_input.{ext}")
                
                # פנייה ל-API המעודכן והחסין של Publer
                api_url = "https://api.publer.io/v1/tools/media-downloader"
                payload = {"url": url}
                headers = {"Content-Type": "application/json"}
                
                res = requests.post(api_url, json=payload, headers=headers, timeout=20)
                res_data = res.json()
                
                # חילוץ הקישור הישיר לקובץ מתוך תגובת השרת
                payload_data = res_data.get("payload", {})
                job_url = None
                
                if ext == "mp3":
                    # ניסיון למשוך אודיו בלבד
                    audio_links = payload_data.get("audio", [])
                    if audio_links:
                        job_url = audio_links[0].get("url")
                
                # אם לא נמצא אודיו או שרצינו וידאו - ניקח מהווידאו
                if not job_url:
                    video_links = payload_data.get("video", [])
                    if video_links:
                        # מנסה למצוא את האיכות שנבחרה
                        matched_video = [v for v in video_links if quality.split("p")[0] in v.get("quality", "")]
                        if matched_video:
                            job_url = matched_video[0].get("url")
                        else:
                            job_url = video_links[0].get("url")
                            
                if not job_url and payload_data.get("url"):
                    job_url = payload_data.get("url")
                    
                if not job_url:
                    raise Exception("השרת לא הצליח לחלץ קישור ישיר למדיה. ודא שהקישור תקין.")
                
                # הורדת הקובץ הפיזי אל שרת ה-Streamlit שלנו
                file_res = requests.get(job_url, stream=True, timeout=30)
                with open(downloaded_file, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # נתיב לקובץ סופי
                final_output = f"final_media.{ext}"
                
                # פקודת FFmpeg לחיתוך ושינוי מהירות (עובד פצצה בענן של Streamlit בזכות ה-packages.txt)
                ffmpeg_cmd = ['ffmpeg', '-y']
                
                if start_time and start_time != "00:00:00":
                    ffmpeg_cmd.extend(['-ss', start_time])
                if end_time:
                    ffmpeg_cmd.extend(['-to', end_time])
                    
                ffmpeg_cmd.extend(['-i', downloaded_file])
                
                # שינוי מהירות
                if speed_val != 1.0:
                    if ext == "mp3":
                        ffmpeg_cmd.extend(['-filter:a', f"atempo={speed_val}"])
                    else:
                        ffmpeg_cmd.extend(['-filter:v', f"setpts={1.0/speed_val}*PTS", '-filter:a', f"atempo={speed_val}"])
                
                # קידוד וידאו תקני למובייל
                if ext == "mp4":
                    ffmpeg_cmd.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac'])
                
                ffmpeg_cmd.append(final_output)
                subprocess.run(ffmpeg_cmd, check=True)
                
                # הצגת כפתור הורדה למכשיר
                with open(final_output, "rb") as f:
                    st.success("✨ העיבוד הסתיים בהצלחה!")
                    st.download_button(
                        label="📥 לחץ כאן להורדת הקובץ למכשיר",
                        data=f,
                        file_name=f"Media_{quality}_{speed}x.{ext}",
                        mime=f"video/mp4" if ext == "mp4" else "audio/mpeg"
                    )
                
            except Exception as e:
                st.error(f"❌ אירעה שגיאה בעיבוד: {str(e)[:150]}")
            
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if final_output and os.path.exists(final_output):
                    os.remove(final_output)
                    
