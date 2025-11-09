"""Test the text cleaning function."""

from core.document_processor import clean_spaced_text

# Test cases
test_texts = [
    "B . S c  i n  I n f o r m a t i o n  S y s t e m s",
    "R o m  S h e y n i s",
    "This is normal text without spacing issues",
    "M L ,  C y b e r s e c u r i t y  &  N e t w o r k i n g"
]

for text in test_texts:
    cleaned = clean_spaced_text(text)
    print(f"Original: {text}")
    print(f"Cleaned:  {cleaned}")
    print("-" * 60)
