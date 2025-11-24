import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

nltk.download('punkt', quiet=True)  # Auto-download if not present


def summarize_resume(text: str, max_sentences: int = 5) -> str:
    """
    Lightweight summarizer using LexRank (Sumy).
    Produces 5 key sentences from the resume.
    Adjust max_sentences if needed.
    """
    if not text or len(text) < 100:
        return text  # Too short → send original

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()

        summary_sentences = summarizer(parser.document, max_sentences)
        summary = " ".join([str(sentence) for sentence in summary_sentences])

        return summary.strip()

    except Exception as e:
        # Fallback if something goes wrong
        return text[:4000]  # Safely send first part
