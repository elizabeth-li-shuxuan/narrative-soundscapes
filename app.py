#Elizabeth Li 5/28/2025
# sentiment analysis and sonification + UI

import tkinter as tk
from tkinter import scrolledtext
from pyo import Server, Sine, Adsr, Pattern
from six_dimensions import analyze_text
import random

# Configuration constants
CHORD_VOL_MIN, CHORD_VOL_MAX = 0.01, 0.4
NOTES_VOL_MIN, NOTES_VOL_MAX = 1.0, 3.0
INTERVAL_MIN, INTERVAL_MAX = 0.5, 4.0
TEMPO_JITTER = 0.1
ROOT_C4 = 261.63

# Mapping functions
def map_valence(valence):
    intervals = [0,4,7] if valence >= 0 else [0,3,7]
    root_freq = ROOT_C4 * (2 ** valence)
    return [root_freq * (2 ** (i/12)) for i in intervals]

def map_variation(variation):
    chord_vol = CHORD_VOL_MAX - variation * (CHORD_VOL_MAX - CHORD_VOL_MIN)
    note_vol  = NOTES_VOL_MIN + variation * (NOTES_VOL_MAX - NOTES_VOL_MIN)
    return chord_vol, note_vol

def map_arousal(arousal_norm):
    return INTERVAL_MAX - arousal_norm * (INTERVAL_MAX - INTERVAL_MIN)

note_index = [0]
def map_dominance(dominance_norm, chord):
    if random.random() < dominance_norm:
        note_index[0] = (note_index[0] + 1) % len(chord)
        return chord[note_index[0]]
    else:
        return random.choice(chord)

def map_subjectivity(subjectivity, min_release=0.1, max_release=1.0):
    return min_release + subjectivity * (max_release - min_release)

class EmotionMusicApp:
    def __init__(self, master):
        self.master = master
        master.title("Emotion-to-Music")

        font = ("Avenir Next", 18)

        # Text input
        tk.Label(master, text="Input Text:", font=font).grid(row=0, column=0, sticky="w")
        self.text_entry = tk.Text(master, height=12, width=80, font=font)
        self.text_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.text_entry.insert("1.0", "This course will focus on practices of embodiment, listening, and sensing vibration. Our own bodies and voices, individual and collective, will be our primary sites of research and learning. The sonic practices we will do together are rooted in non-western, primarily South Asian traditions and philosophies of the voice and body, which, with my guidance, we will bring into a contemporary, living, and experimental shared space of inquiry and possibility.")

        # Run button
        self.run_button = tk.Button(master, text="Play & Analyze", font=font, command=self.run_analysis)
        self.run_button.grid(row=2, column=0, pady=5)

        # Output console
        tk.Label(master, text="Analysis Output:", font=font).grid(row=3, column=0, sticky="w")
        self.output_console = scrolledtext.ScrolledText(master, height=12, width=80, font=font, state="disabled")
        self.output_console.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # Set up Pyo server
        self.server = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
        self.server.start()
        self.pattern = None

    def log(self, message):
        self.output_console.config(state="normal")
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state="disabled")
 
    def run_analysis(self):
        # Clear previous output
        self.output_console.config(state="normal")
        self.output_console.delete("1.0", tk.END)
        self.output_console.config(state="disabled")

        # Stop any existing pattern
        if self.pattern:
            self.pattern.stop()

        # Analyze text
        text = self.text_entry.get("1.0", tk.END).strip()
        features = analyze_text(text)

        # 1) Clamp raw features to their true ranges
        valence      = max(-1.0, min(features['valence'],    1.0))
        arousal_raw  = max(-1.0, min(features['arousal'],    1.0))
        dominance_raw= max(-1.0, min(features['dominance'],  1.0))
        subjectivity = max(0.0,  min(features['subjectivity'], 1.0))
        variation    = max(0.0,  min(features['variation'],    1.0))

        # 2) Normalize arousal & dominance into [0,1] for your mappers
        arousal_norm   = (arousal_raw   + 1) / 2
        dominance_norm = (dominance_raw + 1) / 2

        # Map to musical parameters
        chord       = map_valence(valence)
        #chord_vol, note_vol = map_variation(variation)
        chord_vol, note_vol = 0.02,3.9
        tempo       = map_arousal(arousal_norm)
        release     = map_subjectivity(subjectivity)
        attack      = 0.005 + subjectivity * (0.05 - 0.005)
        decay       = 0.05  + subjectivity * (0.5  - 0.05)
        sustain     = 0.2   + subjectivity * (0.8  - 0.2)
        dur         = release + 1

        # background chord
        if hasattr(self, 'background'):
            for src in self.background:
                src.stop()
        self.background = []
        for note in chord:
            self.background.append(Sine(freq=note, mul=chord_vol).out(chnl=0))
            self.background.append(Sine(freq=note, mul=chord_vol).out(chnl=1))

        # Log results
        freqs_str = ", ".join(f"{freq:.0f}" for freq in chord)
        self.log(f"Valence (–1 to 1) = {valence:.2f}, Chord frequencies = [{freqs_str}]")
        self.log(f"Arousal (-1 to 1): {arousal_raw:.2f}, Tempo: {tempo:.2f}")
        self.log(f"Dominance (-1 to 1):  {dominance_raw:.2f}")
        self.log(f"Variation (0 to 1): {variation:.2f}, Background chord volume: {chord_vol:.2f}, Notes volume: {note_vol:.2f}")
        self.log(f"Subjectivity (0 to 1): {subjectivity:.2f}, Attack = {attack:.3f}, Decay = {decay:.3f}, Sustain = {sustain:.2f}, Release = {release:.2f}")

        # Play melody
        left_melody = []
        right_melody = []

        def play_note():
            freq = map_dominance(dominance_norm, chord)
            env = Adsr(
                attack=attack, decay=decay, sustain=sustain,
                release=release, dur=dur, mul=note_vol
            )
            env.play()
            left_melody.append(Sine(freq=freq, mul=env).out(chnl=0))
            right_melody.append(Sine(freq=freq, mul=env).out(chnl=1))
            if len(left_melody) > 50:
                old = left_melody.pop(0); old.stop()
                old = right_melody.pop(0); old.stop()

        self.pattern = Pattern(play_note, time=tempo).play()


if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionMusicApp(root)
    root.mainloop()
