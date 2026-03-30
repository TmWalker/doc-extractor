import re
import subprocess
import json
from pathlib import Path
import configparser
import argparse

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import TesseractCliOcrOptions

#ocr engine path stored in config
config = configparser.ConfigParser()
config.read("config.cfg")


def pdf_text_extractor(source_path):
    """
    convert a pdf document to markdown and extract text from it

    Input path to pdf document
    Output markdown text as string
    """    

    #build conversion-ocr pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=True)
    pipeline_options.ocr_options = TesseractCliOcrOptions()
    pipeline_options.ocr_options.tesseract_cmd= config["ocr"]["run_path"]  


    #convert doc and extract teext
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    return doc_converter.convert(source_path).document.export_to_markdown()




def regex_pre_extract(text):
    """
    extract text matching email pattern from chunk

    Input chunk of text
    Output dictionary containing email if present and template Keys
    """
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

    return {
        'investor_email': email.group(0) if email else None, 
        'bank_account_name': None, 
        'bank_account_number': None, 
        'bank_sort_code': None, 
        'bank_name': None, 
        'commitment_amount': None,
        'commitment_currency': None
        }

    


def chunk_text(text, size= 8000):
    """
    chunk large body of text in to list of smaller chunks

    Input whole body of text as string
    Output list of chunks
    """
    return [text[i:i+size] for i in range(0, len(text), size)]


def build_prompt(chunk):
    """
    Add the Chunk text to the template prompt for LLM

    Input chunk text
    Output Prompt containing chunk as string
    """
    return f"""
You are an information extraction system.

Your ONLY task is to extract the following fields from the document:
- bank_account_name
- bank_account_number_or_iban
- bank_sort_code
- bank_name
- commitment_amount
- commitment_currency
- investor_email_address

Definitions:
- "bank_account_name": the exact name of the entity or Applicant that owns the bank account.
- "bank_account_number": an 8‑digit UK account number OR an IBAN (alphanumeric, often starting with a country code such as GB).
- "bank_sort_code": a 6‑digit UK sort code (XX‑XX‑XX) or 9-digit routing code (XXXXXXXXX) or swift code alphaneumeric (XXXXXXXX)
- "bank_name": is the name of the bank or financial institution where the account is held.
- "commitment_amount": the amount of the investor’s financial commitment. Provide the value to 0 decimal places, do not include characters. Ignore the currency.
- "commitment_currency": the currency of that commitment (e.g., GBP, USD, EUR).
- "investor_email": the email address of the investor. This will take the format x@x.x

STRICT RULES:
- Use ONLY information explicitly present in the document.
- Do NOT return information that is not present in the document
- Do NOT explain your reasoning.
- Do NOT add any fields.
- Do NOT guess or infer values.
- Output MUST be valid JSON only.
- Output MUST match the schema exactly.
- No commentary, no prose, no markdown.

Output schema (return exactly this structure):
{{
  "bank_account_name": string | null,
  "bank_account_number": string | null,
  "bank_sort_code": string | null,
  "bank_name": string | null,
  "commitment_amount": string | null,
  "commitment_currency": string | null,
  "investor_email": string | null
}}

Document:
{chunk}
"""



def llm_extract(model, prompt):
    """
    Run Ollama model via terminal

    Input model name and prompt as string
    Output LLM response as string
    """

    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    return result.stdout.decode("utf-8")

def merge_results(base, new):
    """
    Add values from a new dictionary in to an old dictionary where keys match and the new value is not empty

    Input old and new dictionary
    Output merged dictionary
    """
    for key, value in new.items():
        if base[key] is None and value not in (None, "null", ""):
            base[key] = value
    return base


def validate_formats(data):
    """
    Test final outputs again regex check to see if they are valid/expected outputs

    Input Dictionary of final outputs
    Output Dictionary containing results of format checks
    """

    patterns = {
        "investor_email": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", #email pattern
        "bank_account_name": r"^.+$",  # non-empty string
        "bank_account_number": r"^\d{8}$",  # 8 digits
        "bank_sort_code": r"^(?:\d{2}[- ]\d{2}[- ]\d{2}|\d{6})$",  # 12-34-56 or 123456
        "bank_name": r"^.+$",  # non-empty string
        "commitment_amount": r"^\d+$", #digits only
        "commitment_currency": r"^[A-Z]{3}$", #3 upper case letters
    }

    format_log = {}

    # If no value present, return None
    for key, value in data.items():
        if value is None:
            format_log[key] = None
            continue
        
        #True or False test on value matching pattern
        value_str = str(value).strip()
        pattern = patterns.get(key)
        format_log[key] = bool(re.fullmatch(pattern, value_str))

    return format_log

def extract_details(pdf_path, model="mistral"):
    """
    pipeline to extract details from a pdf document

    Input path to pdf document and ollama model
    Output dictionary of extracted details
    """

    # extract text from pdf
    md_text = pdf_text_extractor(pdf_path) 

    #extract deterministically any values
    final = regex_pre_extract(md_text)

    #chunk the full text
    chunks = chunk_text(md_text)

    #run LLM extraction on each chunk
    for chunk in chunks:
        prompt = build_prompt(chunk)
        raw = llm_extract(model, prompt)

        #if LLM result is not a JSON, skip the chunk
        #could add a retry or logger to note bad outputs
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue  # skip bad chunks

        # Step 4 — merge results
        final = merge_results(final, data)

    

    return final

def main():

    parser = argparse.ArgumentParser(
        description="Run extraction of details from subscription pdf"
    )

    parser.add_argument(
        "filepath",
        type=Path,
        help="Path to the input file"
    )

    args = parser.parse_args()

    md_path = args.filepath

    result = extract_details(md_path)
    print(result)
    #print(validate_formats(result))
    return result

if __name__ == "__main__":
    main()
    
