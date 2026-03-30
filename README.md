# Document Extraction Pipeline

Extract structured data from a pdf document

Pipeline uses:
- Tesseract OCR (for scanned PDFs)
- Chunked LLM extraction with Ollama
- A Streamlit UI

### Install Guide

Install python dependencies
```
pip install -r requirements.txt
```

Download and install Ollama
https://ollama.com/download

Verify installation 
```
ollama --version
```

Download the model used in this program

'''
ollama pull mistral
'''