# convert txt to csv

import pandas as pd

# 1) Read with whitespace (or specify sep='\t' if tabs)
df = pd.read_csv('/Users/elizabethli/Desktop/School/mus14/narrative-soundscapes/NRC-VAD-Lexicon-v2.1.txt',
                 sep='\s+',                # one-or-more spaces
                 header=None,
                 names=['word','valence','arousal','dominance'])

# 2) Save as CSV
df.to_csv('NRC-VAD-Lexicon.csv', index=False)