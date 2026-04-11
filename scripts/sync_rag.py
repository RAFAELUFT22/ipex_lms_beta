import requests
import os
import sys

# === CONFIGURAÇÕES ===
ANYTHINGLLM_URL = "https://rag.ipexdesenvolvimento.cloud"
API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"
WORKSPACE_SLUG = "tds" # Ajustado para o workspace real encontrado
SOURCE_DIR = "/root/projeto-tds/rag-brain"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def sync_documents():
    print(f"🔍 Iniciando sincronização RAG em: {SOURCE_DIR}...")
    
    files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
    
    if not files:
        print("⚠️ Nenhum arquivo encontrado para sincronizar.")
        return

    for file_name in files:
        file_path = os.path.join(SOURCE_DIR, file_name)
        print(f"📤 Enviando: {file_name}...")
        
        # 1. Upload do documento
        upload_url = f"{ANYTHINGLLM_URL}/api/v1/document/upload"
        with open(file_path, 'rb') as f:
            files_payload = {'file': (file_name, f)}
            try:
                # Nota: Upload geralmente usa multipart/form-data, então removemos Content-Type do header padrão
                upload_headers = {"Authorization": f"Bearer {API_KEY}"}
                response = requests.post(upload_url, files=files_payload, headers=upload_headers)
                
                if response.status_code == 200:
                    doc_data = response.json()
                    doc_id = doc_data['documents'][0]['location']
                    print(f"✅ Upload concluído! Document ID: {doc_id}")
                    
                    # 2. Mover para o Workspace e dar Embed
                    # O AnythingLLM costuma usar o slug do workspace
                    # Este endpoint é um exemplo comum na API deles
                    ws_url = f"{ANYTHINGLLM_URL}/api/v1/workspace/{WORKSPACE_SLUG}/update-embeddings"
                    payload = {
                        "adds": [doc_id]
                    }
                    ws_res = requests.post(ws_url, json=payload, headers=headers)
                    
                    if ws_res.status_code == 200:
                        print(f"🚀 {file_name} integrado ao cérebro '{WORKSPACE_SLUG}'!")
                    else:
                        print(f"❌ Erro ao embutir no workspace: {ws_res.status_code} - {ws_res.text}")
                else:
                    print(f"❌ Erro no upload: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"💥 Falha crítica: {e}")

if __name__ == "__main__":
    sync_documents()
