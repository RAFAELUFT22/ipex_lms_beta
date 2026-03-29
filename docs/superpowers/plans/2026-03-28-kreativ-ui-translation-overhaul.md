# Kreativ Education (TDS) UI & Translation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Frappe LMS into the "Kreativ Education" experience with a custom sidebar, premium gradients, and a complete pt-BR translation using local LLM inference.

**Architecture:** We use `website_route_rules` to override the core LMS SPA shell with a custom Jinja template (`lms_custom.html`). Translations are handled by a local TeenyTinyLlama 460M model via the `transformers` library to avoid API rate limits.

**Tech Stack:** Frappe Framework, Vue.js (Core LMS), Tailwind/CSS, Python, Transformers (Hugging Face), TeenyTinyLlama.

---

### Task 1: Local Translation Engine (TeenyTinyLlama)

**Files:**
- Create: `scripts/local_translate.py`
- Modify: `scripts/auto_translate_lms.py` (optional refactor)

- [ ] **Step 1: Install dependencies**
Run: `pip install transformers accelerate torch`
Expected: Packages installed.

- [ ] **Step 2: Create local translation script**
Create `scripts/local_translate.py`:
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import csv
import json
import os

MODEL_NAME = "pablo-pfeifer/TeenyTinyLlama-460M-Chat-v1" # Optimized for pt-BR
CACHE_FILE = "translation_cache.json"

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16, device_map="auto")
    return tokenizer, model

def translate(text, tokenizer, model):
    prompt = f"<|user|>\nTraduza para Português do Brasil (pt-BR): '{text}'\n<|assistant|>\n"
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    outputs = model.generate(**inputs, max_new_tokens=100)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("<|assistant|>\n")[-1].strip()

# Main logic to read untranslated.csv and update pt-BR.csv
```

- [ ] **Step 3: Run translation for a small batch**
Run: `python scripts/local_translate.py --limit 5`
Expected: `translation_cache.json` updated with 5 items.

- [ ] **Step 4: Commit engine**
```bash
git add scripts/local_translate.py
git commit -m "feat: add local translation engine using TeenyTinyLlama"
```

---

### Task 2: UI Routing Override

**Files:**
- Modify: `kreativ_theme/kreativ_theme/kreativ_theme/hooks.py`

- [ ] **Step 1: Add website_route_rules**
Modify `hooks.py`:
```python
website_route_rules = [
    {"from_route": "/lms", "to_route": "lms_custom"},
    {"from_route": "/lms/<path:app_path>", "to_route": "lms_custom"}
]
```

- [ ] **Step 2: Commit routing change**
```bash
git add kreativ_theme/kreativ_theme/kreativ_theme/hooks.py
git commit -m "feat: override lms routes to custom template"
```

---

### Task 3: Custom SPA Shell (Kreativ Layout)

**Files:**
- Create: `kreativ_theme/kreativ_theme/kreativ_theme/www/lms_custom.html`

- [ ] **Step 1: Implement the layout with Sidebar**
Create `lms_custom.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/assets/lms/frontend/assets/index-2cPoMQqg.css">
    <link rel="stylesheet" href="/assets/kreativ_theme/css/lms_theme.css">
    <style>
        /* Layout logic */
        #kreativ-wrapper { display: flex; height: 100vh; }
        #sidebar { width: 80px; background: #fff; border-right: 1px solid #eee; }
        #main-content { flex: 1; overflow-y: auto; }
    </style>
</head>
<body>
    <div id="kreativ-wrapper">
        <aside id="sidebar">
            <img src="/files/logo_tds_oficial.png" style="width: 40px; margin: 20px;">
            <!-- Nav Icons -->
        </aside>
        <main id="main-content">
            <div id="app"></div>
        </main>
    </div>
    <script type="module" src="/assets/lms/frontend/assets/index-9PaojE28.js"></script>
    <script>
        window.frappe = {};
        window.frappe.boot = {{ boot | tojson }};
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit template**
```bash
git add kreativ_theme/kreativ_theme/kreativ_theme/www/lms_custom.html
git commit -m "feat: implement custom LMS shell with sidebar"
```

---

### Task 4: Premium Styling (Gradients & Cards)

**Files:**
- Modify: `kreativ_theme/kreativ_theme/kreativ_theme/public/css/lms_theme.css`

- [ ] **Step 1: Apply gradients and Soft UI**
Update `lms_theme.css`:
```css
:root {
    --tds-navy: #003366;
    --tds-teal: #008080;
    --tds-yellow: #F9C300;
}
.lms-hero {
    background: linear-gradient(135deg, var(--tds-navy) 0%, var(--tds-teal) 100%) !important;
    border-radius: 40px !important; /* Mobile style from Image 1 */
}
.course-card {
    border-radius: 14px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
}
```

- [ ] **Step 2: Commit CSS**
```bash
git add kreativ_theme/kreativ_theme/kreativ_theme/public/css/lms_theme.css
git commit -m "style: apply premium gradients and soft ui cards"
```

---

### Task 5: Deploy & Validation

- [ ] **Step 1: Run installation script**
Run: `bash scripts/install_theme.sh`
Expected: Assets published, apps installed.

- [ ] **Step 2: Clear site cache**
Run: `docker exec kreativ-frappe-backend bench --site lms.ipexdesenvolvimento.cloud clear-cache`
Expected: Cache cleared.

- [ ] **Step 3: Validate UI**
Action: Open `https://lms.ipexdesenvolvimento.cloud/lms`
Expected: Sidebar visible, new gradients active.
