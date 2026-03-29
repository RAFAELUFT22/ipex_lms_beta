import os
import json
import csv
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

MODEL_NAME = "nicholasKluge/TeenyTinyLlama-460m-Chat"
CACHE_FILE = "translation_cache.json"
INPUT_FILE = "untranslated.csv"
OUTPUT_FILE = "pt-BR.csv"
BATCH_SIZE = 5

def load_model():
    print(f"Loading model {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, 
        device_map="auto", 
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    return tokenizer, model

def load_cache():
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache.update(json.load(f))
    
    # Also load from pt-BR.csv to avoid re-translating existing ones
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        original, translation = row[0], row[1]
                        if original not in cache:
                            cache[original] = translation
        except Exception as e:
            print(f"Warning: Could not read {OUTPUT_FILE}: {e}")
            
    return cache

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def translate(text, tokenizer, model):
    if not text.strip():
        return text
        
    # Few-shot prompt inside instruction for better guidance
    prompt = (
        "<instruction> Traduza os termos de interface de Inglês para Português (Brasil).\n"
        "Inglês: Courses\nPortuguês: Cursos\n"
        "Inglês: Log out\nPortuguês: Sair\n"
        f"Inglês: {text}\nPortuguês: </instruction>"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=32, 
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # print(f"DEBUG: full_output='{full_output}'")
    
    # Extract translation after the last "Português:"
    # Since we have multiple "Português:", we want the one after the last "Inglês: {text}"
    parts = full_output.split("Português:")
    if len(parts) > 1:
        translation = parts[-1].strip().split("\n")[0].split("</instruction>")[0].strip()
    else:
        translation = full_output.strip()
        
    return translation

def main(limit=None):
    tokenizer, model = load_model()
    cache = load_cache()
    
    untranslated = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            untranslated = [line.strip() for line in f if line.strip()]
    
    if limit:
        untranslated = untranslated[:limit]
        print(f"Limited to first {limit} items.")

    to_translate = [s for s in untranslated if s not in cache]
    print(f"Found {len(to_translate)} items to translate.")

    for i in range(0, len(to_translate), BATCH_SIZE):
        batch = to_translate[i:i+BATCH_SIZE]
        print(f"Translating batch {i//BATCH_SIZE + 1}...")
        
        for item in batch:
            translation = translate(item, tokenizer, model)
            cache[item] = translation
            print(f"  '{item}' -> '{translation}'")
            
        save_cache(cache)
        
        # Also update pt-BR.csv
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Add back all items from cache that were in original untranslated list
            # or just all items from cache?
            # The requirement is to save missing items to cache/output.
            # Usually pt-BR.csv should contain all translations.
            for original, trans in cache.items():
                writer.writerow([original, trans])

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    main(limit=args.limit)
