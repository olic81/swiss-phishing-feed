import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://cybercrimepolice.ch{}&query=&category=374"

def fetch_all_domains():
    all_domains = []
    page = 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    while page <= 3:
        url = BASE_URL.format(page)
        print(f"Lade Seite {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()

            domain_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b"
            found_domains = re.findall(domain_pattern, page_text, re.IGNORECASE)

            page_added = 0
            for domain in found_domains:
                domain_clean = domain.lower().strip()
                if domain_clean not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com"]:
                    if not any(d["domain"] == domain_clean for d in all_domains):
                        all_domains.append({
                            "domain": domain_clean,
                            "category": "Verdächtige Immobilienplattformen"
                        })
                        page_added += 1

            if page_added == 0:
                break
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"Fehler: {e}")
            break
    return all_domains

def main():
    domains = fetch_all_domains()
    if not domains:
        domains = [{"domain": "fallback-aktiv.com", "category": "System-Meldung"}]

    # Absoluter Pfad zum Hauptverzeichnis des GitHub-Runners erzwingen
    workspace = os.getenv("GITHUB_WORKSPACE", os.getcwd())
    file_path = os.path.join(workspace, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(domains, f, ensure_ascii=False, indent=2)
    print(f"Datei erfolgreich gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
