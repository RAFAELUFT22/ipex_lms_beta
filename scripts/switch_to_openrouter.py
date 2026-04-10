"""
switch_to_openrouter.py
Salva a chave OpenRouter no Dokploy e atualiza o AnythingLLM via API.
"""
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Credenciais ────────────────────────────────────────────────────────
DOKPLOY_TOKEN  = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
DOKPLOY_BASE   = "http://46.202.150.132:3000/api"
COMPOSE_ID     = "oal_DlgbJpbKfLvIL0wO2"

ANYTHINGLLM_URL = "https://rag.ipexdesenvolvimento.cloud"
ANYTHINGLLM_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"

OPENROUTER_KEY  = "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"
FREE_MODEL      = "google/gemini-2.0-flash-lite:free"

dokploy_headers    = {"x-api-key": DOKPLOY_TOKEN, "Content-Type": "application/json"}
anythingllm_headers = {"Authorization": f"Bearer {ANYTHINGLLM_KEY}", "Content-Type": "application/json"}

# ── 1. Ler env atual do Dokploy ────────────────────────────────────────
print("1. Lendo env atual do Dokploy...")
r = requests.get(f"{DOKPLOY_BASE}/compose.one", headers=dokploy_headers,
                 params={"composeId": COMPOSE_ID}, timeout=15)
current_env = r.json().get("env", "")

# ── 2. Substituir bloco de IA no env ──────────────────────────────────
print("2. Atualizando bloco de IA no env...")

old_llm_block = """# --- Pilar 3: Tutor Cognitivo (AnythingLLM) ---
ANYTHINGLLM_API_KEY=W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0
RAG_URL=https://rag.ipexdesenvolvimento.cloud
LLM_PROVIDER=google
LLM_MODEL_PREF=gemini-1.5-flash
# LLM Providers (Cloud)
GEMINI_API_KEY=AIzaSyABAw4K_KXK52ONaZlzT4S_j-BA6ZEutYo
GROQ_API_KEY=gsk_REDACTED_GROQ_API_KEY"""

new_llm_block = f"""# --- Pilar 3: Tutor Cognitivo (AnythingLLM via OpenRouter) ---
ANYTHINGLLM_API_KEY=W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0
RAG_URL=https://rag.ipexdesenvolvimento.cloud
LLM_PROVIDER=openai
LLM_MODEL_PREF={FREE_MODEL}
# OpenRouter (substitui Gemini direto)
OPENAI_API_KEY={OPENROUTER_KEY}
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY={OPENROUTER_KEY}
# Legacy (desativado, mantido como referência)
GEMINI_API_KEY=AIzaSyABAw4K_KXK52ONaZlzT4S_j-BA6ZEutYo
GROQ_API_KEY=gsk_REDACTED_GROQ_API_KEY"""

if old_llm_block in current_env:
    new_env = current_env.replace(old_llm_block, new_llm_block)
    print("   ✅ Bloco LLM substituído com sucesso.")
else:
    # Append ao final se o bloco exato não foi encontrado
    new_env = current_env + f"\n# OpenRouter (adicionado por switch_to_openrouter.py)\nOPENAI_API_KEY={OPENROUTER_KEY}\nOPENAI_BASE_URL=https://openrouter.ai/api/v1\nOPENROUTER_API_KEY={OPENROUTER_KEY}\nLLM_PROVIDER=openai\nLLM_MODEL_PREF={FREE_MODEL}\n"
    print("   ⚠️  Bloco original não encontrado — chaves adicionadas ao final.")

# ── 3. Salvar env atualizado no Dokploy ───────────────────────────────
print("3. Salvando env atualizado no Dokploy...")
payload = {"composeId": COMPOSE_ID, "env": new_env}
r = requests.post(f"{DOKPLOY_BASE}/compose.update", headers=dokploy_headers,
                  json=payload, timeout=15)
print(f"   Status: {r.status_code} — {r.text[:200]}")

# ── 4. Atualizar AnythingLLM via API REST ─────────────────────────────
print("4. Atualizando AnythingLLM via API...")
anythingllm_data = {
    "LLMProvider": "openai",
    "OpenAiKey": OPENROUTER_KEY,
    "OpenAiModelPref": FREE_MODEL,
    "OpenAiBaseUrl": "https://openrouter.ai/api/v1",
}

endpoints_to_try = [
    "/api/v1/admin/system-preferences",
    "/api/v1/system/update-env",
]

for ep in endpoints_to_try:
    try:
        resp = requests.post(f"{ANYTHINGLLM_URL}{ep}", headers=anythingllm_headers,
                             json=anythingllm_data, verify=False, timeout=15)
        print(f"   [{ep}] Status: {resp.status_code} — {resp.text[:200]}")
        if resp.status_code in (200, 201):
            print("   ✅ AnythingLLM atualizado!")
            break
    except Exception as e:
        print(f"   ❌ {ep}: {e}")

# ── 5. Redeploy da compose ────────────────────────────────────────────
print("5. Solicitando redeploy da compose...")
r = requests.post(f"{DOKPLOY_BASE}/compose.redeploy", headers=dokploy_headers,
                  json={"composeId": COMPOSE_ID}, timeout=30)
print(f"   Status: {r.status_code} — {r.text[:300]}")
print("\n✅ Concluído. Aguarde 2-3 min para os containers subirem.")
