import fitz
from .ocr_fallback import ocr_page
from .pdf_verification import compare_with_pdfplumber, verify_extraction_completeness

def extract_pdf_content(path):
    doc = fitz.open(path)
    extracted_text = ""
    images = []
    tables = {}
    per_page_text = {}
    per_page_images = {}
    per_page_tables = {}
    mismatched_pages = set()

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        
        table_objects = page.find_tables().tables
        table_bboxes = [table.bbox for table in table_objects]
        per_page_tables[page_num] = []
        
        for table in table_objects:
            table_data = {
                "bbox": table.bbox,
                "rows": table.extract(),
                "header": table.header.names if table.header else None
            }
            tables.setdefault(page_num, []).append(table_data)
            per_page_tables[page_num].append(table_data)
        
        text_dict = page.get_text("dict")
        page_text = ""
        
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                block_bbox = block["bbox"]
                in_table = any(fitz.Rect(block_bbox).intersects(fitz.Rect(tbl_bbox)) for tbl_bbox in table_bboxes)
                if not in_table:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            page_text += span.get("text", "") + " "
                        page_text += "\n"
        
        if not page_text.strip():
            page_text = page.get_text("text").strip()
            for table in per_page_tables[page_num]:
                for row in table["rows"]:
                    for cell in row:
                        if isinstance(cell, str):
                            page_text = page_text.replace(cell, "")
        
        per_page_text[page_num] = page_text.strip()
        extracted_text += page_text + "\n\n"
        
        image_list = page.get_images(full=True)
        per_page_images[page_num] = []
        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_info = {
                "page": page_num + 1,
                "xref": xref,
                "ext": base_image["ext"],
                "data": base_image["image"],
                "filename": f"image_page{page_num+1}_{xref}.{base_image['ext']}"
            }
            images.append(image_info)
            per_page_images[page_num].append(image_info)

    pdfplumber_mismatches = compare_with_pdfplumber(
        path, per_page_text, per_page_images, per_page_tables
        )
    
    mismatched_pages.update(pdfplumber_mismatches)

    pymupdf_mismatches = verify_extraction_completeness(
        doc, per_page_text, per_page_images, per_page_tables
    )
    mismatched_pages.update(pymupdf_mismatches)
    if mismatched_pages:
        for page_num in mismatched_pages:
            try:
                ocr_result = ocr_page(doc.load_page(page_num), doc)
                if ocr_result:
                    per_page_text[page_num] = ocr_result["text"]
                    per_page_tables[page_num] = ocr_result["tables"]
                    per_page_images[page_num] = ocr_result["images"]
                    extracted_text += ocr_result["text"] + "\n\n"
                    images.extend(ocr_result["images"])
                    tables[page_num] = ocr_result["tables"]
            except:
                continue
    
    return {
        "text": extracted_text.strip(),
        "tables": tables,
        "images": images,
        "per_page_text": per_page_text,
        "per_page_images": per_page_images,
        "per_page_tables": per_page_tables,
        "mismatched_pages": list(mismatched_pages)
    }

# if __name__ == "__main__":
#     content = extract_pdf_content("C:/Users/rachi/Desktop/remote part time test/pdf/cv-fr.pdf")
    
#     print("Extracted Text Preview:")
#     print(content["text"] + "...")
#     print("\nTables Found:", sum(len(v) for v in content["tables"].values()))
#     for page_num, tables in content["tables"].items():
#         print(f"  Page {page_num+1}: {len(tables)} tables")
#         print(tables[0], tables[1])
#     print("\nImages Found:", len(content["images"]))
#     print("content mismatches", content["mismatched_pages"])
