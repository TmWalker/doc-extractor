import streamlit as st
from src.doc_extract import extract_details, validate_formats

st.set_page_config(page_title="Document Extractor", layout="wide")

st.title("📄 Document Extraction Tool")
st.write("Upload a PDF and extract key investor details.")

#Upload file
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file:
    st.success("PDF uploaded successfully.")

    # save file in temp location
    temp_path = "uploaded.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    # press button to extract details
    if st.button("Extract Details"):
        with st.spinner("Extracting details..."):
            extracted = extract_details(temp_path)

        st.subheader("Extracted Details")
        st.json(extracted)



        format_log = validate_formats(extracted)
        st.subheader("Validation Log")
        st.write("Where True/False/Null reflect correct/incorrect/Null of expected extracted details format")

        st.json(format_log)