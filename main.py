import streamlit as st
import yt_dlp
import os
import subprocess
import shutil

# הגדרות עיצוב דף
st.set_page_config(page_title="Advanced Downloader 2.0", page_icon="🎬", layout="centered")

st.title("🎬 Advanced Downloader 2.0")
st.write("הדבק קישור מיוטיוב, טיקטוק או אינסטגרם, חתוך את הזמן והורד ישירות למכשיר!")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# שדות לבחירת זמן (חיתוך)
col1, col2 = st.columns(2)
with col1:
    start_time = st.text_input("⏱️ זמן התחלה:", value="00:00:00")
with col2:
    end_time = st.text_input("⏱️ זמן סיום (אופציונלי):", placeholder="עד סוף הסרטון")

# בחירת מהירות סרטון
speed = st.selectbox("🚀 מהירות ניגון:", ["Normal (1.0x)", "Slow Motion (0.5x)", "Fast (1.25x)", "Faster (1.5x)", "Double Speed (2.0x)"])
speed_val = float(speed.split("(")[1].replace("x)", ""))

# בחירת פורמט הורדה
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

if url:
    if st.button("🚀 מעבד את הסרטון - לחץ כאן"):
        with st.spinner("מוריד ומעבד את הסרטון בענן..."):
            try:
                temp_dir = "temp_process"
                os.makedirs(temp_dir, exist_ok=True)
                temp_raw = os.path.join(temp_dir, "raw.%(ext)s")
                
                # הגדרות הורדה
                ydl_opts = {'outtmpl': temp_raw, 'overwrites': True}
                if format_type == "סאונד בלבד (MP3)":
                    ydl_opts.update({'format': 'bestaudio'})
                    ext = "mp3"
                else:
                    ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
                    ext = "mp4"
                
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
                
                # שינוי מהירות אם נבחרה מהירות שונה מ-1
                if speed_val != 1.0:
                    if format_type == "סאונד בלבד (MP3)":
                        ffmpeg_cmd.extend(['-filter:a', f"atempo={speed_val}"])
                    else:
                        ffmpeg_cmd.extend(['-filter:v', f"setpts={1.0/speed_val}*PTS", '-filter:a', f"atempo={speed_val}"])
                
                ffmpeg_cmd.append(final_output)
                subprocess.run(ffmpeg_cmd, check=True)
                
                # הצגת כפתור הורדה ישיר למשתמש בטלפון!
                with open(final_output, "rb") as f:
                    st.success("הסרטון מוכן לחילוץ!")
                    st.download_button(
                        label="📥 לחץ כאן להורדת הקובץ למכשיר",
                        data=f,
                        file_name=f"Advanced_Downloader_{info['title'][:15]}.{ext}",
                        mime=f"video/{ext}" if ext == "mp4" else "audio/mpeg"
                    )
                
                # ניקוי זמני
                shutil.rmtree(temp_dir)
                if os.path.exists(final_output): os.remove(final_output)
                
            except Exception as e:
                st.error(f"אירעה שגיאה בעיבוד: {str(e)[:50]}")
