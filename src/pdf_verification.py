import pdfplumber
from .utils import text_match, normalize_text, bbox_overlap

def compare_with_pdfplumber(path, extracted_text_pages, extracted_images, extracted_tables):

    mismatched_pages = set()

    with pdfplumber.open(path) as pdf:
        for page_num in range(len(pdf.pages)):
            try:
                plumber_page = pdf.pages[page_num]
                
                plumber_text = plumber_page.extract_text() or ""
                if not text_match(extracted_text_pages.get(page_num, ""), plumber_text):
                    mismatched_pages.add(page_num)
                
                plumber_tables = plumber_page.extract_tables()
                if len(extracted_tables.get(page_num, [])) != len(plumber_tables):
                    mismatched_pages.add(page_num)
                
                plumber_images = []
                for obj in plumber_page.objects.get("image", []):
                    plumber_images.append({
                        "width": obj["width"],
                        "height": obj["height"],
                        "name": obj.get("name", "")
                    })
                
                if len(extracted_images.get(page_num, [])) != len(plumber_images):
                    mismatched_pages.add(page_num)
                else:
                    for img_idx, (pymupdf_img, plumber_img) in enumerate(zip(extracted_images.get(page_num, []), plumber_images)):
                        pymupdf_width = pymupdf_img.get('width', 0)
                        pymupdf_height = pymupdf_img.get('height', 0)
                        
                        if (abs(pymupdf_width - plumber_img["width"]) > 5 or 
                            abs(pymupdf_height - plumber_img["height"]) > 5):
                            mismatched_pages.add(page_num)
                            break
                            
            except Exception as e:
                print(f"Error comparing page {page_num}: {str(e)}")
                mismatched_pages.add(page_num)
    
    return sorted(mismatched_pages)
    
def verify_extraction_completeness(doc, extracted_text_pages, extracted_images, extracted_tables):
    mismatched_pages = []
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        
        table_bboxes = [table.bbox for table in page.find_tables().tables]
        text_dict = page.get_text("dict")
        clean_original_text = ""
        
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                block_bbox = block["bbox"]
                in_table = any(bbox_overlap(block_bbox, tbl_bbox) for tbl_bbox in table_bboxes)
                if not in_table:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            clean_original_text += span.get("text", "") + " "
                        clean_original_text += "\n"
        
        norm_original = normalize_text(clean_original_text)
        norm_extracted = normalize_text(extracted_text_pages.get(page_num, ""))
        
        if norm_original and norm_extracted not in norm_original:
            mismatched_pages.append(page_num)
            continue
        
        pdf_tables = page.find_tables().tables
        extracted_page_tables = extracted_tables.get(page_num, [])
        if len(pdf_tables) != len(extracted_page_tables):
            mismatched_pages.append(page_num)
            continue
        
        pdf_images = page.get_images()
        extracted_page_images = extracted_images.get(page_num, [])
        if len(pdf_images) != len(extracted_page_images):
            mismatched_pages.append(page_num)
    return sorted(mismatched_pages)