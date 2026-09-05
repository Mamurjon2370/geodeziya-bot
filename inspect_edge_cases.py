import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect_invalid_questions(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"=== Inspecting invalid option count in {json_file} ===")
    for q in data:
        if len(q['options']) < 2 or len(q['options']) > 10:
            print(f"ID {q['id']}: Q='{q['question']}' | opts count={len(q['options'])} | opts={q['options']}")

if __name__ == "__main__":
    inspect_invalid_questions("quiz_data_1.json")
    inspect_invalid_questions("quiz_data_2.json")
