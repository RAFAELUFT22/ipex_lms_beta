import json
import os
from pathlib import Path

def parse_env(path):
    if not path.exists():
        return {}
    lines = path.read_text().splitlines()
    env = {}
    for line in lines:
        if line.strip() and not line.startswith("#"):
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def main():
    root_dir = Path("/root/projeto-tds")
    env_root = parse_env(root_dir / ".env")
    env_dash = parse_env(root_dir / "dashboard-tds" / ".env")
    
    settings_file = root_dir / "settings.json"
    
    # Defaults from lms_lite_api.py
    settings = {
        "anythingllm_url": env_root.get("ANYTHINGLLM_URL", "https://llm.ipexdesenvolvimento.cloud"),
        "anythingllm_key": env_root.get("ANYTHINGLLM_KEY", ""),
        "anythingllm_workspace": env_root.get("ANYTHINGLLM_WORKSPACE", "tds-lms-knowledge"),
        "openrouter_key": env_root.get("OPENROUTER_KEY", ""),
        "openrouter_model": env_root.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "evolution_url": env_root.get("EVOLUTION_URL", "https://evolution.ipexdesenvolvimento.cloud"),
        "evolution_key": env_root.get("EVOLUTION_KEY", ""),
        "evolution_instance": env_root.get("EVOLUTION_INSTANCE", "tds_suporte_audiovisual"),
        "chatwoot_url": env_root.get("CHATWOOT_URL", "https://chatwoot.ipexdesenvolvimento.cloud"),
        "chatwoot_token": env_root.get("CHATWOOT_TOKEN", ""),
        "chatwoot_inbox_id": env_root.get("CHATWOOT_INBOX_ID", "1"),
        "wa_cloud_api_token": env_root.get("WA_CLOUD_API_TOKEN", ""),
        "wa_phone_number_id": env_root.get("WA_PHONE_NUMBER_ID", ""),
        "admin_key": env_root.get("ADMIN_KEY", "admin-tds-2026"),
        "github_token": env_root.get("GITHUB_TOKEN", ""),
        "dokploy_token": env_root.get("DOKPLOY_API_TOKEN", "")
    }

    if settings_file.exists():
        print(f"File {settings_file} already exists. Merging...")
        with open(settings_file) as f:
            current = json.load(f)
        settings.update(current)

    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully created/updated {settings_file}")

if __name__ == "__main__":
    main()
