import os
import json
import requests

# Die direkte JSON-Datenschnittstelle (API) von Cybercrimepolice für die Kategorie 374 (Immobilien)
API_URL = "https://cybercrimepolice.ch"

def fetch_domains_from_api():
    all_domains = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("Rufe offizielle JSON-Schnittstelle ab...")
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Falls die API eine Liste liefert
            if isinstance(data, list):
                for item in data:
                    # Extrahiere die Domain (die API liefert meistens direkt das Feld 'title' oder 'domain')
                    title = item.get("title", {}).get("rendered", "").strip()
                    if title:
                        # Bereinigen falls HTML-Reste vorhanden sind
                        domain_clean = title.lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
                        
                        if domain_clean and domain_clean not in ["cybercrimepolice.ch"]:
                            all_domains.append({
                                "domain": domain_clean,
                                "category": "Verdächtige Immobilienplattformen"
                            })
            print(f"Erfolgreich {len(all_domains)} Domains über API geladen.")
        else:
            print(f"API Fehler: Status {response.status_code}")
    except Exception as e:
        print(f"Verbindungsfehler zur API: {e}")
        
    return all_domains

def main():
    domains = fetch_domains_from_api()
    
    # Sicherungs-Fallback, falls die Schnittstelle gewartet wird
    if not domains:
        domains = [{"domain": "api-temporaer-nicht-erreichbar.com", "category": "System-Meldung"}]

    # Pfad über Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(domains, f, ensure_ascii=False, indent=2)
    print(f"Datei erfolgreich gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
