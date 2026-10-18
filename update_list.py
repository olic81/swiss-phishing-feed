import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Die Basis-Such-URL der polizeilichen Warnliste
SEARCH_URL = "https://cybercrimepolice.ch{}"

def fetch_all_via_delayed_search():
    all_entries = []
    
    # Suchbegriffe generieren: '0', '1'...'9' und 'a', 'b'...'z'
    search_queries = [str(num) for num in range(10)] + [chr(letter) for letter in range(97, 123)]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8"
    }
    
    # Regex filtert Krypto-Wallets und Web-Domains heraus
    entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
    
    print(f"Starte verzögerten Suchlauf über {len(search_queries)} Suchanfragen...")
    
    for query in search_queries:
        url = SEARCH_URL.format(query)
        print(f"Sende Anfrage für Suchbegriff: '{query}'")
        
        try:
            # timeout=15 bricht die Anfrage ab, wenn der Server gar nicht reagiert
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                items = soup.find_all("li")
                query_added = 0
                
                for item in items:
                    text = item.get_text()
                    
                    # Verifiziert, dass es sich um einen Listeneintrag der Warnliste handelt
                    if "Mehr erfahren" in text or "Verdächtige" in text:
                        match = re.search(entry_pattern, text)
                        if match:
                            clean_value = match.group(0).strip().lower()
                            
                            # Kategorien zuweisen
                            category = "Verdächtige Onlineplattform"
                            if "kryptoadressen" in text.lower():
                                category = "Verdächtige Kryptoadresse"
                            elif "immobil" in text.lower():
                                category = "Verdächtige Immobilienplattform"
                            
                            # System-Domains blockieren
                            if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com"]:
                                if not any(e["value"] == clean_value for e in all_entries):
                                    all_entries.append({
                                        "value": clean_value,
                                        "category": category
                                    })
                                    query_added += 1
                                    
                print(f"➔ Begriff '{query}': {query_added} neue Treffer hinzugefügt.")
            else:
                print(f"Server meldet Blockade bei '{query}': Status {response.status_code}")
                
        except Exception as e:
            print(f"Fehler bei Abfrage '{query}': {e}")
            
        # HIER IST DAS GEWÜNSCHTE TIMEOUT: 
        # Wir warten nach JEDER Suchanfrage starr 3 Sekunden, um die Firewall zu schonen.
        print("Warte 3 Sekunden bis zur nächsten Anfrage...")
        time.sleep(3)
            
    return all_entries

def main():
    entries = fetch_all_via_delayed_search()
    
    if not entries:
        print("Suchdurchlauf lieferte keine Ergebnisse.")
        entries = [{"value": "timeout-warteschleife-aktiv.com", "category": "System-Meldung"}]

    # Speicherpfad über Ihre Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Abfrage beendet! {len(entries)} Einträge gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
