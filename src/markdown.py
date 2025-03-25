import os

def convert_to_markdown(extracted_content, file_name, output_dir="output"):  
    os.makedirs(output_dir, exist_ok=True)

    markdown_content = ""
    
    for page_num, text in extracted_content["per_page_text"].items():
        markdown_content += f"\n## Page {page_num + 1}\n\n"
        markdown_content += text + "\n\n"
        
        if page_num in extracted_content["per_page_tables"]:
            for table in extracted_content["per_page_tables"][page_num]:
                markdown_content += "| " + " | ".join(str(item) if item is not None else "Column" for item in (table["header"] or ["Column"] * len(table["rows"][0]))) + " |\n"
                markdown_content += "| " + " | ".join(["---"] * len(table["rows"][0])) + " |\n"
                for row in table["rows"]:
                    markdown_content += "| " + " | ".join(str(item) if item is not None else "" for item in row) + " |\n"
                markdown_content += "\n"
                
        if page_num in extracted_content["per_page_images"]:
            for img_index, img in enumerate(extracted_content["per_page_images"][page_num]):
                img_filename = f"{file_name}_page{page_num + 1}_img{img_index + 1}.{img['filename'].split('.')[-1]}"
                img_path = os.path.join(output_dir, img_filename)
                
                with open(img_path, "wb") as img_file:
                    img_file.write(img["data"])
                markdown_content += f"![Image Page {page_num + 1}](./{img_filename})\n\n"
    
    md_file_path = os.path.join(output_dir, f"{file_name}.md")
    with open(md_file_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
    
    return md_file_path
