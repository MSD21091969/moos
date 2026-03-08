import sys
import PyPDF2

def extract_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"Error reading PDF: {e}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_pdf.py <path_to_pdf>")
    else:
        print(extract_text(sys.argv[1]))
