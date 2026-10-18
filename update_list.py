import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Basis-URL für das Durchblättern der Seiten
BASE_URL = "https://cybercrimepolice.ch{}"

def fetch_all_verified_entries():
    all_entries = []
    page = 1
    # Wir laden für den Anfang die ersten 5 Seiten (ca. 100 topaktuelle Einträge)
    # Sie können die Zahl erhöhen, wenn die App im Testlauf stabil bleibt
    max_pages = 5 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    while page <= max_pages:
        url = BASE_URL.format(page)
        print(f"Lade Seite {page} von {max_pages}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                print(f"Abbruch: Seite {page} nicht erreichbar (Status {response.status_code})")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li", class_="t-warnliste__item")
            
            if not items:
                print(f"Keine Einträge auf Seite {page} gefunden. Beende Suche.")
                break
                
            page_added = 0
            for item in items:
                text = item.get_text()
                
                if "Mehr erfahren" in text:
                    # Verbesserter Regex: Extrahiert alles vor dem Datum (die eigentliche Domain oder Wallet)
                    # Trennt den Text sauber beim ersten vorkommenden Datum auf
                    parts = re.split(r'\s\d{2}\.\d{2}\.\d{4}', text)
                    if parts:
                        # Bereinigen von Listenzeichen am Anfang
                        clean_value = parts[0].replace("-", "").strip().lower()
                        
                        # Kategorisierung bestimmen
                        category = "Verdächtiger Eintrag"
                        if "Kryptoadressen" in text:
                            category = "Verdächtige Kryptoadresse"
                        elif "Onlineplattformen" in text:
                            category = "Verdächtige Onlineplattform"
                        elif "Immobilien" in text:
                            category = "Verdächtige Immobilienplattform"
                        
                        # System-Domains filtern
                        if clean_value and clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com"]:
                            if not any(e["value"] == clean_value for e in all_entries):
                                all_entries.append({
                                    "value": clean_value,
                                    "category": category
                                })
                                page_added += 1
                                
            print(f"Seite {page}: {page_added} Einträge erfolgreich extrahiert.")
            
            # Wichtig: Dem Server Pausen gönnen, um nicht blockiert zu werden
            page += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"Fehler auf Seite {page}: {e}")
            break
            
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    if not entries:
        entries = [{"value": "daten-warten-auf-update.com", "category": "System-Meldung"}]

    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Insgesamt {len(entries)} Einträge gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
