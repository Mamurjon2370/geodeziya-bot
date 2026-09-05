import docx
import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

def parse_document_to_quiz(filename, media_folder):
    doc = docx.Document(filename)
    os.makedirs(media_folder, exist_ok=True)
    
    # Save all media parts
    part_to_file = {}
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.target_ref:
            img_part = rel.target_part
            ext = rel.target_ref.split('.')[-1]
            img_filename = f"{rel_id}.{ext}"
            img_path = os.path.join(media_folder, img_filename)
            with open(img_path, "wb") as f:
                f.write(img_part.blob)
            part_to_file[rel_id] = img_path

    body = doc.element.body
    questions = []
    
    current_category = "Umumiy savollar"
    
    # State tracking
    current_q_text = None
    current_q_images = []
    current_options = []
    correct_idx = -1
    
    def save_current_question():
        nonlocal current_q_text, current_q_images, current_options, correct_idx
        if current_q_text and current_options:
            # If no option was highlighted, default to 0 or check
            if correct_idx == -1:
                c_idx = 0
            else:
                c_idx = correct_idx
                
            # clean options
            clean_opts = [re.sub(r'^[A-D1-4a-d][\.\)\s]+', '', opt).strip() for opt in current_options]
            
            questions.append({
                "id": len(questions) + 1,
                "category": current_category,
                "question": current_q_text,
                "image": current_q_images[0] if current_q_images else None,
                "options": clean_opts,
                "correct_option_index": c_idx,
                "correct_answer": clean_opts[c_idx] if 0 <= c_idx < len(clean_opts) else ""
            })
        current_q_text = None
        current_q_images = []
        current_options = []
        correct_idx = -1

    for child in body:
        tag = child.tag.split('}')[-1]
        
        if tag == 'p':
            p = docx.text.paragraph.Paragraph(child, doc)
            text = p.text.strip()
            if not text:
                continue
                
            if text.lower() == "тест":
                continue
                
            # Category header e.g. "I. Геодезия ва картография..."
            if re.match(r'^(?:[I|V|X]+|\d+)\.\s+[А-ЯЁA-Z]', text) and len(text) < 150 and not text.endswith('?'):
                save_current_question()
                current_category = text
                continue
                
            # Check highlight
            has_hl = False
            for r in p.runs:
                if r.font.highlight_color or 'w:highlight' in r._element.xml:
                    has_hl = True
                    break
                    
            # Check images
            blips = child.xpath('.//a:blip/@r:embed')
            img_files = [part_to_file[b] for b in blips if b in part_to_file]
            
            # Is this paragraph a question or an option?
            # A question:
            # - Has '?' at the end, OR
            # - We don't have current_q_text yet, OR
            # - We currently have a question with some options, and this is NOT highlighted and has '?'
            is_question = False
            if text.endswith('?') or text.endswith('? '):
                is_question = True
            elif current_q_text is None and not has_hl:
                is_question = True
                
            if is_question:
                if current_q_text is not None and len(current_options) >= 2:
                    save_current_question()
                
                if current_q_text is None:
                    current_q_text = text
                    current_q_images = img_files
                else:
                    # Maybe multi-line question
                    if len(current_options) == 0:
                        current_q_text += " " + text
                        current_q_images.extend(img_files)
                    else:
                        save_current_question()
                        current_q_text = text
                        current_q_images = img_files
            else:
                # This is an option
                if current_q_text is None:
                    # An option before any question? Might be visual table or question text
                    current_q_text = "Quyidagi rasmda / belgida nima tasvirlangan?"
                
                if has_hl:
                    correct_idx = len(current_options)
                current_options.append(text)
                
        elif tag == 'tbl':
            # Table question
            save_current_question()
            tbl = docx.table.Table(child, doc)
            
            tbl_img = None
            tbl_opts = []
            tbl_correct = -1
            
            for row in tbl.rows:
                for c_idx, cell in enumerate(row.cells):
                    blips = cell._element.xpath('.//a:blip/@r:embed')
                    if blips and not tbl_img:
                        for b in blips:
                            if b in part_to_file:
                                tbl_img = part_to_file[b]
                                break
                    
                    # check paragraphs in cell
                    for p in cell.paragraphs:
                        p_text = p.text.strip()
                        if not p_text:
                            continue
                        # ignore pure numbers 1, 2, 3, 4
                        if re.match(r'^\d+$', p_text):
                            continue
                        has_hl = False
                        for r in p.runs:
                            if r.font.highlight_color or 'w:highlight' in r._element.xml:
                                has_hl = True
                                break
                        if has_hl:
                            tbl_correct = len(tbl_opts)
                        tbl_opts.append(p_text)
                        
            if tbl_opts:
                questions.append({
                    "id": len(questions) + 1,
                    "category": current_category,
                    "question": "Quyidagi shartli belgi nimani bildiradi?",
                    "image": tbl_img,
                    "options": tbl_opts,
                    "correct_option_index": tbl_correct if tbl_correct != -1 else 0,
                    "correct_answer": tbl_opts[tbl_correct] if tbl_correct != -1 else tbl_opts[0]
                })

    save_current_question()
    print(f"Total questions parsed for {filename}: {len(questions)}")
    return questions

if __name__ == "__main__":
    q1 = parse_document_to_quiz("савол жавоблар 1.docx", "media_1")
    q2 = parse_document_to_quiz("савол жавобlar 2.docx" if not os.path.exists("савол жавоблар 2.docx") else "савол жавоблар 2.docx", "media_2")
    
    with open("quiz_data_1.json", "w", encoding="utf-8") as f:
        json.dump(q1, f, ensure_ascii=False, indent=2)
    with open("quiz_data_2.json", "w", encoding="utf-8") as f:
        json.dump(q2, f, ensure_ascii=False, indent=2)
        
    print("Parsed both files successfully!")
