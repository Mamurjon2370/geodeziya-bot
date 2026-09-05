import os
import json
from PIL import Image

def convert_dir_images(media_dir):
    print(f"Converting images in {media_dir}...")
    for fname in os.listdir(media_dir):
        fpath = os.path.join(media_dir, fname)
        if fname.lower().endswith(('.wmf', '.emf', '.tiff', '.bmp', '.jpeg', '.jpg')):
            png_name = os.path.splitext(fname)[0] + ".png"
            png_path = os.path.join(media_dir, png_name)
            try:
                with Image.open(fpath) as img:
                    # Convert to RGBA or RGB
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA')
                    img.save(png_path, "PNG")
            except Exception as e:
                print(f"Error converting {fpath}: {e}")

def update_json_paths(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for q in data:
        img = q.get("image")
        if img:
            base, ext = os.path.splitext(img)
            png_path = base + ".png"
            if os.path.exists(png_path):
                q["image"] = png_path
            elif os.path.exists(img):
                try:
                    with Image.open(img) as im:
                        im.save(png_path, "PNG")
                    q["image"] = png_path
                except Exception as e:
                    print(f"Could not convert {img}: {e}")
                    q["image"] = None
            else:
                q["image"] = None
                
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {json_file}")

if __name__ == "__main__":
    convert_dir_images("media_1")
    convert_dir_images("media_2")
    update_json_paths("quiz_data_1.json")
    update_json_paths("quiz_data_2.json")
    print("All images converted to standard PNG and JSONs updated!")
