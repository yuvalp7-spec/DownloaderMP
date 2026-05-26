import streamlit as st
import os
import requests
import subprocess
import shutil

# הגדרות עיצוב דף
st.set_page_config(page_title="Advanced Downloader 5.0", page_icon="🎬", layout="centered")

st.title("🎬 Advanced Downloader 5.0")
st.write("מנוע עוקף חסימות קבוע (Invidious Proxy). הדבק קישור, חתוך והורד בבטחה!")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# בחירת פורמט הורדה ראשי
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

# בחירת איכות הורדה
if format_type == "וידאו (MP4)":
    quality = st.selectbox("📺 בחר איכות וידאו:", ["720p (HD)", "360p (Medium)"])
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

def extract_video_id(url_str):
    # חילוץ מזהה הסרטון מכל סוגי הקישורים (רגיל, שורטס, שיתוף)
    if "youtu.be/" in url_str:
        return url_str.split("youtu.be/")[1].split("?")[0].split("/")[0]
    elif "shorts/" in url_str:
        return url_str.split("shorts/")[1].split("?")[0].split("/")[0]
    elif "v=" in url_str:
        return url_str.split("v=")[1].split("&")[0]
    elif "embed/" in url_str:
        return url_str.split("embed/")[1].split("?")[0]
    return None

if url:
    if st.button("🚀 מעבד את הסרטון - לחץ כאן"):
        with st.spinner("מושך את הסרטון דרך צינור מאובטח ומעבד..."):
            temp_dir = "temp_process"
            final_output = None
            try:
                os.makedirs(temp_dir, exist_ok=True)
                ext = "mp4" if format_type == "וידאו (MP4)" else "mp3"
                downloaded_file = os.path.join(temp_dir, f"raw_input.{ext}")
                
                video_id = extract_video_id(url)
                if not video_id:
                    raise Exception("לא מצליח לזהות את מזהה הסרטון מהקישור שהזנת.")
                
                # פנייה לשרת מתווך פתוח ויציב שיוטיוב לא חוסמת
                invidious_instance = "https://invidious.nerdvpn.de"
                api_url = f"{invidious_instance}/api/v1/videos/{video_id}"
                
                res = requests.get(api_url, timeout=15)
                video_info = res.json()
                
                # חילוץ הקישור הישיר לקובץ הוידאו/אודיו מתוך השרת
                format_streams = video_info.get("formatStreams", [])
                adaptive_streams = video_info.get("adaptiveStreams", [])
                
                stream_url = None
                
                if ext == "mp3":
                    # מחפש קובץ אודיו בלבד
                    audio_streams = [s for s in adaptive_streams if "audio/" in s.get("type", "")]
                    if audio_streams:
                        stream_url = audio_streams[0].get("url")
                else:
                    # מחפש וידאו משולב עם אודיו (בדרך כלל 720p או 360p בקובצי MP4 מוכנים)
                    if "720p" in quality:
                        hd_streams = [s for s in format_streams if s.get("qualityLabel") == "720p"]
                        if hd_streams: stream_url = hd_streams[0].get("url")
                    
                    if not stream_url: # ברירת מחדל או אם לא נמצא 720p
                        if format_streams:
                            stream_url = format_streams[0].get("url")
                
                if not stream_url:
                    raise Exception("השרת המתווך עמוס כרגע, נסה שוב בעוד כמה רגעים.")
                
                # אם הקישור הוא יחסי, מוסיפים את כתובת השרת
                if stream_url.startswith("/"):
                    stream_url = invidious_instance + stream_url
                
                # הורדת הקובץ לשרת Streamlit שלנו
                file_res = requests.get(stream_url, stream=True, timeout=30)
                with open(downloaded_file, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                
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
                
                # הצגת כפתור הורדה
                with open(final_output, "rb") as f:
                    st.success("✨ העיבוד הסתיים בהצלחה!")
                    st.download_button(
                        label="📥 לחץ כאן להורדת הקובץ למכשיר",
                        data=f,
                        file_name=f"Downloader_{video_info.get('title', 'video')[:15]}.{ext}",
                        mime=f"video/mp4" if ext == "mp4" else "audio/mpeg"
                    )
                
            except Exception as e:
                st.error(f"❌ אירעה שגיאה בעיבוד: {str(e)[:150]}")
            
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if final_output and os.path.exists(final_output):
                    os.remove(final_output)
