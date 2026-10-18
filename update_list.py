import json
import time
from bs4 import BeautifulSoup
import requests

# Basis-URL von Cybercrimepolice.ch
BASE_URL = "https://cybercrimepolice.ch{}&query=&category=374"


def fetch_all_domains():
    all_domains = []
    page = 1

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    while True:
        url = BASE_URL.format(page)
        print(f"Lade Seite {page}...")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Seite {page} nicht erreichbar. Breche ab.")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Cybercrimepolice listet die Einträge in einer Liste/Tabelle auf.
            # Wir suchen gezielt nach den Text-Inhalten der Einträge.
            items = soup.find_all("li", class_="t-warnliste__item")

            # Falls das Layout leicht abweicht, nutzen wir einen flexiblen Fallback auf die Links im Inhaltsbereich
            if not items:
                items = soup.select(".c-warnliste-item, tr, .entry")

            if not items:
                # Keine weiteren Einträge gefunden (Ende der Liste erreicht)
                break

            page_added = 0
            for item in items:
                text = item.get_text()
                # Sucht nach typischen Domain-Formaten (z.B. "farmont-estate.com")
                import re

                match = re.search(
                    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}\b",
                    text,
                    re.IGNORECASE,
                )

                if match:
                    domain = match.group(0).lower().strip()
                    # Ignoriere System-Domains
                    if domain not in [
                        "cybercrimepolice.ch",
                        "instagram.com",
                        "google.com",
                    ]:
                        if not any(
                            d["domain"] == domain for d in all_domains
                        ):
                            all_domains.append(
                                {
                                    "domain": domain,
                                    "category": "Verdächtige Immobilienplattformen",
                                }
                            )
                            page_added += 1

            if page_added == 0:
                # Wenn auf einer Seite gar keine neuen Domains mehr extrahiert werden konnten, stoppen wir
                break

            page += 1
            time.sleep(1)  # Kurze Pause, um den Server nicht zu überlasten

        except Exception as e:
            print(f"Fehler auf Seite {page}: {e}")
            break

    return all_domains


def main():
    domains = fetch_all_domains()

    if domains:
        with open("phishing_list.json", "w", encoding="utf-8") as f:
            json.dump(domains, f, ensure_ascii=False, indent=2)
        print(
            f"Erfolgreich {len(domains)} Domains in 'phishing_list.json' gespeichert!"
        )
    else:
        print("Keine Domains gefunden. Datei wird nicht überschrieben.")


if __name__ == "__main__":
    main()
