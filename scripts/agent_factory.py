import requests
import os
import json
import time

# --- Agent Factory for TDS ---
# This script automates:
# 1. AnythingLLM Workspace Creation
# 3. Embedding the TDS Knowledge Base
# 4. Linking to Evolution API / Chatwoot

def load_settings():
    path = "/root/projeto-tds/settings.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

settings = load_settings()

ANYTHINGLLM_URL = settings.get("anythingllm_url", "http://anythingllm:3001")
ANYTHINGLLM_KEY = settings.get("anythingllm_key")
EVOLUTION_URL = settings.get("evolution_url", "https://evolution.ipexdesenvolvimento.cloud")
EVOLUTION_KEY = settings.get("evolution_key")

def headers_llm():
    return {"Authorization": f"Bearer {ANYTHINGLLM_KEY}", "Content-Type": "application/json"}

def create_workspace(name):
    print(f"Creating AnythingLLM Workspace: {name}...")
    base_url = ANYTHINGLLM_URL.rstrip('/')
    # Handle the case where ANYTHINGLLM_URL already ends with /api
    if not base_url.endswith('/api'):
        base_url = f"{base_url}/api"
        
    url = f"{base_url}/v1/workspace/new"
    slug = name.lower().replace(" ", "-").replace("/", "-")
    payload = {"name": name}
    response = requests.post(url, json=payload, headers=headers_llm())
    if response.status_code == 200:
        print(f" ✅ Workspace created: {slug}")
        return slug
    else:
        print(f" ❌ Error creating workspace: {response.status_code} - {response.text}")
        return None

def upload_and_embed(workspace_slug, file_path):
    print(f"Uploading {file_path} to {workspace_slug}...")
    # This involves multiple steps in AnythingLLM API:
    # 1. Upload to /api/v1/document/upload
    # 2. Add to workspace /api/v1/workspace/{slug}/update-embeddings
    
    base_url = ANYTHINGLLM_URL.rstrip('/')
    if not base_url.endswith('/api'):
        base_url = f"{base_url}/api"
        
    upload_url = f"{base_url}/v1/document/upload"
    files = {"file": open(file_path, "rb")}
    res_upload = requests.post(upload_url, files=files, headers={"Authorization": f"Bearer {ANYTHINGLLM_KEY}"})
    
    if res_upload.status_code == 200:
        try:
            doc_data = res_upload.json().get("documents", [])[0]
            location = doc_data.get("location")
            print(f" ✅ File uploaded ({file_path}). Embedding...")
            
            # Now update workspace embeddings
            update_url = f"{base_url}/v1/workspace/{workspace_slug}/update-embeddings"
            payload = {"adds": [location]}
            res_embed = requests.post(update_url, json=payload, headers=headers_llm())
            if res_embed.status_code == 200:
                print(f" ✅ Embeddings updated for {workspace_slug}.")
                return True
            else:
                print(f" ❌ Error embedding: {res_embed.status_code} - {res_embed.text}")
        except Exception as e:
            print(f" ❌ Error parsing upload response: {e}")
            print(f" Response text: {res_upload.text}")
    else:
        print(f" ❌ Error uploading: {res_upload.status_code} - {res_upload.text}")
    
    return False

def set_workspace_settings(slug):
    base_url = ANYTHINGLLM_URL.rstrip('/')
    if not base_url.endswith('/api'):
        base_url = f"{base_url}/api"
        
    url = f"{base_url}/v1/workspace/{slug}/update"
    
    bpm_prompt = (
        "Você é um especialista em Gestão de Processos de Negócio (BPM) com foco em melhoria contínua "
        "e Lean Six Sigma (estilo Zeev). Atue como um Analista de Processos Sênior. "
        "Sua missão é mapear fluxos, identificar gargalos e sugerir redesenhos (TO-BE) otimizados. "
        "Sempre estruture suas respostas definindo o papel, contexto (stakeholders e sistemas) e "
        "saídas em formato de listas, tabelas ou descrições BPMN."
    )
    
    payload = {
        "workspace": {
            "openAiPrompt": bpm_prompt,
            "tts_enabled": True, # User requested TTS/STT
            "stt_enabled": True
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers_llm())
        if response.status_code == 200:
            print(f" ✅ BPM Prompt & TTS/STT enabled for {slug}.")
        else:
            print(f" ⚠️ Response setting prompt: {response.text}")
    except Exception as e:
        print(f" ❌ Error updating workspace settings: {e}")

def provision_agent(agent_name, course_files):
    slug = create_workspace(agent_name)
    if not slug: return None
    
    # Set strategic BPM prompt and features
    set_workspace_settings(slug)
    
    for f in course_files:
        if os.path.exists(f):
            upload_and_embed(slug, f)
            
    print(f"\n🚀 Agent '{agent_name}' is ready as a BPM Specialist.")
    return slug

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 agent_factory.py <AgentName> [course_slug]")
        sys.exit(1)
        
    name = sys.argv[1]
    course_slug = sys.argv[2] if len(sys.argv) > 2 else "geral"
    
    # Files from specific course folder + general files
    course_dir = f"/root/projeto-tds/arquivos_do_projeto/rag_library/{course_slug}"
    general_dir = "/root/projeto-tds/arquivos_do_projeto/rag_library/geral"
    
    rag_files = []
    
    # General files
    if os.path.exists(general_dir):
        rag_files += [os.path.join(general_dir, f) for f in os.listdir(general_dir) if f.endswith(".pdf")]
    
    # Course specific files
    if course_slug != "geral" and os.path.exists(course_dir):
        rag_files += [os.path.join(course_dir, f) for f in os.listdir(course_dir) if f.endswith(".pdf")]
    
    # Unique files only
    rag_files = list(set(rag_files))
    
    provision_agent(name, rag_files)
