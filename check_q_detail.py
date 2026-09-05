import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document("савол жавоблар 2.docx")
found = False
for i, p in enumerate(doc.paragraphs):
    if "Интернет оркали" in p.text:
        found = True
    if found:
        print(f"P{i}: text='{p.text}' | bold={[r.bold for r in p.runs]} | hl={[r.font.highlight_color for r in p.runs]}")
        if "туманни билдиради" in p.text:
            # print next 10 paras
            for j in range(i+1, min(i+10, len(doc.paragraphs))):
                p2 = doc.paragraphs[j]
                print(f"P{j}: text='{p2.text}' | bold={[r.bold for r in p2.runs]} | hl={[r.font.highlight_color for r in p2.runs]}")
            break
