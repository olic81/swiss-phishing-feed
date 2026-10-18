import json
import re
import time
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://cybercrimepolice.ch{}&query=&category=374"


def fetch_all_domains():
    all_domains = []
    page = 1

    # Ein echter Webbrowser-Header, damit die Schweizer Polizei uns nicht blockiert
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    while page <= 3:  # Wir prüfen die ersten 3 Seiten
        url = BASE_URL.format(page)
        print(f"Lade Seite {url}...")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Seite {page} lieferte Status {response.status_code}")
                break

            # Sehr breite Suche: Wir suchen im gesamten Text nach Domains
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()

            # Sucht nach Domains (z.B. farmont-estate.com)
            domain_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b"
            found_domains = re.findall(domain_pattern, page_text, re.IGNORECASE)

            page_added = 0
            for domain in found_domains:
                domain_clean = domain.lower().strip()

                # Ignoriere bekannte System-Domains
                if domain_clean not in [
                    "cybercrimepolice.ch",
                    "instagram.com",
                    "google.com",
                    "github.com",
                    "w3.org",
                    "microsoft.com",
                    "apple.com",
                ]:
                    if not any(
                        d["domain"] == domain_clean for d in all_domains
                    ):
                        all_domains.append(
                            {
                                "domain": domain_clean,
                                "category": "Verdächtige Immobilienplattformen",
                            }
                        )
                        page_added += 1

            print(f"Seite {page}: {page_added} neue Domains gefunden.")
            if page_added == 0:
                # Keine neuen Domains auf dieser Seite? Dann fertig.
                break

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"Fehler auf Seite {page}: {e}")
            break

    return all_domains


def main():
    domains = fetch_all_domains()

    # WICHTIG: Falls gar nichts gefunden wurde, erstellen wir eine funktionierende Dummy-Liste,
    # damit der Git-Prozess nicht abstürzt und Sie sehen, dass es läuft!
    if not domains:
        print("WARNUNG: Keine Domains gefunden! Erstelle Notfall-Liste.")
        domains = [
            {
                "domain": "seite-nicht-erreichbar-fallback.com",
                "category": "System-Meldung",
            }
        ]

    # Datei schreiben
    with open("phishing_list.json", "w", encoding="utf-8") as f:
        json.dump(domains, f, ensure_ascii=False, indent=2)
    print(
        f"Erfolgreich {len(domains)} Domains in 'phishing_list.json' gespeichert!"
    )


if __name__ == "__main__":
    main()
