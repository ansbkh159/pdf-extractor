import pytesseract
from PIL import Image
import io
import fitz

def ocr_page(page, doc, dpi=300):
    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        
        pix = page.get_pixmap(matrix=matrix)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        custom_config = r'--oem 3 --psm 6 -l eng+fra'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        images = []
        for img_index, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            images.append({
                "page": page.number + 1,
                "xref": xref,
                "ext": image_ext,
                "data": image_bytes,
                "filename": f"image_page{page.number+1}_{xref}.{image_ext}"
            })
        
        tables = []
        pdf_tables = page.find_tables().tables
        if pdf_tables:
            for table in pdf_tables:
                tables.append({
                    "bbox": table.bbox,
                    "rows": table.extract(),
                    "header": table.header.names if table.header else None,
                    "source": "pdf"
                })
        else:
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            potential_tables = detect_tables_from_ocr(ocr_data)
            tables.extend(potential_tables)
        
        return {
            "text": text,
            "tables": tables,
            "images": images,
            "page_number": page.number + 1
        }
        
    except Exception as e:
        print(f"OCR failed on page {page.number}: {str(e)}")
        return None

def detect_tables_from_ocr(ocr_data):
    tables = []    
    rows = {}
    for i in range(len(ocr_data["text"])):
        if int(ocr_data["conf"][i]) > 60:
            x, y, w, h = (
                int(ocr_data["left"][i]),
                int(ocr_data["top"][i]),
                int(ocr_data["width"][i]),
                int(ocr_data["height"][i])
            )
            text = ocr_data["text"][i].strip()
            
            if text:
                found_row = False
                for row_y in rows:
                    if abs(y - row_y) < h/2:
                        rows[row_y].append((x, text))
                        found_row = True
                        break
                if not found_row:
                    rows[y] = [(x, text)]
    
    table_rows = []
    for y in sorted(rows.keys()):
        row = sorted(rows[y], key=lambda item: item[0])
        if len(row) > 1:
            table_rows.append([text for (x, text) in row])
    
    if len(table_rows) >= 2:
        tables.append({
            "rows": table_rows,
            "header": table_rows[0] if len(table_rows) > 1 else None,
            "source": "ocr"
        })
    
    return tables
