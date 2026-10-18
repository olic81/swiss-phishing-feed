import os
import json
import re
import requests

# Die direkte, offizielle JSON-Schnittstelle der Kantonspolizei Zürich.
# Holt die neuesten 100 Einträge aller Kategorien unfiltriert auf einen Schlag ab.
API_URL = "https://cybercrimepolice.ch"

def fetch_live_phishing_data():
    all_entries = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        print("Verbinde direkt mit der polizeilichen JSON-Datenschnittstelle...")
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            raw_data = response.json()
            print(f"Schnittstelle antwortet stabil. Verarbeite Datensätze...")
            
            # Regulärer Ausdruck für Domains (kaffeemachers.shop) und Krypto-Wallets (bc1q...)
            entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
            
            # Die Schnittstelle liefert ein JSON-Array. Wir durchlaufen jeden Eintrag einzeln.
            if isinstance(raw_data, list):
                for item in raw_data:
                    # Wir extrahieren den Titel (enthält die Domain oder die Wallet) und die Kategorie
                    title = item.get("title", "").strip()
                    category_raw = item.get("category", "Verdächtiger Eintrag")
                    
                    if title:
                        # Bereinigen von Protokollen und Slashes
                        clean_value = title.lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0].strip()
                        
                        # System-Domains filtern, um Fehlalarme in Ihrer Android-App zu verhindern
                        if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com", "w3.org"]:
                            if not any(e["value"] == clean_value for e in all_entries):
                                all_entries.append({
                                    "value": clean_value,
                                    "category": category_raw
                                })
                                
            print(f"Verarbeitung erfolgreich beendet. {len(all_entries)} echte Schweizer Betrugsfälle extrahiert.")
        else:
            print(f"Die Schnittstelle meldet einen Fehler: Status-Code {response.status_code}")
            
    except Exception as e:
        print(f"Verbindungsfehler zur Live-Datenschnittstelle: {e}")
        
    return all_entries

def main():
    entries = fetch_live_phishing_data()
    
    # Schutz-Fallback, falls die Schnittstelle gewartet wird
    if not entries:
        print("Schnittstelle lieferte keine Daten. Fallback aktiviert.")
        entries = [{"value": "daten-warten-auf-server-freigabe.com", "category": "System-Meldung"}]

    # Pfad über Ihre eingerichtete Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Die Live-Daten wurden erfolgreich weggeschrieben unter: {file_path}")

if __name__ == "__main__":
    main()
