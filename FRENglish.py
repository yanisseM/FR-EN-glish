from huggingface_hub import InferenceClient
from google.cloud import texttospeech, speech
import os
import sounddevice as sd
import soundfile as sf
import pyaudio
import io
import wave
 
# LLM client setup (streaming LLM)
llm_client = InferenceClient(
    provider="nebius",
    api_key="eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnb29nbGUtb2F1dGgyfDExMTQ0OTE4MzIzNTI4NTQ0MjQ1MiIsInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIiwiaXNzIjoiYXBpX2tleV9pc3N1ZXIiLCJhdWQiOlsiaHR0cHM6Ly9uZWJpdXMtaW5mZXJlbmNlLmV1LmF1dGgwLmNvbS9hcGkvdjIvIl0sImV4cCI6MTkwMDE0MTQ0MiwidXVpZCI6ImQxNDM4NGNiLWY4M2YtNGM0ZS1iMTM0LTRjYzAyZWI3M2JjYyIsIm5hbWUiOiJVbm5hbWVkIGtleSIsImV4cGlyZXNfYXQiOiIyMDMwLTAzLTE5VDA5OjA0OjAyKzAwMDAifQ.vT6sRSfDAybzwT5tVU1zKIde6lRzuIf4vB4_9Z07h_0",
)
 
# Authentification GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"
 
# Setup client TTS
tts_client = texttospeech.TextToSpeechClient()
voice_params = texttospeech.VoiceSelectionParams(
    language_code='en-US',
    name='en-US-Wavenet-I',

    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
 
# Fonction de lecture audio WAV avec PyAudio
def play_audio(audio_bytes):
    with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
 
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
 
        stream.stop_stream()
        stream.close()
        p.terminate()
 
# Contexte initial
context = (
    "Tu es une IA patiente et bienveillante, spécialisée dans l'apprentissage de l'anglais pour des personnes francophones. "
    "Lorsque quelqu’un parle anglais, tu analyses la phrase, corriges les fautes et reformules la phrase proprement. Si la question laisse une réponse, répond de sorte à mettre en place une discussion"
    "Tu expliques simplement si nécessaire, mais tu réponds toujours uniquement en anglais corrigé. "
    "N’utilise pas de français dans ta réponse. Sois claire, concise et utile."
    "Si on t'insulte ou que l'on dis des choses grave, tu ne reponds pas et dis que ce n'est pas dans tes valeurs"
)
messages = [
    {"role": "system", "content": context}
]
 
while True:
    # 1. Enregistrement de la voix
    duration = 5  # secondes
    sample_rate = 44100
    print("🎤 Enregistrement...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    sf.write('voice.flac', audio_data, sample_rate)
    print("✅ Enregistrement terminé.")
 
    # 2. Transcription vocale avec Google STT
    speech_client = speech.SpeechClient()
    with open("voice.flac", "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(sample_rate_hertz=44100, language_code="en-US")
    result = speech_client.recognize(config=config, audio=audio)
 
    if len(result.results) == 0:
        print("⚠️ Aucune voix détectée.")
        continue
 
    user_input = result.results[0].alternatives[0].transcript
    print("👤 Elève :", user_input)
    messages.append({"role": "user", "content": user_input})
 
    # 3. Réponse en streaming du LLM + TTS phrase par phrase
    completion = llm_client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=messages,
        max_tokens=1512,
        stream=True,
        temperature=0.9
    )
 
    print("Rephrasio : ", end="", flush=True) 

    reponse = ""
    buffer = ""
 
    for chunk in completion:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            reponse += content
            buffer += content
 
            if any(p in buffer for p in [".", "!", "?", "\n"]):
                synthesis_input = texttospeech.SynthesisInput(text=buffer.strip())
                tts_response = tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )
                play_audio(tts_response.audio_content)
                buffer = ""
 
    print()
    print("✅ Correction complète :", reponse)
    messages.append({"role": "assistant", "content": reponse})

    with open("corrections.txt", "a", encoding="utf-8") as f:
        f.write(f"🎙 Élève : {user_input}\n")
        f.write(f"✅ Correction : {reponse}\n")
        f.write("-" * 40 + "\n")
