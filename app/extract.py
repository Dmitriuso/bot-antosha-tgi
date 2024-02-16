import re

from pdfminer.high_level import extract_text
from unicodedata import normalize

PDF_PATTERN = re.compile(r".pdf|.PDF")
TXT_PATTERN = re.compile(r".txt|.TXT")

BAD_PATTERNS = [re.compile(r"\n"), re.compile(r"\s{2,}")]

BAD_PUNCT = [
    (re.compile(r"\-\n"), ""),
    (re.compile(r"\n{2,}"), "\t")
]

def extract_normalize(path: str) -> str:
    if PDF_PATTERN.search(path):
        text = extract_text(path)
        for pu in BAD_PUNCT:
            text = pu[0].sub(pu[1], text)
        for p in BAD_PATTERNS:
            text = p.sub(" ", text)
        text = normalize("NFC", text)
        return text
    
    elif TXT_PATTERN.search(path):
        text = open(path).read()
        for pu in BAD_PUNCT:
            text = pu[0].sub(pu[1], text)
        for p in BAD_PATTERNS:
            text = p.sub(" ", text)
        text = normalize("NFC", text)
        return text
    
    else:
        return "Only .pdf and .txt files are admitted"