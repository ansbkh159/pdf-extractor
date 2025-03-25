import sys
from src.extractor import extract_pdf_content
from src.markdown import convert_to_markdown

def main(pdf_path, output_filename):
    content = extract_pdf_content(pdf_path)
    convert_to_markdown(content, output_filename)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <pdf_path> <output_filename>")
    else:
        main(sys.argv[1], sys.argv[2])
