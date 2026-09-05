import docx
import os
import sys
import json
import base64

sys.stdout.reconfigure(encoding='utf-8')

def parse_full_doc(filename, output_json, media_dir):
    doc = docx.Document(filename)
    os.makedirs(media_dir, exist_ok=True)
    
    # Save all media parts
    part_to_file = {}
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.target_ref:
            img_part = rel.target_part
            ext = rel.target_ref.split('.')[-1]
            img_filename = f"{rel_id}.{ext}"
            img_path = os.path.join(media_dir, img_filename)
            with open(img_path, "wb") as f:
                f.write(img_part.blob)
            part_to_file[rel_id] = img_path
            
    print(f"Extracted {len(part_to_file)} media parts for {filename}")

    # Now let's iterate through body elements in sequence
    body = doc.element.body
    questions = []
    
    # We will accumulate questions
    # Standard text questions:
    # A question paragraph (usually not highlighted, often has ? or section/lead-in)
    # followed by 3-4 option paragraphs, one of which has YELLOW highlight (the correct answer).
    #
    # Table questions:
    # A table containing options in one cell (one highlighted) and image in another cell!
    
    items = []
    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            p = docx.text.paragraph.Paragraph(child, doc)
            text = p.text.strip()
            # find images
            blips = child.xpath('.//a:blip/@r:embed')
            img_files = [part_to_file[b] for b in blips if b in part_to_file]
            
            # find highlight
            has_hl = False
            for r in p.runs:
                if r.font.highlight_color:
                    has_hl = True
                    break
                if 'w:highlight' in r._element.xml:
                    has_hl = True
                    break
            
            items.append({
                'type': 'p',
                'text': text,
                'is_highlighted': has_hl,
                'images': img_files
            })
        elif tag == 'tbl':
            tbl = docx.table.Table(child, doc)
            # check cells
            tbl_info = []
            for r_idx, row in enumerate(tbl.rows):
                for c_idx, cell in enumerate(row.cells):
                    blips = cell._element.xpath('.//a:blip/@r:embed')
                    img_files = [part_to_file[b] for b in blips if b in part_to_file]
                    
                    # paragraphs in cell
                    cell_paras = []
                    for p in cell.paragraphs:
                        p_text = p.text.strip()
                        if p_text:
                            has_hl = False
                            for r in p.runs:
                                if r.font.highlight_color or 'w:highlight' in r._element.xml:
                                    has_hl = True
                                    break
                            cell_paras.append({
                                'text': p_text,
                                'is_highlighted': has_hl
                            })
                    if cell_paras or img_files:
                        tbl_info.append({
                            'row': r_idx,
                            'col': c_idx,
                            'paras': cell_paras,
                            'images': img_files
                        })
            items.append({
                'type': 'tbl',
                'cells': tbl_info
            })
            
    print(f"Total raw items parsed: {len(items)}")
    return items, part_to_file

if __name__ == "__main__":
    items1, media1 = parse_full_doc("савол жавоблар 1.docx", "data_1.json", "media_1")
    items2, media2 = parse_full_doc("савол жавобlar 2.docx" if not os.path.exists("савол жавоблар 2.docx") else "савол жавоблар 2.docx", "data_2.json", "media_2")
