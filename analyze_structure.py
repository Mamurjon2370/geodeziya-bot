import docx
from docx.oxml.ns import qn
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def analyze_docx_structure(filename, out_txt):
    doc = docx.Document(filename)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"=== STRUCTURE OF {filename} ===\n")
        
        # Iterate over all block elements in doc.element.body
        body = doc.element.body
        elem_idx = 0
        for child in body:
            tag = child.tag.split('}')[-1]
            if tag == 'p':
                p = docx.text.paragraph.Paragraph(child, doc)
                text = p.text.strip()
                # Check for images in paragraph
                images = child.xpath('.//a:blip/@r:embed')
                
                # Check highlight
                highlights = []
                for r in p.runs:
                    if r.font.highlight_color:
                        highlights.append(str(r.font.highlight_color))
                    elif 'w:highlight' in r._element.xml:
                        highlights.append("xml_highlight")
                
                f.write(f"[{elem_idx}] P: text='{text[:120]}' | imgs={images} | hl={highlights}\n")
                elem_idx += 1
            elif tag == 'tbl':
                tbl = docx.table.Table(child, doc)
                images = child.xpath('.//a:blip/@r:embed')
                cell_texts = []
                for row in tbl.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            cell_texts.append(cell.text.strip().replace('\n', ' '))
                f.write(f"[{elem_idx}] TBL: rows={len(tbl.rows)}, cols={len(tbl.columns)} | imgs={images} | text={' // '.join(cell_texts)[:150]}\n")
                elem_idx += 1

if __name__ == "__main__":
    analyze_docx_structure("савол жавоблар 1.docx", "structure_1.txt")
    analyze_docx_structure("савол жавоблар 2.docx", "structure_2.txt")
    print("Structure analysis completed.")
