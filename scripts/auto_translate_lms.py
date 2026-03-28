import requests
import csv
import os
import time
import json
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# Configuração AnythingLLM
RAG_URL = "https://rag.ipexdesenvolvimento.cloud/api/v1"
RAG_API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"
WORKSPACE = "tds"

# Caminhos Absolutos
BASE_DIR = "/root/projeto-tds"
INPUT_FILE = os.path.join(BASE_DIR, "untranslated.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "pt-BR.csv")
CACHE_FILE = os.path.join(BASE_DIR, "translation_cache.json")

HEADERS = {
    "Authorization": f"Bearer {RAG_API_KEY}",
    "Content-Type": "application/json"
}

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler cache: {e}", flush=True)
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar cache: {e}", flush=True)

def translate_batch(texts):
    prompt = (
        "Você é um tradutor especializado em sistemas educacionais. "
        "Traduza as seguintes frases do Frappe LMS para Português do Brasil (pt-BR). "
        "Mantenha placeholders como {0}, {1}, %s exatamente como estão. "
        "Use termos acadêmicos brasileiros (Ex: Batch -> Turma, Quiz -> Questionário, Lesson -> Lição). "
        "Retorne APENAS as traduções, uma por linha, na mesma ordem.\n\n" + "\n".join(texts)
    )
    
    url = f"{RAG_URL}/workspace/{WORKSPACE}/chat"
    payload = {"message": prompt, "mode": "chat"}
    
    try:
        res = requests.post(url, headers=HEADERS, json=payload, verify=False, timeout=60)
        if res.status_code == 200:
            response_text = res.json().get("textResponse", "")
            lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]
            return lines
        elif res.status_code == 500 and "429" in res.text:
            print("🛑 Rate limit atingido. Aguardando 60 segundos...", flush=True)
            time.sleep(60)
            return None
        else:
            print(f"❌ Erro na API: {res.status_code} - {res.text}", flush=True)
            return None
    except Exception as e:
        print(f"❌ Erro na tradução: {e}", flush=True)
        return None

def main():
    print("🚀 Iniciando script de tradução...", flush=True)
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Arquivo {INPUT_FILE} não encontrado!", flush=True)
        return

    cache = load_cache()
    print(f"✅ Cache carregado com {len(cache)} itens.", flush=True)
    
    untranslated_lines = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] not in cache:
                untranslated_lines.append(row[0])

    print(f"📦 Total de novas linhas para traduzir: {len(untranslated_lines)}", flush=True)
    if not untranslated_lines:
        print("✅ Tudo já está no cache.", flush=True)
    else:
        batch_size = 10
        total_batches = (len(untranslated_lines) + batch_size - 1) // batch_size
        for i in range(0, len(untranslated_lines), batch_size):
            batch = untranslated_lines[i:i+batch_size]
            print(f"🔄 Traduzindo lote {i//batch_size + 1} / {total_batches}...", flush=True)
            
            translations = translate_batch(batch)
            
            if translations and len(translations) == len(batch):
                for original, translated in zip(batch, translations):
                    cache[original] = translated
                save_cache(cache)
                print(f"✅ Lote {i//batch_size + 1} salvo.", flush=True)
            else:
                print(f"⚠️ Falha no lote {i//batch_size + 1}. Tentando modo individual...", flush=True)
                for text in batch:
                    if text in cache: continue
                    res = translate_batch([text])
                    if res:
                        cache[text] = res[0]
                        save_cache(cache)
                        print(f"  - Traduzido: {text[:20]}...", flush=True)
                        time.sleep(2)
                    else:
                        print(f"  - Falhou: {text[:20]}...", flush=True)
            
            time.sleep(3)

    # Gerar o CSV final
    final_data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                orig = row[0]
                trans = cache.get(orig, orig)
                final_data.append([orig, trans])

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(final_data)

    print(f"🚀 Concluído! Arquivo: {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
