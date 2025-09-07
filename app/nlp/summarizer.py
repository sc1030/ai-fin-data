# app/nlp/summarizer.py
# Tries transformer-based summarizer first; falls back to LexRank (sumy)
try:
    from transformers import pipeline
    _summ = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    def summarize_text(text, max_length=150, min_length=30):
        if not text or len(text.split()) < 30:
            return text
        out = _summ(text, max_length=max_length, min_length=min_length)
        return out[0]["summary_text"]
except Exception:
    # fallback: LexRank via sumy
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    def summarize_text(text, sentences_count=3):
        if not text:
            return ""
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(sentence) for sentence in summary)
