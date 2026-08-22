import pdfplumber
with pdfplumber.open('KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf') as pdf:
    print(pdf.pages[0].extract_text()[:4000])
