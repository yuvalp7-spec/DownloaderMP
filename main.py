import streamlit as st
import urllib.parse

st.set_page_config(page_title="Hybrid Downloader 8.2", page_icon="🎬", layout="centered")

st.title("🎬 Hybrid Downloader 8.2")
st.write("מנוע היברידי: הממשק בענן, הביצוע החסין ישירות מהנייד שלך!")

# שדה קלט לקישור
url = st.text_input("הדבק את הקישור שלך כאן:", placeholder="https://...")

# בחירת פורמט הורדה ראשי
format_type = st.radio("🎵 בחר פורמט קובץ:", ["וידאו (MP4)", "סאונד בלבד (MP3)"])

# בחירת איכות
if format_type == "וידאו (MP4)":
    quality = st.selectbox("📺 בחר איכות וידאו:", ["720p", "1080p", "480p"])
else:
    quality = st.selectbox("🎧 בחר איכות סאונד:", ["Best Audio"])

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
    st.markdown("---")
    st.subheader("🚀 שלבי הפעלה מהירים לנייד (חסין חסימות):")
    
    ext = "mp4" if format_type == "וידאו (MP4)" else "mp3"
    
    # הגדרת פילטר מהירות לטרמינל
    filter_cmd = ""
    if speed_val != 1.0:
        if ext == "mp3":
            filter_cmd = f'-filter:a "atempo={speed_val}"'
        else:
            filter_cmd = f'-filter:v "setpts={1.0/speed_val}*PTS" -filter:a "atempo={speed_val}"'
            
    to_cmd = f"-to {end_time}" if end_time else ""
    quality_num = quality.replace("p", "")
    
    format_opt = f"best[height<={quality_num}][ext=mp4]/best" if ext == "mp4" else "bestaudio/best"
    
    # שימוש בנתיב המלא והמאולץ של ה-FFmpeg הפנימי של Pydroid 3 במובייל
    pydroid_ffmpeg = "/data/data/ru.iiec.pydroid3/files/aarch64-linux-android/bin/ffmpeg"
    
    # בניית הפקודה המשולבת המושלמת
    pydroid_command = f'yt-dlp -f "{format_opt}" "{url}" -o "raw_tmp.%(ext)s" && {pydroid_ffmpeg} -y -ss {start_time} {to_cmd} -i raw_tmp.* {filter_cmd} /storage/emulated/0/Download/Output_{speed_val}x.{ext} && rm raw_tmp.*'
    
    st.write("1. **העתק את פקודת ההרצה המוכנה עבור הטרמינל בטלפון:**")
    st.code(pydroid_command, language="bash")
    
    st.write("2. פתח את אפליקציית **Pydroid 3**, ככנס ל-**Terminal**, הדבק את השורה הזו ולחץ אנטר.")
    st.success("✨ הקובץ החתוך והמואץ יישמר אוטומטית ישירות בתיקיית ה-Download הרגילה של הטלפון שלך!")
    
