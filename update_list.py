#!/usr/bin/env python3
"""
Wöchentliches Update: Lädt Seite 1 jeder Kategorie und fügt
nur neue Einträge zu den bestehenden JSON-Dateien hinzu.
"""
import json, urllib.request, re, os

BASE = "https://cybercrimepolice.ch/de/warnliste?page=1&query=&category={cat}"
FILES = {
    "373": ("warnliste_cryptoadressen.json", "Verdächtige Kryptoadressen"),
    "374": ("warnliste_immobilienplattformen.json", "Verdächtige Immobilienplattformen"),
    "375": ("warnliste_onlineplattformen.json", "Verdächtige Onlineplattformen"),
}

def fetch_page(cat):
    url = BASE.format(cat=cat)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Fehler beim Laden von Kategorie {cat}: {e}")
        return ""

def extract_entries(html, category_name):
    # Extrahiert alle Einträge aus der HTML-Seite (Seite 1)
    # Muster: c-warnlist-item__heading ... </p>
    results = []
    pattern = re.compile(r'c-warnlist-item__heading[^"]*>(.*?)</p>', re.DOTALL)
    for m in pattern.finditer(html):
        addr = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        addr = " ".join(addr.split())
        if len(addr) > 2:
            results.append({"value": addr, "category": category_name})
    # Deduplizieren
    seen = []
    for r in results:
        if not any(s["value"] == r["value"] for s in seen):
            seen.append(r)
    return seen

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for cat, (filename, category_name) in FILES.items():
        path = os.path.join(script_dir, filename)
        # Bestehende Daten laden
        existing = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        # Seite 1 laden
        html = fetch_page(cat)
        if not html:
            continue
        new_entries = extract_entries(html, category_name)
        # Nur neue hinzufügen
        existing_values = {e["value"] for e in existing}
        added = 0
        for entry in new_entries:
            if entry["value"] not in existing_values:
                existing.append(entry)
                existing_values.add(entry["value"])
                added += 1
        # Speichern
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"Kategorie {cat} ({category_name}): {len(existing)} Einträge gesamt (+{added} neu) -> {filename}")

if __name__ == "__main__":
    main()
