#!/usr/bin/env python3
# generate_loop_pyo.py
# Elizabeth Li 5/13/2025
# Continuously loop a generative tone driven by six text dimensions.

from pyo import Server, Pattern, Sine, Freeverb, ButLP
import random
from six_dimensions import analyze_text  # your text-analysis module

def map_features(features):
    """
    Map the six sentiment dimensions onto audio parameters:
      - valence → pitch (Hz)
      - arousal → tempo (BPM) & volume
      - dominance → step duration factor
      - subjectivity → reverb wetness
      - sentiment_variation → modulation depth (Hz)
      - emotion_density → number of steps per loop
    Returns (scale_freqs, step_duration, amp, rev_wet, mod_depth, steps).
    """
    # 1) Base scale: C4 = 261.63Hz, major/minor decision by valence
    root = 261.63
    major = [0,2,4,5,7,9,11]
    minor = [0,2,3,5,7,8,10]
    ints = major if features['valence'] >= 0 else minor
    scale_freqs = [root * (2 ** (i/12)) for i in ints]
    
    # 2) Tempo & volume from arousal
    bpm = 60 + features['arousal'] * 100        # 60–160 BPM
    amp = 0.2 + features['arousal'] * 0.8       # 0.2–1.0 volume
    
    # 3) Steps per loop from emotion density
    steps = max(1, int(4 + features['emotion_density'] * 12))  # 4–16
    
    # 4) Step duration: one bar = 4 beats
    step_duration = (60.0 / bpm) * (4.0 / steps)
    
    # 5) Reverb wetness from subjectivity
    rev_wet = features['subjectivity']          # 0.0–1.0
    
    # 6) Modulation depth from variation
    mod_depth = features['sentiment_variation'] * 50  # ±0–50Hz
    
    return scale_freqs, step_duration, amp, rev_wet, mod_depth, steps

def run_text_to_sound_loop(text: str):
    # Extract features once
    features = analyze_text(text)
    freqs, dur, amp, rev, mod, steps = map_features(features)

    # Initialize Pyo server (no input, stereo output)
    s = Server(duplex=False, sr=44100, nchnls=2, audio='portaudio').boot()
    s.start()

    def play_step():
        # Pick a scale degree and apply modulation
        base = random.choice(freqs)
        freq = base + random.uniform(-mod, mod)
        # Sine oscillator
        osc = Sine(freq=freq, mul=amp)
        # Simple low-pass for warmth
        filt = ButLP(osc, freq=1000 + mod * 10)
        # Reverb for subjectivity
        revd = Freeverb(filt, size=0.8, damp=0.5, bal=rev)
        # Output to both channels
        revd.out(chnl=0)

    # Create and retain pattern so it's not garbage-collected
    loop = Pattern(play_step, time=float(dur)).play()

    # GUI keeps process alive
    s.gui(locals())

if __name__ == "__main__":
    user_text = input("I love sunny days, but sometimes I feel anxious when it's too bright.")
    run_text_to_sound_loop(user_text)
