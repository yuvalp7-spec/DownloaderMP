import streamlit as st
import os
import requests
import subprocess
import shutil

# הגדרות עיצוב דף
st.set_page_config(page_title="Advanced Downloader 3.1", page_icon="🎬", layout="centered")

st.title("🎬 Advanced Downloader 3.1")
st.write("מנגנון עוקף חסימות מעודכן (v10 API). הדבק קישור, חתוך והורד בבטחה.")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# בחירת פורמט הורדה ראשי
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

# בחירת איכות
if format_type == "וידאו (MP4)":
    quality = st.selectbox("📺 בחר איכות וידאו:", ["1080p", "720p", "480p"])
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
        with st.spinner("מושך את הסרטון דרך הצינור החדש ומעבד..."):
            temp_dir = "temp_process"
            final_output = None
            try:
                os.makedirs(temp_dir, exist_ok=True)
                ext = "mp4" if format_type == "וידאו (MP4)" else "mp3"
                downloaded_file = os.path.join(temp_dir, f"raw_input.{ext}")
                
                # הכתובת הרשמית והמעודכנת של ה-API החדש שלהם
                api_url = "https://api.cobalt.tools/"
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                
                # הפורמט החדש של הגדרות ה-Payload
                payload = {
                    "url": url,
                    "videoQuality": quality.replace("p", "") if ext == "mp4" else "720",
                    "downloadMode": "audio" if ext == "mp3" else "auto"
                }
                
                response = requests.post(api_url, json=payload, headers=headers)
                res_data = response.json()
                
                # חילוץ הקישור לפי הפורמט החדש
                if res_data.get("status") == "error":
                    raise Exception(res_data.get("error", {}).get("text", "שגיאת שרת חיצוני"))
                
                file_download_url = res_data.get("url")
                
                if not file_download_url:
                    raise Exception("השרת לא החזיר קישור הורדה תקין. נסה שוב או בדוק את הקישור.")
                
                # הורדת הקובץ הזמני אל שרת ה-Streamlit שלנו
                file_res = requests.get(file_download_url, stream=True)
                with open(downloaded_file, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # נתיב לקובץ סופי
                final_output = f"final_media.{ext}"
                
                # פקודת FFmpeg לחיתוך ושינוי מהירות
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
                        file_name=f"Downloader_File.{ext}",
                        mime=f"video/mp4" if ext == "mp4" else "audio/mpeg"
                    )
                
            except Exception as e:
                st.error(f"❌ אירעה שגיאה בעיבוד: {str(e)[:150]}")
            
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if final_output and os.path.exists(final_output):
                    os.remove(final_output)
