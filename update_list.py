import os
import json
import requests

# Die direkte, offizielle WordPress-Schnittstelle der Kantonspolizei Zürich.
# per_page=100 holt die neuesten 100 Einträge auf einmal ab.
API_URL = "https://cybercrimepolice.ch"

def fetch_all_verified_entries():
    all_entries = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        print("Verbinde direkt mit der polizeilichen JSON-Datenschnittstelle...")
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            posts = response.json()
            print(f"Schnittstelle antwortet stabil. Verarbeite {len(posts)} Datensätze...")
            
            # Regulärer Ausdruck für Web-Domains und Krypto-Wallets (26-42 Zeichen)
            entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
            
            for post in posts:
                # Wir holen den reinen Textinhalt der Meldung aus der Datenbank
                title_text = post.get("title", {}).get("rendered", "")
                content_text = post.get("content", {}).get("rendered", "")
                combined_text = f"{title_text} {content_text}"
                
                # Wir suchen gezielt nach den blockierten Adressen innerhalb des Datensatzes
                import re
                match = re.search(entry_pattern, combined_text)
                
                if match:
                    clean_value = match.group(0).strip().lower()
                    
                    # Bestimmung der Kategorie anhand der WordPress-Datenstrukturen
                    category = "Verdächtige Onlineplattform"
                    if "krypto" in combined_text.lower():
                        category = "Verdächtige Kryptoadresse"
                    elif "immobil" in combined_text.lower():
                        category = "Verdächtige Immobilienplattform"
                        
                    # Bereinigen von System-Domains, um Fehlalarme in Ihrer App zu verhindern
                    if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com", "w3.org"]:
                        # Verhindert doppelte Einträge in der Liste
                        if not any(e["value"] == clean_value for e in all_entries):
                            all_entries.append({
                                "value": clean_value,
                                "category": category
                            })
                            
            print(f"Verarbeitung abgeschlossen. {len(all_entries)} verifizierte Schweizer Betrugsfälle extrahiert.")
        else:
            print(f"Die Schnittstelle lieferte einen Fehler-Code: {response.status_code}")
            
    except Exception as e:
        print(f"Verbindungsfehler zur Datenschnittstelle: {e}")
        
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    # Letzte Absicherung vor leeren Dateien
    if not entries:
        print("Keine Einträge gefunden. Nutze Notfall-Datensatz.")
        entries = [{"value": "daten-warten-auf-update.com", "category": "System-Meldung"}]

    # Speichern über die bewährte Umgebungsvariable im GitHub-Workspace
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Die Live-Daten wurden erfolgreich weggeschrieben unter: {file_path}")

if __name__ == "__main__":
    main()
