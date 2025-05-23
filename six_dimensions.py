# Elizabeth Li 5/12/2025
# input text and get 
# six dimensions: valence, arousal, dominance, subjectivity, variation (how much sentiment shifts across clauses), density (proportion of explicitly emotional words in the text)

import csv
from textblob import TextBlob
import numpy as np
from nrclex import NRCLex
import re

lexicon = '/Users/elizabethli/Desktop/School/mus14/narrative-soundscapes/NRC-VAD-Lexicon-v2.1.csv'
input = "This course will focus on practices of embodiment, listening, and sensing vibration. Our own bodies and voices, individual and collective, will be our primary sites of research and learning. The sonic practices we will do together are rooted in non-western, primarily South Asian traditions and philosophies of the voice and body, which, with my guidance, we will bring into a contemporary, living, and experimental shared space of inquiry and possibility."

def load_vad_lexicon(filepath=lexicon):
    vad = {}
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row['term'].lower()
            vad[term] = {
                'valence': float(row['valence']),
                'arousal': float(row['arousal']),
                'dominance': float(row['dominance'])
            }
    return vad

# 2. Compute mean VAD for a text
def compute_vad(text, vad_lex):
    tokens = [w.strip('.,!?;:').lower() for w in text.split()]
    vs, ars, doms = [], [], []
    for t in tokens:
        if t in vad_lex:
            vs.append(vad_lex[t]['valence'])
            ars.append(vad_lex[t]['arousal'])
            doms.append(vad_lex[t]['dominance'])
    return {
        'valence': np.mean(vs) if vs else 0.0,
        'arousal': np.mean(ars) if ars else 0.0,
        'dominance': np.mean(doms) if doms else 0.0
    }

# 3. Subjectivity (TextBlob; polarity, subjectivity)
def compute_subjectivity(text):
    return TextBlob(text).sentiment.subjectivity


# 5. Sentiment variation across sentences
#all the ways to split sentences into clauses
CL_SPLIT = re.compile(
    r"""
    (?:[.?!]\s+)             |  # sentence end
    (?:[;:—-]\s+)            |  # semicolon, colon, dash
    (?:,\s+(?=and|but|or|so|because)) |  # comma + coordinating conj.
    \b(?:and|but|or|so|for|nor|yet|if|when|while|because|although|though|unless|since)\b |  # conjunctions
    \n+                         # line breaks
    """,
    re.IGNORECASE | re.VERBOSE
)

def split_clauses(text: str) -> list[str]:
    """Split text into clauses based on punctuation and conjunctions."""
    return [part.strip() for part in CL_SPLIT.split(text) if part.strip()]

def compute_sentiment_variation(text, vad_lex):
    clauses = split_clauses(text)
    clause_vals = []
    for clause in clauses:
        tokens = [w.strip('.,!?;:').lower() for w in clause.split()]
        vals = [vad_lex[t]['valence'] for t in tokens if t in vad_lex]
        clause_vals.append(np.mean(vals) if vals else 0.0)
    return float(np.std(clause_vals)) if len(clause_vals) > 1 else 0.0

# 6. Emotional lexical density (LIWC-style count of emotion words)
def compute_lexical_density(text):
    emo = NRCLex(text)
    total = len(text.split())
    emo_count = sum(emo.raw_emotion_scores.values())
    return emo_count / total if total else 0.0

# 7. Master analysis function
def analyze_text(text, vad_path=lexicon):
    vad_lex = load_vad_lexicon(vad_path)
    features = compute_vad(text, vad_lex)           # Valence, Arousal, Dominance
    features['subjectivity'] = compute_subjectivity(text)
    features['variation'] = compute_sentiment_variation(text, vad_lex)
    features['density'] = compute_lexical_density(text)

    features = {k: float(v) for k, v in features.items()} #remove the "np.float" outputs

    return features

if __name__ == "__main__":
    results = analyze_text(input)
    print(results)