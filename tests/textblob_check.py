from textblob import TextBlob

def has_sentiment(word):
    return TextBlob(word).sentiment.polarity != 0.0

for w in ["ecstatic", "devastated", "love", "happy"]:
    print(w, TextBlob(w).sentiment.polarity)
