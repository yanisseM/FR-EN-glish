import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import wave
import os
import tempfile
import pyaudio
import sounddevice as sd
import soundfile as sf
from google.cloud import texttospeech, speech
from huggingface_hub import InferenceClient

# 🔐 Configurations d'accès aux API
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"  # Clé Google Cloud
llm_client = InferenceClient(
    model="HuggingFaceH4/zephyr-7b-beta",  
    token=""
)

# 🎤 Google Cloud TTS setup
tts_client = texttospeech.TextToSpeechClient()
voice_params = texttospeech.VoiceSelectionParams(
    language_code='en-US',
    name='en-US-Wavenet-I',
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

# 🎙️ Enregistrement vocal 5 secondes
def record_audio(filename="voice.wav", duration=5):
    samplerate = 44100
    data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    sf.write(filename, data, samplerate)

# 📃 Transcription de la voix en texte
def transcribe_audio(filename):
    client = speech.SpeechClient()
    with open(filename, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    transcripts = [result.alternatives[0].transcript for result in response.results]
    return " ".join(transcripts) if transcripts else ""

# 🤖 Correction du texte par IA
def correct_english(text):
    prompt = f"Correct this English sentence in a friendly tone: '{text}'"
    response = llm_client.text_generation(
        prompt=prompt,
        max_new_tokens=100
    )
    if isinstance(response, dict) and "generated_text" in response:
        return response["generated_text"]
    elif isinstance(response, list) and len(response) > 0 and "generated_text" in response[0]:
        return response[0]["generated_text"]
    else:
        return str(response)

# 🔊 Synthèse vocale
def speak_text(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config
    )
    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmpfile:
        tmpfile.write(response.audio_content)
        tmpfile.flush()
        wf = wave.open(tmpfile.name, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(wf.getnframes())
        stream.write(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()

# 🖼️ Interface graphique
class FRENglishGUI:
    def __init__(self, root):
        self.root = root
        root.title("FR-EN-glish - English Coach")
        root.geometry("600x450")
        root.configure(bg="#f7f7f7")

        try:
            import tkinter.ttk as ttk
            style = ttk.Style()
            style.theme_use('default')
        except Exception:
            pass

        tk.Label(root, text="FR-EN-glish", font=("Helvetica", 20, "bold"), fg="#d63031", bg="#f7f7f7").pack(pady=10)

        tk.Label(root, text="Phrase entendue :", font=("Helvetica", 12), bg="#f7f7f7").pack()
        self.text_original = scrolledtext.ScrolledText(root, height=4, width=65, font=("Helvetica", 10))
        self.text_original.pack(padx=20, pady=5)

        tk.Label(root, text="Correction :", font=("Helvetica", 12), bg="#f7f7f7").pack()
        self.text_corrected = scrolledtext.ScrolledText(root, height=4, width=65, font=("Helvetica", 10))
        self.text_corrected.pack(padx=20, pady=5)

        frame = tk.Frame(root, bg="#f7f7f7")
        frame.pack(pady=15)

        self.btn_record = tk.Button(frame, text="Parler (5 sec)", command=self.start_process, bg="#d63031", fg="white", font=("Helvetica", 12), width=20)
        self.btn_record.pack(side=tk.LEFT, padx=10)

        self.btn_speak = tk.Button(frame, text="Écouter la correction", command=self.speak_correction, font=("Helvetica", 12), width=25)
        self.btn_speak.pack(side=tk.LEFT, padx=10)

    def start_process(self):
        self.btn_record.config(state=tk.DISABLED)
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        self.text_original.delete('1.0', tk.END)
        self.text_corrected.delete('1.0', tk.END)
        try:
            record_audio()
            original = transcribe_audio("voice.wav")
            self.text_original.insert(tk.END, original)
            corrected = correct_english(original)
            self.text_corrected.insert(tk.END, corrected)

            with open("corrections.txt", "a", encoding="utf-8") as f:
                f.write(f"Élève : {original}\n")
                f.write(f"Correction : {corrected}\n")
                f.write("-" * 40 + "\n")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        finally:
            self.btn_record.config(state=tk.NORMAL)

    def speak_correction(self):
        corrected_text = self.text_corrected.get('1.0', tk.END).strip()
        if corrected_text:
            threading.Thread(target=speak_text, args=(corrected_text,), daemon=True).start()

if __name__ == '__main__':
    root = tk.Tk()
    app = FRENglishGUI(root)
    root.mainloop()
