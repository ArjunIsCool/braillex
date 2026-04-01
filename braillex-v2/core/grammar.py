try:
    from textblob import TextBlob

    TEXTBLOB_OK = True
except ImportError:
    TEXTBLOB_OK = False


def correct_text(text):
    if not TEXTBLOB_OK:
        return text, "textblob not installed"
    try:
        blob = TextBlob(text)
        corrected = str(blob.correct())
        return corrected, None
    except Exception as e:
        return text, str(e)
