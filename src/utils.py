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
    
    if mismatched_pages:
        return False, mismatched_pages
    
    return True, "All content extracted successfully"

def normalize_text(text):
    return " ".join(text.lower().strip().split())

def bbox_overlap(bbox1, bbox2, threshold=0.5):
    x1, y1, x2, y2 = bbox1
    x3, y3, x4, y4 = bbox2
    
    x_overlap = max(0, min(x2, x4) - max(x1, x3))
    y_overlap = max(0, min(y2, y4) - max(y1, y3))
    intersection = x_overlap * y_overlap
    
    area1 = (x2 - x1) * (y2 - y1)
    
    return intersection > (area1 * threshold)

def text_match(text1, text2, threshold=0.9):
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    if norm1 == norm2:
        return True
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold