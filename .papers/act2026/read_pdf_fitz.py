import sys
import fitz  # PyMuPDF

def extract_text(pdf_path, out_path):
    try:
        doc = fitz.open(pdf_path)
        with open(out_path, "w", encoding="utf-8") as f:
            for page in doc:
                f.write(page.get_text() + "\n")
        print(f"Successfully extracted to {out_path}")
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python read_pdf_fitz.py <path_to_pdf> <out_path>")
    else:
        extract_text(sys.argv[1], sys.argv[2])
