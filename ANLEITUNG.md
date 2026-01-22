# WebShop Tracker Bot - Konfigurationsanleitung

## Überblick
Der Bot wurde überarbeitet und kann nun **mehrere Webshops gleichzeitig überwachen** ohne auf bestimmte Shop-spezifische Begriffe angewiesen zu sein. Er prüft **alle Produkte auf Verfügbarkeit**.

## Vorkonfigurierte Shops

Folgende Shops sind bereits vorkonfiguriert:

### ✅ White Rabbit (aktiv)
- URL: https://www.whiterabbit-cgs.de/shop/Booster-Displays_2
- Type: `white_rabbit`
- Status: Voll funktionsfähig

### ✅ World of TCG (aktiv)
- URL: https://worldoftcg.de/de/shop/one-piece?vorverkauf=true
- Type: `world_of_tcg`
- Status: Voll funktionsfähig

### ⚠️ Games Island (deaktiviert)
- URL: https://games-island.eu/c/Kartenspiele/One-Piece-TCG?qf=5
- Type: `games_island`
- Status: **Deaktiviert** - Die Website nutzt komplexes JavaScript, daher konnte keine automatische Konfiguration ermittelt werden
- **Aktivierung**: Um diesen Shop zu nutzen, musst du die CSS-Selektoren manuell ermitteln (siehe Punkt "CSS-Selektoren ermitteln" unten) und dann `"enabled": true` in der Konfiguration setzen.

### ✅ Yonko TCG (aktiv)
- URL: https://yonko-tcg.de/collections/one-piece-displays-deutsch-englisch
- Type: `yonko_tcg`
- Status: Voll funktionsfähig

## Shops hinzufügen / Konfigurieren

### 1. `shops_config.json` bearbeiten

Die Datei `shops_config.json` enthält die Konfiguration für alle zu überwachenden Shops. Hier ist ein Beispiel:

```json
{
  "shops": [
    {
      "name": "White Rabbit",
      "url": "https://www.whiterabbit-cgs.de/shop/Booster-Displays_2",
      "enabled": true,
      "selectors": {
        "products": "div.productbox-column",
        "name": "span.productbox-title",
        "price": "span.price",
        "status_ribbon": "div.ribbon"
      },
      "unavailable_indicators": {
        "status_values": ["Vorverkauf gestoppt", "Nicht verfügbar"],
        "text_patterns": ["momentan nicht verfügbar", "ausverkauft"]
      }
    }
  ]
}
```

### 2. Struktur der Shop-Konfiguration

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| `name` | Name des Shops (für Berichte) | `"White Rabbit"` |
| `url` | URL der zu überwachenden Seite | `"https://..."` |
| `enabled` | Aktiv/Inaktiv (true/false) | `true` |
| `selectors.products` | CSS-Selektor für Produkt-Container | `"div.productbox-column"` |
| `selectors.name` | CSS-Selektor für Produktname | `"span.productbox-title"` |
| `selectors.price` | CSS-Selektor für Preis | `"span.price"` |
| `selectors.status_ribbon` | CSS-Selektor für Status-Badge (optional) | `"div.ribbon"` |
| `unavailable_indicators.status_values` | Liste von Status-Texten, die "nicht verfügbar" bedeuten | `["Ausverkauft", "Nicht verfügbar"]` |
| `unavailable_indicators.text_patterns` | Text-Muster im Produkt, die "nicht verfügbar" bedeuten | `["ausverkauft", "nicht verfügbar"]` |

### 3. CSS-Selektoren ermitteln

Um die CSS-Selektoren für einen neuen Shop zu finden:

1. Öffne die Shop-Website im Browser
2. Drücke **F12** um Developer Tools zu öffnen
3. Nutze den **Element-Inspector** (Pfeilen-Symbol oben links)
4. Klicke auf ein Produktelement
5. Beachte den **CSS-Klassen** und **HTML-Struktur**:
   - Für alle Produkte: Suche eine wiederholte Klasse/ID (z.B. `class="product"`)
   - Für Produktname: Suche ein `<span>`, `<h2>`, `<a>` mit Produkttitel
   - Für Preis: Suche ein Element mit Preisangabe
   - Für Status: Suche ein Badge/Banner mit Status-Info

Beispiel CSS-Selektoren:
```
Alle Produkte:     "div.product-item" oder ".product" oder "[data-product-id]"
Produktname:       "h2.title" oder ".product-title" oder "a.product-link"
Preis:             "span.price" oder ".product-price" oder "[data-price]"
Status:            "span.badge" oder ".status-ribbon" oder ".stock-indicator"
```

### 4. Verfügbarkeitsindikatoren anpassen

Der Bot prüft automatisch auf:
- **Text-Muster**: Durchsucht den kompletten Produkttext nach Begriffen wie "ausverkauft", "nicht verfügbar", etc.
- **Status-Werte**: Vergleicht den Status-Text mit der Liste der "nicht verfügbar"-Indikatoren
- **Generische Muster**: Automatisch werden auch generische Begriffe wie "lagerbestand", "stock", "verfügbar nicht" geprüft

Du kannst weitere Muster hinzufügen:

```json
"unavailable_indicators": {
  "status_values": ["Ausverkauft", "Out of Stock", "Nicht verfügbar"],
  "text_patterns": ["ausverkauft", "out of stock", "nicht verfügbar", "temporarily unavailable"]
}
```

## Beispiele für neue Shops

### Beispiel 1: Einfacher Shop (wie White Rabbit)

```json
{
  "name": "MeinShop",
  "url": "https://example.com/products",
  "enabled": true,
  "selectors": {
    "products": "div.product",
    "name": "h3.product-title",
    "price": "span.price",
    "status_ribbon": "span.badge"
  },
  "unavailable_indicators": {
    "status_values": ["Out of Stock"],
    "text_patterns": ["out of stock", "sold out"]
  }
}
```

### Beispiel 2: Shop mit Data-Attributen

```json
{
  "name": "DataShop",
  "url": "https://example.com/catalog",
  "enabled": true,
  "selectors": {
    "products": "[data-product-id]",
    "name": "[data-product-name]",
    "price": "[data-product-price]",
    "status_ribbon": "[data-stock-status]"
  },
  "unavailable_indicators": {
    "status_values": ["inactive", "unavailable"],
    "text_patterns": ["not available", "coming soon"]
  }
}
```

## Bot ausführen

```bash
python bot.py
```

### Automatische Ausführung (Windows Task Scheduler)

Erstelle eine Batch-Datei `run_bot.bat`:

```batch
@echo off
cd C:\Users\SPA\Projects\WebShopTracker
python bot.py
```

Und planen Sie sie im **Task Scheduler** (z.B. alle 30 Minuten).

## Features des überarbeiteten Bots

✅ **Multi-Shop-Unterstützung**: Überwache mehrere Webshops gleichzeitig  
✅ **Flexible Verfügbarkeitserkennung**: Nicht beschränkt auf "White Rabbit"-spezifische Begriffe  
✅ **Automatische Indikatoren**: Erkennt automatisch häufige "nicht verfügbar"-Muster  
✅ **Email-Benachrichtigungen**: Benachrichtigungen mit Shop-Namen und direktem Link  
✅ **Änderungsverfolgung**: Neue Artikel, Preisänderungen, Statusänderungen, Verfügbarkeitswechsel  
✅ **Einfache Aktivierung/Deaktivierung**: Shops mit `"enabled": false` werden ignoriert

## Fehlerbehebung

**Problem**: "Selektoren finden keine Produkte"
- Überprüfe die CSS-Selektoren mit F12 Developer Tools
- Achte auf Leerzeichen und genaue Schreibweise
- Manche Shops laden Inhalte asynchron - der Bot wartet 2 Sekunden, aber das kann manchmal nicht ausreichen

**Problem**: "Verfügbarkeit wird nicht korrekt erkannt"
- Füge mehr Text-Muster zu `unavailable_indicators.text_patterns` hinzu
- Überprüfe die genauen Begriffe auf der Website (Grossschreibung, Leerzeichen)
- Aktiviere Debug-Ausgabe um zu sehen, was erkannt wird

**Problem**: "Email wird nicht gesendet"
- Überprüfe `.env` Datei mit korrekten Anmeldedaten
- Nutze ein **App-Passwort** statt Dein normales Gmail-Passwort
- Siehe: https://myaccount.google.com/apppasswords

## Weitere Anpassungsmöglichkeiten

Du kannst den Bot weiter anpassen:

1. **Prüfintervall**: Ändere den Scheduler/Task um den Bot häufiger/seltener auszuführen
2. **Benachrichtigungen**: Modifiziere die `send_email()` Funktion
3. **Datenspeicherung**: Ändere die `save_products()` und `load_previous_products()` Funktionen um z.B. eine Datenbank zu nutzen
4. **Filterung**: Füge Filter hinzu um nur bestimmte Produkte zu überwachen

Viel Erfolg! 🚀
