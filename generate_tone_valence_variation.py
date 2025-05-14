# Elizabeth Li 5/13/2025

from pyo import Server, Sine, Adsr, Pattern
from six_dimensions import analyze_text
import random

# CHORD_VOL range (0.01–0.5): least shifting → highest chord vol; most shifting → lowest chord vol
CHORD_VOL_MIN = 0.01  # quietest chord volume
CHORD_VOL_MAX = 0.5   # loudest chord volume
# NOTES_VOL range (0.2–3): least shifting → lowest notes vol; most shifting → highest notes vol
NOTES_VOL_MIN = 0.2   # quietest melody volume
NOTES_VOL_MAX = 3.0   # loudest melody volume

# Tempo mapping
INTERVAL_MIN = 0.1   # fastest interval (high arousal), in seconds
INTERVAL_MAX = 1.0   # slowest interval (low arousal), in seconds
JITTER_PCT = 0.1     # ±10% timing jitter around the base interval

# Example text
TEXT = "I'm ecstatic! I'm sad."

# 1) Extract features
features  = analyze_text(TEXT)
valence   = float(features['valence'])
variation = float(features['variation'])
arousal   = float(features['arousal'])

# 2) Clamp features to [0,1]
variation = max(0.0, min(variation, 1.0))
arousal   = max(0.0, min(arousal,   1.0))

# 3) Map to audio parameters
CHORD_VOL = CHORD_VOL_MAX - variation * (CHORD_VOL_MAX - CHORD_VOL_MIN)
NOTES_VOL = NOTES_VOL_MIN + variation * (NOTES_VOL_MAX - NOTES_VOL_MIN)

# Build triad based on valence
intervals   = [0, 4, 7] if valence >= 0 else [0, 3, 7]
root_c4     = 261.63
root_freq   = root_c4 * (2 ** valence)
chord_freqs = [root_freq * (2 ** (i / 12)) for i in intervals]

# Map arousal to a base melody interval
melody_interval = INTERVAL_MAX - arousal * (INTERVAL_MAX - INTERVAL_MIN)

# 4) Boot Pyo server
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()

# 5) Sustain chord
left_channels, right_channels = [], []
for f in chord_freqs:
    left_channels.append( Sine(freq=f, mul=CHORD_VOL).out(chnl=0) )
    right_channels.append( Sine(freq=f, mul=CHORD_VOL).out(chnl=1) )

# 6) Prepare melody state
mel_idx     = [0]
left_leads  = []
right_leads = []

def play_melody():
    """Play one chord tone as a lead with ADSR and reschedule with jittered interval."""
    # Choose next freq
    if random.random() < variation:
        mel_idx[0] = (mel_idx[0] + 1) % len(chord_freqs)
        freq = chord_freqs[mel_idx[0]]
    else:
        freq = random.choice(chord_freqs)

    # Trigger envelope
    env = Adsr(attack=0.01, decay=0.05, sustain=0.6, release=0.2,
               dur=0.3, mul=NOTES_VOL)
    env.play()

    # Play lead on both channels
    left_leads.append(  Sine(freq=freq, mul=env).out(chnl=0)  )
    right_leads.append( Sine(freq=freq, mul=env).out(chnl=1) )

    # Prune old leads
    if len(left_leads) > 50:
        left_leads.pop(0)
        right_leads.pop(0)

    # Compute jittered interval for next call
    jitter        = random.uniform(-JITTER_PCT * melody_interval,
                                    JITTER_PCT * melody_interval)
    next_interval = melody_interval + jitter
    next_interval = max(INTERVAL_MIN,
                        min(INTERVAL_MAX, next_interval))
    # Reschedule Pattern
    melody.time = next_interval

# 7) Start the patterned melody
melody = Pattern(play_melody, time=melody_interval)
melody.play()

print(f"Valence={valence:.2f}, variation={variation:.2f}, "
      f"arousal={arousal:.2f}, interval≈{melody_interval:.2f}s "
      f"(±{JITTER_PCT * 100:.0f}% jitter)")
print("Now playing")

# 8) Keep GUI alive
s.gui(locals())
