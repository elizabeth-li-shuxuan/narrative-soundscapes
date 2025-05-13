#!/usr/bin/env python3
# simple_pyo_test.py

from pyo import Server, Sine

# 1) Boot the server (no inputs, stereo output)
s = Server(duplex=False, nchnls=2, sr=44100, audio='portaudio').boot()
s.start()

# 2) Play a continuous 440 Hz tone at half‐volume
left_channel = Sine(freq=440, mul=0.2).out(chnl = 0) 
right_channel = Sine(freq=440, mul=0.2).out(chnl = 1) 

# 4) Keep the GUI alive so you can hear it.
s.gui(locals())
