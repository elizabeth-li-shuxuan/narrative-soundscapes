#Elizabeth Li 5/13/2025
#generate tones based on the six dimensions

from pyo import Server, Pattern, Sine, Adsr, Freeverb, ButLP, pa_list_devices
import random
from six_dimensions import analyze_text
import numpy as np

def run_text_to_sound_loop(text: str):
    # 1) Analyze text to extract features
    features = analyze_text(text)
    features = {k: float(v) if isinstance(v, np.generic) else v
            for k,v in features.items()}
    
    # 2) Define scale (major vs. minor) based on valence
    root_freq = 261.63  # Middle C (C4)
    major_intervals = [0, 2, 4, 5, 7, 9, 11]
    minor_intervals = [0, 2, 3, 5, 7, 8, 10]
    scale_intervals = major_intervals if features['valence'] >= 0 else minor_intervals
    scale_freqs = [root_freq * (2 ** (i / 12)) for i in scale_intervals]
    
    # 3) Map arousal → tempo, steps per loop
    bpm = 60 + features['arousal'] * (180 - 60)  # 60–180 BPM
    steps = int(4 + features['density'] * 12)  # between 4 and 16 steps
    step_duration = (60.0 / bpm) * (4.0 / steps)  # duration of each step
    
    # 4) Map dominance → amplitude
    amp = 0.2 + features['dominance'] * 0.8  # 0.2–1.0
    
    # 5) Map subjectivity → reverb wetness
    rev_wet = features['subjectivity']  # 0.0–1.0
    
    # 6) Map variation → modulation depth
    mod_depth = features['variation'] * 100  # ±Hz deviation
    
    # 7) Initialize audio server
    s = Server().boot()
    s.start()
    
    # 8) Define callback to play each step
    def play_step():
        print("play_step() fired")
        base_freq = random.choice(scale_freqs)
        # Apply small random pitch modulation based on variation
        freq = base_freq + random.uniform(-mod_depth, mod_depth)
        
        # Envelope: attack based on arousal
        env = Adsr(
            attack=features['arousal'] * 0.1,
            decay=0.05, sustain=0.7, release=0.1,
            dur=step_duration, mul=amp
        ).play()
        
        # Sine oscillator
        osc = Sine(freq=freq, mul=env)
        
        # Low-pass filter with cutoff modulated by variation
        cutoff = 500 + mod_depth * 5
        filt = ButLP(osc, freq=cutoff)
        
        # Reverb effect based on subjectivity
        Freeverb(filt, size=0.8, damp=0.5, bal=rev_wet).out()
    
    # 9) Create a looping pattern
    loop = Pattern(play_step, time=float(step_duration))
    loop.play()
    
    # 10) Launch GUI to keep audio running
    s.gui(locals())

if __name__ == "__main__":
    user_text = input("Enter your text: ")
    run_text_to_sound_loop(user_text)
