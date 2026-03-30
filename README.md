# Document Extraction Pipeline

Extract structured data from a pdf document

Pipeline uses:
- Tesseract OCR (for scanned PDFs)
- Chunked LLM extraction with Ollama
- A Streamlit UI

### Install Guide


Install and activate requirements for this system
```
pip install -r requirements.txt
```

```
venv\Scripts\activate
```


Download and install Ollama
https://ollama.com/download

Verify installation 
```
ollama --version
```

Download the model used in this program

```'
ollama pull mistral
```

Install Tesseract OCR

https://github.com/UB-Mannheim/tesseract/wiki

Note the location of the install

Add the tesseract.exe file path to run_path in config.cfg

Verify Installation 

```
tesseract --version

### Run Guide

Details can be extracted from a pdf using the command

```
python -m src.doc_extract "path\to\file"  
```

Run the Streamlit app using

```
streamlit run app.py
```
This allows you to Upload a pdf and extract details

