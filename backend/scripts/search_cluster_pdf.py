import pdfplumber

def search_programmes():
    pdf_path = 'KUCCPS PROGRAMMES PDF/DEGREE_CLUSTER_DOCUMENT_2025_03.pdf'
    targets = ["BACHELOR OF ARTS", "ACTUARIAL SCIENCE", "COMPUTER SCIENCE"]
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                for target in targets:
                    if target.upper() in text.upper():
                        print(f"'{target}' found on Page {i+1}")
                        # Print some context
                        idx = text.upper().find(target.upper())
                        print(f"Context: {text[max(0, idx-50):idx+100]}...")

if __name__ == "__main__":
    search_programmes()
