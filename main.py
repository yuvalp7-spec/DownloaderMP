import streamlit as st
import yt_dlp
import os
import subprocess
import shutil

# הגדרות עיצוב דף
st.set_page_config(page_title="Advanced Downloader 4.0", page_icon="🎬", layout="centered")

st.title("🎬 Advanced Downloader 4.0")
st.write("גרסה עצמאית חסינת חסימות (iOS Engine). הדבק קישור, חתוך והורד ישירות למכשיר!")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# בחירת פורמט הורדה ראשי
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

# בחירת איכות הורדה
if format_type == "וידאו (MP4)":
    quality = st.selectbox("📺 בחר איכות וידאו:", [
        "הכי גבוהה שיש (Best Quality)",
        "1080p (Full HD)",
        "720p (HD)",
        "480p / 360p"
    ])
else:
    quality = st.selectbox("🎧 בחר איכות סאונד:", [
        "הכי גבוהה שיש (320kbps)",
        "סטנדרטית (192kbps)",
        "נמוכה (128kbps)"
    ])

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
        with st.spinner("מוריד ומעבד את הסרטון בצינור המאובטח..."):
            temp_dir = "temp_process"
            final_output = None
            try:
                os.makedirs(temp_dir, exist_ok=True)
                temp_raw = os.path.join(temp_dir, "raw.%(ext)s")
                
                # הגדרות התחזות מושלמות לאייפון/ספארי - עוקף את חסימות ה-403 לחלוטין
                ydl_opts = {
                    'outtmpl': temp_raw, 
                    'overwrites': True,
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'impersonate': 'safari-15.5', # התחזות ישירה לדפדפן אפל רשמי
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios'], # אילוץ שימוש בפרוטוקול iOS המאובטח
                        }
                    }
                }
                
                # התאמת פורמט ואיכות לפי בחירת המשתמש
                if format_type == "סאונד בלבד (MP3)":
                    ext = "mp3"
                    ydl_opts.update({'format': 'bestaudio/best'})
                else:
                    ext = "mp4"
                    if "1080p" in quality:
                        ydl_opts.update({'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'})
                    elif "720p" in quality:
                        ydl_opts.update({'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'})
                    elif "480p" in quality:
                        ydl_opts.update({'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'})
                    else:
                        ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'})
                
                # ביצוע ההורדה הישירה מהאייפון הווירטואלי לשרת שלנו
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    actual_ext = info.get('ext', ext)
                    downloaded_file = os.path.join(temp_dir, f"raw.{actual_ext}")
                
                # נתיב לקובץ סופי
                final_output = f"downloaded_media.{ext}"
                
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
                    st.success("✨ הסרטון עובד ועובד בהצלחה!")
                    
                    safe_title = "".join([c for c in info.get('title', 'media') if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                    safe_title = safe_title[:20] if safe_title else "media"
                    
                    st.download_button(
                        label="📥 לחץ כאן להורדת הקובץ למכשיר",
                        data=f,
                        file_name=f"{safe_title}.{ext}",
                        mime=f"video/mp4" if ext == "mp4" else "audio/mpeg"
                    )
                
            except Exception as e:
                st.error(f"❌ אירעה שגיאה בעיבוד: {str(e)[:150]}")
            
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if final_output and os.path.exists(final_output):
                    os.remove(final_output)
