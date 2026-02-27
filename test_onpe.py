import requests
import re

def extract_api():
    url = "https://consultaelectoral.onpe.gob.pe/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    
    # Extract any js files
    js_files = re.findall(r'src="([^"]+\.js)"', response.text)
    for js in js_files:
        if not js.startswith('http'):
            js = "https://consultaelectoral.onpe.gob.pe/" + js
        
        js_resp = requests.get(js, headers=headers)
        
        # searching for anything that looks like an endpoint /api/
        endpoints = re.findall(r'["\']/[a-zA-Z0-9_-]+/api/[a-zA-Z0-9_/-]+["\']', js_resp.text)
        endpoints2 = re.findall(r'["\']https?://[^"\']+/api/[^"\']+["\']', js_resp.text)
        endpoints3 = re.findall(r'["\']/.*?api.*?["\']', js_resp.text)

        all_endpoints = set(endpoints + endpoints2 + endpoints3)
        if all_endpoints:
            print(f"Endpoints in {js}:", all_endpoints)

if __name__ == "__main__":
    extract_api()
