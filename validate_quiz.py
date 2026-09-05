import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def validate_quiz_data(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"\n=== Validating {json_file} (Total: {len(data)}) ===")
    
    poll_incompatible_q_len = 0
    poll_incompatible_opt_len = 0
    poll_incompatible_opt_count = 0
    has_image_count = 0
    invalid_correct_idx = 0
    
    for q in data:
        q_text = q['question']
        opts = q['options']
        c_idx = q['correct_option_index']
        img = q['image']
        
        if img:
            has_image_count += 1
            
        if len(q_text) > 300:
            poll_incompatible_q_len += 1
            
        if len(opts) < 2 or len(opts) > 10:
            poll_incompatible_opt_count += 1
            
        for opt in opts:
            if len(opt) > 100:
                poll_incompatible_opt_len += 1
                break
                
        if c_idx < 0 or c_idx >= len(opts):
            invalid_correct_idx += 1
            
    print(f"Questions with image: {has_image_count}")
    print(f"Questions > 300 chars (Poll limit): {poll_incompatible_q_len}")
    print(f"Questions with options > 100 chars (Poll limit): {poll_incompatible_opt_len}")
    print(f"Questions with invalid option count: {poll_incompatible_opt_count}")
    print(f"Questions with invalid correct index: {invalid_correct_idx}")

if __name__ == "__main__":
    validate_quiz_data("quiz_data_1.json")
    validate_quiz_data("quiz_data_2.json")
