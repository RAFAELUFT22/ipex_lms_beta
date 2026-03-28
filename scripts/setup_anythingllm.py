import requests
import os
import urllib3

# Suppress SSL warnings for local connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ANYTHINGLLM_URL = "https://rag.ipexdesenvolvimento.cloud"
API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def create_workspace(slug):
    print(f"Checking/Creating Workspace '{slug}'...")
    url = f"{ANYTHINGLLM_URL}/api/v1/workspace/new"
    data = {"name": slug}
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        if response.status_code == 200:
            print(f" ✅ Workspace '{slug}' created.")
            return True
        elif response.status_code == 403:
            print(f" ℹ️ Workspace '{slug}' already exists or unauthorized.")
            return True
        else:
            print(f" ❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f" ❌ Connection Error: {e}")
        return False

def upload_and_embed(workspace_slug, file_path):
    print(f"Processing {os.path.basename(file_path)}...")
    if not os.path.exists(file_path):
        print(f" ❌ File not found: {file_path}")
        return
        
    url = f"{ANYTHINGLLM_URL}/api/v1/document/upload"
    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
    
    try:
        response = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}"}, files=files, verify=False, timeout=30)
        
        if response.status_code == 200:
            doc_data = response.json().get("documents", [{}])[0]
            location = doc_data.get("location")
            print(f" ✅ Uploaded. Embedding into workspace...")
            
            add_url = f"{ANYTHINGLLM_URL}/api/v1/workspace/{workspace_slug}/update-embeddings"
            add_data = {"adds": [location]}
            add_res = requests.post(add_url, headers=headers, json=add_data, verify=False, timeout=60)
            if add_res.status_code == 200:
                print(" ✅ Knowledge base updated.")
            else:
                print(f" ❌ Embedding failed: {add_res.text}")
        else:
            print(f" ❌ Upload failed: {response.text}")
    except Exception as e:
        print(f" ❌ Error during processing: {e}")

if __name__ == "__main__":
    if create_workspace("tds"):
        docs = [
            "/root/projeto-tds/arquivos_do_projeto/Projeto_TDS_V3.pdf",
            "/root/projeto-tds/arquivos_do_projeto/Cópia de EMENTAS.pdf",
            "/root/projeto-tds/arquivos_do_projeto/Plano_de_Trabalho___TDS_08.25.pdf"
        ]
        for doc in docs:
            upload_and_embed("tds", doc)
    
    print("\n🚀 Knowledge Base setup finalized!")
