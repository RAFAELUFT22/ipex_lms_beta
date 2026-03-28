import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://lms.ipexdesenvolvimento.cloud"
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = os.getenv("FRAPPE_API_SECRET")

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def upload_file(file_path):
    print(f"Uploading {file_path}...")
    if not os.path.exists(file_path):
        print(f" ❌ File not found: {file_path}")
        return None
    url = f"{BASE_URL}/api/method/upload_file"
    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
    # Note: Authorization header is required
    upload_headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
    response = requests.post(url, headers=upload_headers, files=files)
    if response.status_code == 200:
        file_url = response.json().get("message", {}).get("file_url")
        print(f" ✅ Uploaded: {file_url}")
        return file_url
    print(f" ❌ Upload failed: {response.text}")
    return None

def update_lms_settings(logo_url, banner_url):
    print("Updating LMS Settings...")
    url = f"{BASE_URL}/api/resource/LMS Settings/LMS Settings"
    data = {
        "portal_name": "TDS – Território de Desenvolvimento Social",
        "portal_description": "Projeto de Inclusão Produtiva e Inovação Territorial – UFT / IPEX / MDS / FAPTO",
        "brand_logo": logo_url,
        "banner_image": banner_url,
        "primary_brand_color": "#003366", # UFT Navy Blue
        "show_banner": 1
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("✅ LMS Settings updated successfully.")
    else:
        print(f"❌ Error updating LMS Settings: {response.text}")

if __name__ == "__main__":
    # 1. Logos Acquisition
    logo_path = "/root/projeto-tds/arquivos_do_projeto/logos/logo_tds_oficial.png"
    banner_path = "/root/projeto-tds/arquivos_do_projeto/logos/logo-ipex.jpg"
    
    logo_url = upload_file(logo_path)
    banner_url = upload_file(banner_path)
    
    if logo_url and banner_url:
        update_lms_settings(logo_url, banner_url)
    
    # 2. Upload additional logos for footer reference (if needed in other places)
    footer_path = "/root/projeto-tds/arquivos_do_projeto/logos/uft logo.png"
    upload_file(footer_path)
    
    print("\n🚀 TDS Branding Finalization Completed!")
