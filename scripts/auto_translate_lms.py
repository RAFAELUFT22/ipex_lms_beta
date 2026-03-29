import requests
import csv
import os
import time
import json
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# Configuração AnythingLLM (Consumindo do ambiente ou fallback)
RAG_URL = os.getenv("RAG_URL", "https://rag.ipexdesenvolvimento.cloud/api/v1")
RAG_API_KEY = os.getenv("RAG_API_KEY", "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0")
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
    # Prompt otimizado para evitar falhas de formatação
    prompt = (
        "Você é um tradutor especializado em sistemas educacionais (Frappe LMS).\n"
        "Converta a lista JSON de textos abaixo para Português do Brasil (pt-BR).\n"
        "REGRAS CRÍTICAS:\n"
        "1. Mantenha placeholders como {0}, {1}, %s intactos.\n"
        "2. Retorne APENAS um objeto JSON onde as chaves são os originais e os valores são as traduções.\n"
        "3. Se não souber traduzir, mantenha o original.\n\n"
        f"TEXTOS: {json.dumps(texts)}"
    )
    
    url = f"{RAG_URL}/workspace/{WORKSPACE}/chat"
    payload = {"message": prompt, "mode": "chat"}
    
    try:
        res = requests.post(url, headers=HEADERS, json=payload, verify=False, timeout=90)
        if res.status_code == 200:
            raw_text = res.json().get("textResponse", "")
            # Tentar extrair JSON da resposta (caso venha com markdown ou explicações)
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "{" in raw_text:
                raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
            
            return json.loads(raw_text)
        elif res.status_code == 429 or (res.status_code == 500 and "429" in res.text):
            print("🛑 Rate limit atingido. Dormindo 120s...", flush=True)
            time.sleep(120)
            return None
        else:
            print(f"❌ Erro na API: {res.status_code} - {res.text}", flush=True)
            return None
    except Exception as e:
        print(f"❌ Erro no processamento: {e}", flush=True)
        return None

def main():
    print("🚀 Tradutor Kreativ TDS v2 (JSON-Safe Batching)", flush=True)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} não encontrado.", flush=True)
        return

    cache = load_cache()
    
    # Carregar todas as chaves
    all_keys = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                all_keys.append(row[0].strip())

    untranslated = [k for k in all_keys if k not in cache]
    print(f"📦 Pendentes: {len(untranslated)} / Total: {len(all_keys)}", flush=True)

    if not untranslated:
        print("✅ Nada para traduzir.", flush=True)
    else:
        # Lotes menores para maior precisão e evitar timeouts
        batch_size = 5 
        for i in range(0, len(untranslated), batch_size):
            batch = untranslated[i:i+batch_size]
            print(f"🔄 Traduzindo lote {i//batch_size + 1}...", flush=True)
            
            result = translate_batch(batch)
            if result and isinstance(result, dict):
                for orig, trans in result.items():
                    cache[orig] = trans
                save_cache(cache)
                print(f"  ✅ Sucesso ({len(result)} itens)", flush=True)
            else:
                print(f"  ❌ Falha no lote. Pulando...", flush=True)
            
            time.sleep(5) # Delay entre lotes

    # Gerar CSV final preservando ordem
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for k in all_keys:
            writer.writerow([k, cache.get(k, k)])

    print(f"🏁 Concluído! Resultado em {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
