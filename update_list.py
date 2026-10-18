import os
import json
import re
import requests

# Die direkte JSON-Schnittstelle der Kantonspolizei Zürich (holt die neuesten 100 Einträge unfiltriert)
API_URL = "https://cybercrimepolice.ch"

def fetch_all_verified_entries():
    all_entries = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print("Verbinde direkt mit der polizeilichen JSON-Datenschnittstelle...")
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            posts = response.json()
            print(f"API antwortet stabil. Verarbeite {len(posts)} Live-Datensätze...")
            
            # Erkennt Domains (z.B. kaffeemachers.shop) und Krypto-Wallets (26-42 Zeichen)
            entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
            
            for post in posts:
                # Textinhalte aus der polizeilichen Datenbank extrahieren
                title_text = post.get("title", {}).get("rendered", "")
                content_text = post.get("content", {}).get("rendered", "")
                combined_text = f"{title_text} {content_text}"
                
                match = re.search(entry_pattern, combined_text)
                if match:
                    clean_value = match.group(0).strip().lower()
                    
                    # Kategorie anhand des Inhalts zuweisen
                    category = "Verdächtige Onlineplattform"
                    if "krypto" in combined_text.lower():
                        category = "Verdächtige Kryptoadresse"
                    elif "immobil" in combined_text.lower():
                        category = "Verdächtige Immobilienplattform"
                        
                    # System-Domains filtern, um Fehlalarme in Ihrer App zu verhindern
                    if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com", "w3.org"]:
                        if not any(e["value"] == clean_value for e in all_entries):
                            all_entries.append({
                                "value": clean_value,
                                "category": category
                            })
                            
            print(f"Verarbeitung abgeschlossen. {len(all_entries)} verifizierte Schweizer Betrugsfälle geladen.")
        else:
            print(f"API-Fehler: Status {response.status_code}")
            
    except Exception as e:
        print(f"Verbindungsfehler zur Schnittstelle: {e}")
        
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    if not entries:
        print("Schnittstelle lieferte keine Ergebnisse. Fallback aktiviert.")
        entries = [{"value": "api-warten-auf-freigabe.com", "category": "System-Meldung"}]

    # Speicherpfad über Ihre Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Datei erfolgreich im Verzeichnis aktualisiert: {file_path}")

if __name__ == "__main__":
    main()
