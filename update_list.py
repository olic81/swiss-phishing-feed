import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Die Haupt-Warnliste ohne Kategorie-Einschränkung
BASE_URL = "https://cybercrimepolice.ch{}"

def fetch_all_verified_entries():
    all_entries = []
    page = 1
    # Max_pages schützt vor Endlosschleifen, falls der Server blockiert
    max_pages = 10 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    while page <= max_pages:
        url = BASE_URL.format(page)
        print(f"Lade verifizierte Einträge von Seite {page}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Seite {page} lieferte Fehler-Status: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li", class_="t-warnliste__item")
            
            # Flexible Fallbacks für abweichende Strukturen
            if not items:
                items = soup.select(".c-warnliste-item, tr, .entry")
                
            if not items:
                print("Keine weiteren Listeneinträge gefunden. Beende Durchlauf.")
                break
                
            # Regex erkennt sowohl Krypto-Wallets (längere alphanumerische Ketten) als auch reguläre Web-Domains
            entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
            page_added = 0
            
            for item in items:
                text = item.get_text()
                
                # Wir suchen nach der Domain oder Wallet-Adresse im Listeneintrag
                match = re.search(entry_pattern, text)
                if match:
                    clean_value = match.group(0).strip()
                    
                    # Erkennung der konkreten Kategorie im Textfeld
                    category = "Verdächtiger Eintrag"
                    if "Kryptoadressen" in text:
                        category = "Verdächtige Kryptoadresse"
                    elif "Onlineplattformen" in text:
                        category = "Verdächtige Onlineplattform"
                    elif "Immobilien" in text:
                        category = "Verdächtige Immobilienplattform"
                    
                    # System-Ausschluss zur Absicherung gegen Fehlalarme
                    if clean_value.lower() not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com"]:
                        if not any(e["value"] == clean_value for e in all_entries):
                            all_entries.append({
                                "value": clean_value,
                                "category": category
                            })
                            page_added += 1
            
            print(f"Seite {page}: {page_added} neue Einträge hinzugefügt.")
            if page_added == 0:
                break
                
            page += 1
            time.sleep(1.5) # Wichtige Pause, um die Server-Anfragen menschlich zu halten
            
        except Exception as e:
            print(f"Fehler auf Seite {page}: {e}")
            break
            
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    if not entries:
        entries = [{"value": "pipeline-daten-platzhalter.com", "category": "System-Meldung"}]

    # Pfad über Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Vollständige Liste erfolgreich gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
