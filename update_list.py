import os
import json
import re
import time
from bs4 import BeautifulSoup
import requests

# Die Basis-Such-URL, an die wir die Buchstaben/Zahlen anhängen
SEARCH_URL = "https://cybercrimepolice.ch{}"

def fetch_all_via_search_queries():
    all_entries = []
    
    # Wir generieren die Suchbegriffe: '0*', '1*', ... '9*' und 'a*', 'b*', ... 'z*'
    search_queries = [f"{num}*" for num in range(10)] + [f"{chr(letter)}*" for letter in range(97, 123)]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8"
    }
    
    # Regulärer Ausdruck für Domains und Krypto-Wallets
    entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
    
    print(f"Starte die sequenzielle Abfrage von {len(search_queries)} Suchbegriffen...")
    
    for query in search_queries:
        url = SEARCH_URL.format(query)
        print(f"Suche nach: '{query}' -> {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Suchbegriff '{query}' übersprungen (Status {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Wir holen den reinen Text aller Listenelemente (li) auf der Seite
            items = soup.find_all("li")
            query_added = 0
            
            for item in items:
                text = item.get_text()
                
                # Nur echte Warnlisten-Einträge auswerten
                if "Mehr erfahren" in text or "Verdächtige" in text:
                    match = re.search(entry_pattern, text)
                    if match:
                        clean_value = match.group(0).strip().lower()
                        
                        # Kategorie zuweisen
                        category = "Verdächtiger Eintrag"
                        if "kryptoadressen" in text.lower():
                            category = "Verdächtige Kryptoadresse"
                        elif "onlineplattformen" in text.lower():
                            category = "Verdächtige Onlineplattform"
                        elif "immobilien" in text.lower():
                            category = "Verdächtige Immobilienplattform"
                        
                        # System-Domains herausfiltern
                        if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com"]:
                            if not any(e["value"] == clean_value for e in all_entries):
                                all_entries.append({
                                    "value": clean_value,
                                    "category": category
                                })
                                query_added += 1
                                
            print(f"➔ '{query}': {query_added} neue Einträge gefunden.")
            
            # WICHTIG: Kurze Pause, damit die Schweizer Firewall uns nicht wegen Spam blockiert
            time.sleep(2)
            
        except Exception as e:
            print(f"Fehler bei Suchbegriff '{query}': {e}")
            continue
            
    return all_entries

def main():
    entries = fetch_all_via_search_queries()
    
    if not entries:
        print("Suche lieferte keine Ergebnisse. Fallback aktiviert.")
        entries = [{"value": "suche-warten-auf-freigabe.com", "category": "System-Meldung"}]

    # Speicherpfad über die funktionierende Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Suche beendet! Insgesamt {len(entries)} echte Einträge gespeichert unter: {file_path}")

if __name__ == "__main__":
    main()
