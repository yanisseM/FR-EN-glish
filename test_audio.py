import sounddevice as sd

print("Liste des périphériques audio :")
print(sd.query_devices())

print("\nEnregistrement en cours...")
duration = 3  # secondes
fs = 44100  # fréquence d'échantillonnage
audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()
print("Enregistrement terminé.")
