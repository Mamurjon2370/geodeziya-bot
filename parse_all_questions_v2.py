import docx
import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

def parse_runs_text(p):
    parts = []
    has_hl = False
    for r in p.runs:
        t = r.text
        if not t:
            continue
        if r.font.highlight_color or 'w:highlight' in r._element.xml:
            has_hl = True
        if r.font.underline:
            t = f"<u>{t}</u>"
        elif r.bold:
            # only if not entire paragraph is bold
            pass
        parts.append(t)
    return "".join(parts).strip(), has_hl

def is_para_bold(p):
    non_empty_runs = [r for r in p.runs if r.text.strip()]
    if not non_empty_runs:
        return False
    return all(r.bold for r in non_empty_runs)

def parse_document_to_quiz_v2(filename, media_folder):
    doc = docx.Document(filename)
    os.makedirs(media_folder, exist_ok=True)
    
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
    
    current_q_text = None
    current_q_images = []
    current_options = []
    correct_idx = -1
    
    def save_current_question():
        nonlocal current_q_text, current_q_images, current_options, correct_idx
        if current_q_text and current_options:
            c_idx = correct_idx if correct_idx != -1 else 0
            
            # Clean options
            clean_opts = []
            for opt in current_options:
                cleaned = re.sub(r'^[A-D1-4a-d][\.\)\s]+', '', opt).strip()
                if cleaned:
                    clean_opts.append(cleaned)
                    
            if len(clean_opts) >= 2:
                # Remove question numbering prefix like "1. ", "25. "
                clean_q = re.sub(r'^\d+[\.\)]\s*', '', current_q_text).strip()
                questions.append({
                    "id": len(questions) + 1,
                    "category": current_category,
                    "question": clean_q,
                    "image": current_q_images[0] if current_q_images else None,
                    "options": clean_opts,
                    "correct_option_index": min(c_idx, len(clean_opts) - 1),
                    "correct_answer": clean_opts[min(c_idx, len(clean_opts) - 1)]
                })
        current_q_text = None
        current_q_images = []
        current_options = []
        correct_idx = -1

    for child in body:
        tag = child.tag.split('}')[-1]
        
        if tag == 'p':
            p = docx.text.paragraph.Paragraph(child, doc)
            plain_text = p.text.strip()
            if not plain_text:
                continue
                
            if plain_text.lower() == "тест":
                continue
                
            # Category header
            if re.match(r'^(?:[I|V|X]+|\d+)\.\s+[А-ЯЁA-Z]', plain_text) and len(plain_text) < 150 and not plain_text.endswith('?'):
                save_current_question()
                current_category = plain_text
                continue
                
            formatted_text, has_hl = parse_runs_text(p)
            bold = is_para_bold(p)
            
            blips = child.xpath('.//a:blip/@r:embed')
            img_files = [part_to_file[b] for b in blips if b in part_to_file]
            
            # Determine if this is a question header
            is_question = False
            if not has_hl:
                if plain_text.endswith('?') or plain_text.endswith('? '):
                    is_question = True
                elif bold and (re.match(r'^\d+[\.\)]', plain_text) or len(current_options) >= 2 or current_q_text is None):
                    is_question = True
                elif re.match(r'^\d+[\.\)]\s+[А-ЯЁA-Z]', plain_text):
                    is_question = True
                elif current_q_text is None:
                    is_question = True
                    
            if is_question:
                if current_q_text is not None and len(current_options) >= 2:
                    save_current_question()
                    
                if current_q_text is None:
                    current_q_text = plain_text
                    current_q_images = img_files
                else:
                    if len(current_options) == 0:
                        current_q_text += " " + plain_text
                        current_q_images.extend(img_files)
                    else:
                        save_current_question()
                        current_q_text = plain_text
                        current_q_images = img_files
            else:
                # Option
                if current_q_text is None:
                    current_q_text = "Quyidagi variantlardan to'g'risini tanlang:"
                    
                if has_hl:
                    correct_idx = len(current_options)
                current_options.append(formatted_text)
                
        elif tag == 'tbl':
            save_current_question()
            tbl = docx.table.Table(child, doc)
            tbl_img = None
            tbl_opts = []
            tbl_correct = -1
            
            for row in tbl.rows:
                for cell in row.cells:
                    blips = cell._element.xpath('.//a:blip/@r:embed')
                    if blips and not tbl_img:
                        for b in blips:
                            if b in part_to_file:
                                tbl_img = part_to_file[b]
                                break
                    for p in cell.paragraphs:
                        p_plain = p.text.strip()
                        if not p_plain or re.match(r'^\d+$', p_plain):
                            continue
                        p_fmt, p_hl = parse_runs_text(p)
                        if p_hl:
                            tbl_correct = len(tbl_opts)
                        tbl_opts.append(p_fmt)
                        
            if len(tbl_opts) >= 2:
                questions.append({
                    "id": len(questions) + 1,
                    "category": current_category,
                    "question": "Quyidagi shartli belgi nimani bildiradi?",
                    "image": tbl_img,
                    "options": tbl_opts,
                    "correct_option_index": tbl_correct if tbl_correct != -1 else 0,
                    "correct_answer": tbl_opts[tbl_correct if tbl_correct != -1 else 0]
                })

    save_current_question()
    print(f"File {filename} parsed -> {len(questions)} clean questions.")
    return questions

if __name__ == "__main__":
    q1 = parse_document_to_quiz_v2("савол жавоблар 1.docx", "media_1")
    q2 = parse_document_to_quiz_v2("савол жавобlar 2.docx" if not os.path.exists("савол жавоблар 2.docx") else "савол жавоблар 2.docx", "media_2")
    
    with open("quiz_data_1.json", "w", encoding="utf-8") as f:
        json.dump(q1, f, ensure_ascii=False, indent=2)
    with open("quiz_data_2.json", "w", encoding="utf-8") as f:
        json.dump(q2, f, ensure_ascii=False, indent=2)
        
    print("Exported quiz_data_1.json and quiz_data_2.json successfully!")
