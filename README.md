🇬🇧 FR-EN-glish — Apprendre l'anglais par la conversation IA - MOUNIB Yanisse - DURIMEL Terence
FR-EN-glish est un projet d’intelligence artificielle conçu pour vous aider à améliorer votre anglais oral en discutant en temps réel avec une IA.

🎯 Objectif
Permettre à toute personne souhaitant progresser en anglais de s'entraîner à l’oral via une conversation naturelle avec une intelligence artificielle basée sur des modèles Hugging Face et des services de Google Cloud.

🧠 Technologies utilisées
🧩 Langage & Frameworks :
Python 3.10+

Hugging Face Inference API (InferenceClient)

Google Cloud Text-to-Speech et Speech-to-Text

Twinker (interface graphique)

🗣 Bibliothèques Python :
python
Copier
Modifier
from huggingface_hub import InferenceClient
from google.cloud import texttospeech, speech
import os
import sounddevice as sd
import soundfile as sf
import pyaudio
import io
import wave
⚙️ Fonctionnalités
🎙️ Enregistrement de votre voix

☁️ Transcription via Google Cloud Speech-to-Text

💬 Envoi de votre question au modèle Hugging Face

🧠 Réponse générée par une IA conversationnelle

🔊 Restitution audio via Google Cloud Text-to-Speech

🖥 Interface interactive via Twinker
