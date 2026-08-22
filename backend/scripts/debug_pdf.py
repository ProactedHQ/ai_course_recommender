import pdfplumber
with pdfplumber.open('KUCCPS PROGRAMMES PDF/DEGREE_PROGRAMMES_2025.pdf') as pdf:
    print(pdf.pages[0].extract_text()[:2000])
