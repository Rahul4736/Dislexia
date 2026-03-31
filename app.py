import streamlit as st
import fitz
from gtts import gTTS
import speech_recognition as sr
import tempfile
import google.generativeai as genai
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
genai.configure(api_key="API Key Here")  # 🔥 PUT YOUR API KEY HERE
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Dyslexia AI", layout="wide")

st.title("🧠 Dyslexia AI Assistant")
st.markdown("### 🌍 AI-Powered • Multilingual • Dyslexia-Friendly")

# ---------------- LANGUAGE MAP ----------------
language_map = {
    "English": "en","Hindi": "hi","Konkani": "gom","Kannada": "kn","Dogri": "doi",
    "Bodo": "brx","Urdu": "ur","Tamil": "ta","Kashmiri": "ks","Assamese": "as",
    "Bengali": "bn","Marathi": "mr","Sindhi": "sd","Maithili": "mai",
    "Punjabi": "pa","Malayalam": "ml","Manipuri": "mni","Telugu": "te",
    "Sanskrit": "sa","Nepali": "ne","Santali": "sat","Gujarati": "gu","Odia": "or"
}

# ---------------- PDF ----------------
def extract_pdf(file):
    try:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "".join([p.get_text() for p in doc])
    except:
        return "❌ Error reading PDF"

# ---------------- AUDIO INPUT ----------------
def audio_to_text(file):
    r = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        path = tmp.name

    with sr.AudioFile(path) as src:
        audio = r.record(src)

    try:
        return r.recognize_google(audio)
    except:
        return "❌ Audio not clear"

# ---------------- FALLBACK ----------------
def fallback_process(text, lang_name):
    try:
        return GoogleTranslator(source='auto', target=language_map[lang_name]).translate(text)
    except:
        return text

# ---------------- GEMINI PROCESS ----------------
def ai_process(text, lang_name):

    prompt = f"""
    Translate the following text into {lang_name}.

    Then make it dyslexia-friendly:
    - Keep paragraph structure
    - Break ONLY complex words
    - Use spacing like: im po ssi ble
    - Do NOT break small words
    - Maintain natural readability
    - Keep output in {lang_name}
    - Read out slow

    Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)

        if response and hasattr(response, "text"):
            return response.text
        else:
            return fallback_process(text, lang_name)

    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return fallback_process(text, lang_name)

# ---------------- AUDIO PREP ----------------
def prepare_audio_text(text):
    text = text.replace(".", ". ... ")
    text = text.replace(",", ", ... ")
    text = text.replace("  ", " ... ")
    return text

# ---------------- TTS ----------------
def generate_audio(text, lang_code):

    text = prepare_audio_text(text)

    chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
    files = []

    for i, chunk in enumerate(chunks):
        try:
            tts = gTTS(chunk, lang=lang_code)
            filename = f"audio_{i}.mp3"
            tts.save(filename)
            files.append(filename)
        except:
            continue

    return files

# ---------------- PROCESS ----------------
def process(text, lang_name):
    return ai_process(text, lang_name)

# ---------------- UI ----------------
col1, col2 = st.columns(2)

with col1:
    input_type = st.radio("📥 Input Type", ["PDF", "Audio"])
    file = st.file_uploader("Upload File", type=["pdf", "wav"])
    lang_name = st.selectbox("🌍 Output Language", list(language_map.keys()))
    run = st.button("🚀 Process")

with col2:
    if file and run:
        with st.spinner("⚡ Processing with AI..."):

            # Extract text
            if input_type == "PDF":
                text = extract_pdf(file)
            else:
                text = audio_to_text(file)

            st.subheader("📄 Extracted Text")
            st.text_area("Text", text, height=250)

            # AI Output
            output = process(text, lang_name)

            st.subheader("🧠 Output (Paragraph Wise)")
            paragraphs = output.split("\n")

            for p in paragraphs:
                if p.strip():
                    st.markdown(
                        f"<div style='font-size:18px; line-height:1.8;'>{p}</div>",
                        unsafe_allow_html=True
                    )

            # Audio Output
            lang_code = language_map[lang_name]
            audio_files = generate_audio(output, lang_code)

            st.subheader("🔊 Audio Output")
            for f in audio_files:
                st.audio(f)

    else:
        st.info("Upload file and click Process")
