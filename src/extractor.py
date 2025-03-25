import fitz
from .utils import verify_extraction_completeness, bbox_overlap
from .ocr_fallback import ocr_page

def extract_pdf_content(path):
    doc = fitz.open(path)
    extracted_text = ""
    images = []
    tables = {}
    per_page_text = {}
    per_page_images = {}
    per_page_tables = {}
    
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
                in_table = False
                
                for tbl_bbox in table_bboxes:
                    if bbox_overlap(block_bbox, tbl_bbox):
                        in_table = True
                        break
                
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
        
        extracted_text += page_text + "\n\n"
        per_page_text[page_num] = page_text.strip()
        
        image_list = page.get_images(full=True)
        per_page_images[page_num] = []
        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]            
            filename = f"image_page{page_num+1}_{xref}.{image_ext}"
            
            image_info = {
                "page": page_num + 1,
                "xref": xref,
                "ext": image_ext,
                "data": image_bytes,
                "filename": filename
            }
            images.append(image_info)
            per_page_images[page_num].append(image_info)
    
    is_complete, mismatched_pages = verify_extraction_completeness(doc, per_page_text, per_page_images, per_page_tables)
    
    if not is_complete:
        for page_num in mismatched_pages:
            ocr_result = ocr_page(doc.load_page(page_num), doc)
            if ocr_result:
                per_page_text[page_num] = ocr_result["text"]
                per_page_tables[page_num] = ocr_result["tables"]
                per_page_images[page_num] = ocr_result["images"]
                extracted_text += ocr_result["text"] + "\n\n"
                images.extend(ocr_result["images"])
                tables[page_num] = ocr_result["tables"]
    
    overall_complete = bool(extracted_text.strip()) and is_complete
    
    return {
        "text": extracted_text.strip(),
        "tables": tables,
        "images": images,
        "complete": overall_complete,
        "per_page_text": per_page_text,
        "per_page_images": per_page_images,
        "per_page_tables": per_page_tables
    }

# if __name__ == "__main__":
#     doc = fitz.open("C:/Users/rachi/Desktop/remote part time test/pdf/cv-fr.pdf")
#     content = extract_pdf_content(doc)
    
#     print("Extracted Text Preview:")
#     print(content["text"] + "...")
#     print("\nTables Found:", sum(len(v) for v in content["tables"].values()))
#     for page_num, tables in content["tables"].items():
#         print(f"  Page {page_num+1}: {len(tables)} tables")
#         print(tables[0], tables[1])
#     print("\nImages Found:", len(content["images"]))
#     print("Extraction Complete:", content["complete"])