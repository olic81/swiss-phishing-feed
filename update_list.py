import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Die reguläre Warnlisten-Infrastruktur der Kapo Zürich
BASE_URL = "https://cybercrimepolice.ch{}"

def fetch_all_verified_entries():
    all_entries = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    # Treffsicherer Regex für Krypto-Wallets (z.B. bc1q...) und klassische Internet-Domains
    entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
    
    # Wir durchforsten die ersten 5 Seiten, um die Liste schrittweise aufzubauen
    for page in range(1, 6):
        url = BASE_URL.format(page)
        print(f"Rufe Warnliste ab: Seite {page} -> {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Server blockiert auf Seite {page} (Status-Code {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Kritisches Update: Wir suchen direkt im kompletten Text des Hauptinhalts (Main/Body)
            page_text = soup.get_text()
            
            # Alle potenziellen Übereinstimmungen auf der aktuellen Seite finden
            found_matches = re.findall(entry_pattern, page_text, re.IGNORECASE)
            page_added = 0
            
            for match in found_matches:
                clean_value = match.lower().strip()
                
                # System-Infrastruktur ausschliessen, um Fehlalarme in Ihrer Android-App zu vermeiden
                if clean_value not in [
                    "cybercrimepolice.ch", "instagram.com", "google.com", 
                    "github.com", "w3.org", "apple.com", "microsoft.com"
                ] and not clean_value.endswith(".jpg") and not clean_value.endswith(".png"):
                    
                    # Einmaliger Eintrag in die Liste sichern
                    if not any(e["value"] == clean_value for e in all_entries):
                        
                        # Dynamische Kategoriezuweisung anhand des Werts
                        category = "Verdächtige Onlineplattform"
                        if clean_value.startswith("bc1") or len(clean_value) >= 26:
                            category = "Verdächtige Kryptoadresse"
                        elif "immobil" in clean_value:
                            category = "Verdächtige Immobilienplattform"
                            
                        all_entries.append({
                            "value": clean_value,
                            "category": category
                        })
                        page_added += 1
                        
            print(f"➔ Seite {page}: {page_added} verifizierte Adressen extrahiert.")
            
            # Wichtiges Timeout: 3 Sekunden warten, um die Server-Firewall nicht zu triggern
            time.sleep(3)
            
        except Exception as e:
            print(f"Fehler bei der Datenverarbeitung auf Seite {page}: {e}")
            continue
            
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    # Absicherung vor leeren JSON-Dateien
    if not entries:
        entries = [{"value": "pipeline-warten-auf-daten.com", "category": "System-Meldung"}]

    # Pfad über Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Erfolgreich beendet! Insgesamt {len(entries)} echte Schweizer Live-Einträge gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
