# Elizabeth Li 5/13/2025

from pyo import Server, Sine, Adsr, Pattern
from six_dimensions import analyze_text
import random

TEXT = "I'm ecstatic! I'm sad. I'm happy."

#1. configuration ─────────────────────────────────────────────────────────────────────────────
# variation - volume
CHORD_VOL_MIN, CHORD_VOL_MAX = 0.01, 0.5 
NOTES_VOL_MIN, NOTES_VOL_MAX = 0.2, 3.0
# arousal - tempo
INTERVAL_MIN, INTERVAL_MAX = 0.1, 1.0
TEMPO_JITTER = 0.1     # tempo: ±10% timing jitter

#base pitch for C4
ROOT_C4 = 261.63


#2. text analysis ─────────────────────────────────────────────────────────────────────────────
features  = analyze_text(TEXT)
valence   = float(features['valence'])
variation = float(features['variation'])
arousal   = float(features['arousal'])
dominance = float(features['dominance'])
subjectivity = float(features['subjectivity'])

# clamp everything except valence to valid ranges, just in case
variation = max(0.0, min(variation, 1.0))
arousal   = max(0.0, min(arousal,   1.0))
dominance = max(0.0, min(dominance, 1.0))
subjectivity = max(0.0, min(subjectivity, 1.0))


#3. Mapping ─────────────────────────────────────────────────────────────────────────────
# positive valence = major triad, negative valence = minor triad
def map_valence(valence):
    intervals = [0,4,7] if valence >= 0 else [0,3,7]
    root_freq = ROOT_C4 * (2 ** valence)
    return [root_freq * (2 ** (i/12)) for i in intervals]
chord = map_valence(valence) #chord is originally chord_freqs

# low variation = soft notes/strong chord, high variation = strong notes/soft chord
def map_variation(variation):
    chord_vol = CHORD_VOL_MAX - variation * (CHORD_VOL_MAX - CHORD_VOL_MIN)
    note_vol  = NOTES_VOL_MIN + variation * (NOTES_VOL_MAX - NOTES_VOL_MIN)
    return chord_vol, note_vol
chord_vol, note_vol = map_variation(variation)

# arousal = tempo
def map_arousal(arousal):
    return INTERVAL_MAX - arousal * (INTERVAL_MAX - INTERVAL_MIN)
tempo = map_arousal(arousal)

# dominance = the pitch of the next tone (how randomly its order is following the previous note)
note_index = [0]
def map_dominance(dominance, chord, note_index):
    if random.random() < dominance:
        note_index = (note_index[0] + 1) % len(chord)
        return chord[note_index[0]]
    else:
        return random.choice(chord)

#subjectivity = how long each note is played
def map_subjectivity(subjectivity, min_release=0.1, max_release=1.0):
    return min_release + subjectivity * (max_release - min_release)
subjectivity = map_subjectivity(subjectivity)
attack  = 0.005 + subjectivity * (0.05  - 0.005)
decay   = 0.05  + subjectivity * (0.5   - 0.05)
sustain = 0.2   + subjectivity * (0.8   - 0.2)
release = 0.05   + subjectivity * (1.0   - 0.05)
duration = release + 1


#4. Setup pyo ─────────────────────────────────────────────────────────────────────────────
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()



#5. background music 
left_background, right_background = [], []
for note in chord: #for 0 in [0,4,7]
    left_background.append(Sine(freq=note, mul=chord_vol).out(chnl=0) )
    right_background.append(Sine(freq=note, mul=chord_vol).out(chnl=1) )

#6. set "melody" notes
mel_idx     = [0]
left_melody  = []
right_melody = []

def play_melody():
    #pick the next note based on dominance
    freq = map_dominance(dominance, chord, note_index)
    
    # Trigger envelope
    #env = Adsr(release=release, mul=NOTE_VOL)
    env = Adsr(attack=attack, decay=decay, sustain=sustain, release=release, dur=duration, mul=note_vol)
    #env = Adsr(attack=0.01, decay=0.05, sustain=0.6, release=release, dur=duration, mul=NOTE_VOL)
    env.play()

    # Play melody
    left_melody.append(Sine(freq=freq, mul=env).out(chnl=0)  )
    right_melody.append(Sine(freq=freq, mul=env).out(chnl=1) )

    # limits list of notes to 50 to save memory
    if len(left_melody) > 50:
        left_melody.pop(0)
        right_melody.pop(0)

    # play the next note at a jittered tempo
    next_interval = tempo + random.uniform(-TEMPO_JITTER * tempo, TEMPO_JITTER * tempo)
    next_interval = max(INTERVAL_MIN, min(INTERVAL_MAX, next_interval))
    melody.time = next_interval

#7. Start melody
melody = Pattern(play_melody, time=tempo)
melody.play()

print(f"valence={valence:.2f}, chord={chord}")
print(f"variation={variation:.2f}, background chord volumne={chord_vol:.2f}, notes volume={note_vol:.2f}")
print(f"arousal={arousal:.2f}, tempo={tempo:.2f}")
print(f"dominance={dominance:.2f}")
print(f"subjectivity={subjectivity:.2f}")
print("Now playing")

# 8) Keep GUI alive
s.gui(locals())

