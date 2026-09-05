import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document("савол жавоблар 2.docx")
for idx in [1353, 1355, 1357, 1359]:
    p = doc.paragraphs[idx]
    runs_txt = []
    for r in p.runs:
        runs_txt.append(f"'{r.text}'(b={r.bold}, u={r.font.underline}, hl={r.font.highlight_color})")
    print(f"P{idx}: {' + '.join(runs_txt)}")
