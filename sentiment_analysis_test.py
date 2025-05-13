# Elizabeth Li 5/12/2025
# Test the sentiment analysis

from textblob import TextBlob

def test_textblob_sentiment():
    test_phrases = [
        "I love this product!",
        "I hate this service.",
        "It is okay, not good not bad.",
        "This is the worst experience ever.",
        "This is the best day of my life!"
    ]
    
    print("Testing TextBlob Sentiment Analysis:\n")
    for text in test_phrases:
        blob = TextBlob(text)
        print(f"Text: {text}")
        print(f"  Polarity: {blob.sentiment.polarity:.2f}  (-1.0 to +1.0)")
        print(f"  Subjectivity: {blob.sentiment.subjectivity:.2f}  (0.0 to 1.0)\n")

if __name__ == "__main__":
    test_textblob_sentiment()