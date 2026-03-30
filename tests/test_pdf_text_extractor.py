from src.doc_extract import pdf_text_extractor

def test_ocr_works():
    assert len(pdf_text_extractor(r"input\test-ocr.pdf")) == 104
