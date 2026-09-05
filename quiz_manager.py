import json
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class QuizManager:
    def __init__(self):
        self.data_1 = self._load_json("quiz_data_1.json")
        self.data_2 = self._load_json("quiz_data_2.json")
        
        # Build category map
        self.categories_1 = self._extract_categories(self.data_1)
        self.categories_2 = self._extract_categories(self.data_2)
        
    def _load_json(self, filename):
        full_path = os.path.join(BASE_DIR, filename)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for q in data:
                    if q.get("image"):
                        # Normalize backslashes to forward slashes and ensure absolute path
                        clean_img = q["image"].replace("\\", "/")
                        q["image"] = os.path.join(BASE_DIR, clean_img)
                return data
        return []
        
    def _extract_categories(self, dataset):
        cats = {}
        for q in dataset:
            c = q.get("category", "Umumiy")
            if c not in cats:
                cats[c] = []
            cats[c].append(q)
        return cats

    def get_collection_count(self, collection_id: int):
        if collection_id == 1:
            return len(self.data_1)
        elif collection_id == 2:
            return len(self.data_2)
        elif collection_id == 3: # All combined
            return len(self.data_1) + len(self.data_2)
        return 0

    def get_questions(self, collection_id: int, count: int = 10, shuffle: bool = True, category: str = None):
        if collection_id == 1:
            pool = self.data_1
        elif collection_id == 2:
            pool = self.data_2
        elif collection_id == 3:
            pool = self.data_1 + self.data_2
        else:
            pool = self.data_1

        if category:
            pool = [q for q in pool if q.get("category") == category]

        # Make copy
        selected = list(pool)
        if shuffle:
            random.shuffle(selected)
            
        if count and count < len(selected):
            selected = selected[:count]
            
        # Also randomize options order for each question while preserving correct answer tracking
        prepared_questions = []
        for q in selected:
            orig_opts = list(q['options'])
            correct_opt = orig_opts[q['correct_option_index']]
            
            # Shuffle options
            shuffled_opts = list(orig_opts)
            if shuffle:
                random.shuffle(shuffled_opts)
                
            new_correct_idx = shuffled_opts.index(correct_opt)
            
            prepared_questions.append({
                "collection_id": collection_id if collection_id in (1, 2) else (1 if q in self.data_1 else 2),
                "id": q["id"],
                "category": q.get("category", "Umumiy"),
                "question": q["question"],
                "image": q["image"],
                "options": shuffled_opts,
                "correct_option_index": new_correct_idx,
                "correct_answer": correct_opt
            })
            
        return prepared_questions

    def get_question_by_id(self, collection_id: int, q_id: int):
        pool = self.data_1 if collection_id == 1 else self.data_2
        for q in pool:
            if q["id"] == q_id:
                return q
        return None

quiz_manager = QuizManager()
