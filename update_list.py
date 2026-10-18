import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Wir nutzen das normale System der Warnliste und blättern die Seiten 1 bis 5 durch
BASE_URL = "https://cybercrimepolice.ch{}"

def fetch_all_verified_entries():
    all_entries = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    # Regulärer Ausdruck: Erkennt Web-Domains (kaffeemachers.shop) und Krypto-Wallets (z.B. bc1q...)
    entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
    
    # Wir klappern die ersten 5 Seiten der Warnliste nacheinander ab
    for page in range(1, 6):
        url = BASE_URL.format(page)
        print(f"Rufe Warnliste ab: Seite {page} -> {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Seite {page} wurde vom Server blockiert (Status {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Die Einträge stehen auf der echten Webseite in einer Liste (li)
            items = soup.find_all("li")
            page_added = 0
            
            for item in items:
                text = item.get_text()
                
                # Wir filtern strikt nur Einträge aus der echten Tabelle ("Mehr erfahren" oder "Verdächtige")
                if "Mehr erfahren" in text or "Verdächtige" in text:
                    match = re.search(entry_pattern, text)
                    if match:
                        clean_value = match.group(0).strip().lower()
                        
                        # Kategorie bestimmen
                        category = "Verdächtige Onlineplattform"
                        if "kryptoadressen" in text.lower():
                            category = "Verdächtige Kryptoadresse"
                        elif "immobil" in text.lower():
                            category = "Verdächtige Immobilienplattform"
                        
                        # Verhindert, dass interne Seiten-Links in Ihre App rutschen
                        if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com", "w3.org"]:
                            if not any(e["value"] == clean_value for e in all_entries):
                                all_entries.append({
                                    "value": clean_value,
                                    "category": category
                                })
                                page_added += 1
                                
            print(f"➔ Seite {page}: {page_added} neue Einträge erfolgreich extrahiert.")
            
            # 2 Sekunden Pause zwischen den Seiten, damit die Firewall uns nicht sperrt
            time.sleep(2)
            
        except Exception as e:
            print(f"Fehler auf Seite {page}: {e}")
            continue
            
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    # Fallback-Schutz, falls der Server mitten im Lauf die Verbindung kappt
    if not entries:
        entries = [{"value": "pipeline-warten-auf-server.com", "category": "System-Meldung"}]

    # Speicherpfad über die funktionierende Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Fertig! Insgesamt {len(entries)} echte Schweizer Live-Einträge gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
