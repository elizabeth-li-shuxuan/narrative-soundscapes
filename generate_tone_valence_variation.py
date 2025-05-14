# Elizabeth Li 5/13/2025

from pyo import Server, Sine, Adsr, Pattern
from six_dimensions import analyze_text
import random


from pyo import Server, Sine, Adsr, Pattern
from six_dimensions import analyze_text
import random

# CHORD_VOL range (0.01–0.5): least shifting → highest chord vol; most shifting → lowest chord vol
CHORD_VOL_MIN = 0.01  # quietest chord volume
CHORD_VOL_MAX = 0.5   # loudest chord volume
# NOTES_VOL range (0.2–3): least shifting → lowest notes vol; most shifting → highest notes vol
NOTES_VOL_MIN = 0.2   # quietest melody volume
NOTES_VOL_MAX = 3.0   # loudest melody volume

# Very low variation (all uniformly positive → variation ≈ 0)
# Very high variation (polar opposite clauses → variation ≈ 1)
TEXT = (
    "I'm ecstatic! I'm sad."
)



# 2) Extract valence & variation
features   = analyze_text(TEXT)

valence    = float(features['valence'])

variation  = float(features['variation'])
variation  = max(0.0, min(variation, 1.0))
CHORD_VOL = CHORD_VOL_MAX - variation * (CHORD_VOL_MAX - CHORD_VOL_MIN)
NOTES_VOL = NOTES_VOL_MIN + variation * (NOTES_VOL_MAX - NOTES_VOL_MIN)

# 3) Build triad
intervals   = [0,4,7] if valence >= 0 else [0,3,7]
root_c4     = 261.63
root_freq   = root_c4 * (2 ** valence)
chord_freqs = [root_freq * (2 ** (i/12)) for i in intervals]

# 4) Boot Pyo
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()

# 5) Sustain chord: keep references in lists
left_channels, right_channels = [], []
for f in chord_freqs:
    left_channel  = Sine(freq=f, mul=CHORD_VOL).out(chnl=0)
    right_channel = Sine(freq=f, mul=CHORD_VOL).out(chnl=1)
    left_channels.append(left_channel)
    right_channels.append(right_channel)

# 6) Prepare melody state and storage
mel_idx = [0]
left_leads, right_leads = [], []

def play_melody():
    """Play one chord tone as an articulate lead (with ADSR) on both channels."""
    # Choose next freq deterministically or at random
    if random.random() < variation:
        mel_idx[0] = (mel_idx[0] + 1) % len(chord_freqs)
        freq = chord_freqs[mel_idx[0]]
    else:
        freq = random.choice(chord_freqs)
    # Create an envelope and trigger it
    env = Adsr(attack=0.01, decay=0.05, sustain=0.6, release=0.2,
               dur=0.3, mul=NOTES_VOL)
    env.play()
    # Explicit left/right lead voices and store them so they persist until release
    left_channel  = Sine(freq=freq, mul=env).out(chnl=0)
    right_channel = Sine(freq=freq, mul=env).out(chnl=1)
    left_leads.append(left_channel)
    right_leads.append(right_channel)
    # Optionally prune old leads to avoid unbounded growth
    if len(left_leads) > 50:
        left_leads.pop(0)
        right_leads.pop(0)

# 7) Schedule the melody every 0.5s
melody = Pattern(play_melody, time=0.5).play()

print(f"Valence={valence:.2f}, variation={variation:.2f}")
print("Now playing")

# 8) Keep the GUI alive
s.gui(locals())
