#!/usr/bin/env python3
# continuous_valence_chord_pyo.py
# Elizabeth Li 5/13/2025
# Continuous, gap-free valence chord via pyo.

from pyo import Server, Sine
from six_dimensions import analyze_text   # your sentiment analyzer

# 1) Hardcoded text
TEXT = (
    "I love sunny days, but sometimes I feel anxious when it's too bright. "
)

# 2) Extract valence
features = analyze_text(TEXT)
valence = float(features['valence'])  # –1.0 … +1.0

# 3) Chord quality: major vs minor triad
intervals = [0, 4, 7] if valence >= 0 else [0, 3, 7]

# 4) Variable root: C4 ± 2 octaves by valence
root_c4 = 261.63
root_freq = root_c4 * (2 ** valence*2)  

# 5) Compute chord frequencies
chord_freqs = [root_freq * (2 ** (i / 12)) for i in intervals]

# 6) Boot pyo server (stereo out, no input)
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()

# 7) Instantiate and sustain voices on both channels
amp = 0.3
left_voices, right_voices = [], []
for f in chord_freqs:
    left_voices.append(Sine(freq=f, mul=amp).out(chnl=0) )
    right_voices.append(Sine(freq=f, mul=amp).out(chnl=1) )

print(f"Valence={valence:.2f} → root={root_freq:.1f}Hz → "
      f"{'major' if valence>=0 else 'minor'} triad (continuous)")

# 8) GUI loop holds the server alive with zero dropouts
s.gui(locals())