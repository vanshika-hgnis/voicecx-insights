import sounddevice as sd, wave

duration = 5
samplerate = 16000
device = 1  # or set to your mic index

print(sd.query_devices())
audio = sd.rec(
    int(duration * samplerate),
    samplerate=samplerate,
    channels=1,
    dtype="int16",
    device=device,
)
sd.wait()
with wave.open("test.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio.tobytes())
print("Saved test.wav")
