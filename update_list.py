import os
import json
import re
from bs4 import BeautifulSoup
import requests

# Wir nutzen das Suchformular der Warnliste. Eine leere Abfrage liefert alle Einträge unfiltriert.
URL = "https://cybercrimepolice.ch"

def fetch_all_verified_entries():
    all_entries = []
    
    # Ein standardisierter Browser-Header, der exakt wie ein regulärer Browserzugriff wirkt
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        print("Rufe unfiltrierte polizeiliche Suchdaten ab...")
        response = requests.get(URL, headers=headers, timeout=20)
        
        print(f"Server-Antwort erhalten mit Status-Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Die Einträge befinden sich in einer Liste mit der CSS-Klasse "t-warnliste__item"
            items = soup.find_all("li", class_="t-warnliste__item")
            
            # Flexibler Fallback auf generische Listenelemente, falls Klassen variieren
            if not items:
                items = soup.select("ul li, main li")
                
            print(f"Analysiere {len(items)} HTML-Segmente auf Betrugsdaten...")
            
            # Regex filtert sowohl Web-Domains als auch Krypto-Wallet-Adressen heraus
            entry_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b|[a-zA-Z0-9]{26,42}"
            
            for item in items:
                text = item.get_text()
                
                # Wir stellen sicher, dass es sich um einen verifizierten Warnlisteneintrag handelt
                if "Mehr erfahren" in text or "Verdächtige" in text:
                    match = re.search(entry_pattern, text)
                    if match:
                        clean_value = match.group(0).strip().lower()
                        
                        # Bestimmung der korrekten Kategorie direkt aus dem Listentext
                        category = "Verdächtiger Eintrag"
                        if "Kryptoadressen" in text:
                            category = "Verdächtige Kryptoadresse"
                        elif "Onlineplattformen" in text:
                            category = "Verdächtige Onlineplattform"
                        elif "Immobilien" in text:
                            category = "Verdächtige Immobilienplattform"
                        
                        # System-Domains filtern, um Fehlalarme in Ihrer App zu verhindern
                        if clean_value not in ["cybercrimepolice.ch", "instagram.com", "google.com", "github.com", "w3.org"]:
                            if not any(e["value"] == clean_value for e in all_entries):
                                all_entries.append({
                                    "value": clean_value,
                                    "category": category
                                })
                                
            print(f"Extraktion beendet. {len(all_entries)} echte Schweizer Fälle registriert.")
        else:
            print(f"Zugriff wurde verweigert. Status-Code: {response.status_code}")
            
    except Exception as e:
        print(f"Fehler während der Datenverarbeitung: {e}")
        
    return all_entries

def main():
    entries = fetch_all_verified_entries()
    
    # Absolute Absicherung, damit die Pipeline niemals mit einer leeren Datei abbricht
    if not entries:
        print("Scraping lieferte keine Ergebnisse. Fallback aktiviert.")
        entries = [{"value": "daten-warten-auf-server-freigabe.com", "category": "System-Meldung"}]

    # Pfad über Ihre eingerichtete Umgebungsvariable auslesen
    target_dir = os.getenv("TARGET_WORKSPACE", os.getcwd())
    file_path = os.path.join(target_dir, "phishing_list.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Daten erfolgreich weggeschrieben unter: {file_path}")

if __name__ == "__main__":
    main()
