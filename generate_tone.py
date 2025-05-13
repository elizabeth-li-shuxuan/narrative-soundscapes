#Elizabeth Li 5/13/2025
#generate tones based on the six dimensions
#valence only
from pyo import Server, Sine
from six_dimensions import analyze_text   # your sentiment analyzer
import numpy as np

# 1) Hard-coded text input
TEXT = (
    "I love sunny days, but sometimes I feel anxious when it's too bright. "
    "I just want to enjoy the weather without worrying about my skin."
)

# 2) Analyze only valence
features = analyze_text(TEXT)
valence = float(features['valence'])  # –1.0 … +1.0

# 3) Map valence to a pitch between C3 (130.8 Hz) and C6 (1046.5 Hz)
root_c3 = 130.81
root_c6 = 1046.50
freq = root_c3 + (valence + 1) / 2 * (root_c6 - root_c3)

# 4) Boot Pyo server (mono inputs off, stereo out)
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()

# 5) Play the valence-mapped tone continuously in left and right channels
left_channel = Sine(freq=freq, mul=0.2).out(chnl=0)
right_chanenl = Sine(freq=freq, mul=0.2).out(chnl=1)

# 6) Keep the GUI alive so you can hear it
print(f"Valence = {valence:.3f} → freq = {freq:.1f} Hz")
s.gui(locals())