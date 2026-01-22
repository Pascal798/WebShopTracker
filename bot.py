import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import urllib3
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

urllib3.disable_warnings()

# Konfiguration
SHOPS_CONFIG_FILE = "shops_config.json"
PRODUCTS_FILE = "products.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Email Konfiguration
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
RECIPIENT_EMAIL = "PascalStephan2016@gmail.com"

def load_shops_config():
    """Lade die Shop-Konfiguration aus der Datei"""
    if os.path.exists(SHOPS_CONFIG_FILE):
        with open(SHOPS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Default-Konfiguration erstellen, wenn Datei nicht existiert
        default_config = {
            "shops": [
                {
                    "name": "White Rabbit",
                    "url": "https://www.whiterabbit-cgs.de/shop/Booster-Displays_2",
                    "enabled": True,
                    "selectors": {
                        "products": "div.productbox-column",
                        "name": "span.productbox-title",
                        "price": "span.price",
                        "status_ribbon": "div.ribbon",
                        "availability_text": ["momentan nicht verfügbar", "ausverkauft", "nicht auf lager"]
                    },
                    "unavailable_indicators": {
                        "status_values": ["Vorverkauf gestoppt", "Nicht verfügbar"],
                        "text_patterns": ["momentan nicht verfügbar", "ausverkauft"]
                    }
                }
            ]
        }
        # Speichere die Standard-Konfiguration
        with open(SHOPS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config

def get_products_from_shop(shop_config):
    """Fetche alle Produkte von einem Shop mit JavaScript-Rendering"""
    try:
        url = shop_config["url"]
        selectors = shop_config["selectors"]
        unavailable_indicators = shop_config.get("unavailable_indicators", {})
        shop_type = shop_config.get("type", "generic")  # white_rabbit oder world_of_tcg
        
        print(f"  🔍 Prüfe: {shop_config['name']}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            
            # Warte auf Produkte
            import time
            time.sleep(3)  # Erhöht auf 3 Sekunden für JS-basierte Shops
            
            # Hole den HTML-Content nach JavaScript-Rendering
            content = page.content()
            browser.close()
        
        soup = BeautifulSoup(content, "html.parser")
        
        products = []
        product_divs = soup.select(selectors["products"])
        
        print(f"    ℹ️ {len(product_divs)} Produkt-Container gefunden")
        
        for product in product_divs:
            try:
                # Speziallogik je nach Shop-Typ
                if shop_type == "world_of_tcg":
                    extracted = _extract_worldoftcg_product(product, url, shop_config)
                    if extracted:
                        products.extend(extracted)
                elif shop_type == "white_rabbit":
                    extracted = _extract_whiterabbit_product(product, url, shop_config)
                    if extracted:
                        products.append(extracted)
                elif shop_type == "games_island":
                    extracted = _extract_games_island_product(product, url, shop_config)
                    if extracted:
                        products.append(extracted)
                elif shop_type == "yonko_tcg":
                    extracted = _extract_yonko_product(product, url, shop_config)
                    if extracted:
                        products.append(extracted)
                else:
                    # Standard Extraktionslogik für andere Shops
                    prod = _extract_generic_product(product, url, shop_config)
                    if prod:
                        products.append(prod)
            except Exception as e:
                print(f"      ❌ Fehler bei Produktextraktion: {e}")
                continue
        
        return products
    except Exception as e:
        print(f"  ❌ Fehler beim Abrufen von {shop_config.get('name', 'Shop')}: {e}")
        return []

def _extract_generic_product(product, url, shop_config):
    """Extrahiere Produkt mit generischen Selektoren"""
    selectors = shop_config["selectors"]
    unavailable_indicators = shop_config.get("unavailable_indicators", {})
    
    # Extrahiere Produktname
    name_elem = product.select_one(selectors["name"])
    name = name_elem.get_text(strip=True) if name_elem else None
    
    # Extrahiere Preis
    price_elem = product.select_one(selectors["price"])
    price = price_elem.get_text(strip=True) if price_elem else None
    
    # Extrahiere Status (Ribbon/Badge)
    status = "Verfügbar"  # Default-Status
    if selectors.get("status_ribbon"):
        ribbon = product.select_one(selectors["status_ribbon"])
        if ribbon:
            ribbon_text = ribbon.get_text(strip=True)
            if ribbon_text:
                status = ribbon_text
    
    # Prüfe Verfügbarkeit
    product_text = product.get_text().lower()
    is_available = True
    
    # Prüfe auf Verfügbarkeitsindikatoren (Text-Muster)
    unavailable_texts = unavailable_indicators.get("text_patterns", [])
    for pattern in unavailable_texts:
        if pattern.lower() in product_text:
            is_available = False
            break
    
    # Prüfe auf Status-Indikatoren
    unavailable_statuses = unavailable_indicators.get("status_values", [])
    if status in unavailable_statuses:
        is_available = False
    
    # Generische Muster
    out_of_stock_patterns = ["lagerbestand", "stock", "verfügbar nicht", "nicht verfügbar", "verkauft"]
    for pattern in out_of_stock_patterns:
        if pattern in product_text:
            is_available = False
            break
    
    # Nur hinzufügen, wenn Name und Preis vorhanden
    if name and price:
        return {
            "name": name,
            "price": price,
            "status": status,
            "available": is_available,
            "url": url,
            "shop": shop_config["name"]
        }
    return None

def _extract_whiterabbit_product(product, url, shop_config):
    """Spezielle Extraktionslogik für White Rabbit"""
    unavailable_indicators = shop_config.get("unavailable_indicators", {})
    
    # White Rabbit nutzt Image-Alt-Text für den Produktnamen
    img = product.select_one('img')
    if not img:
        return None
    
    name = img.get('alt', '').strip()
    # Entferne das "..." am Ende
    if name.endswith('...'):
        name = name[:-3].strip()
    
    if not name:
        return None
    
    # Finde den Preis - Alle Spans durchsuchen die € enthalten
    price = None
    for span in product.select('span'):
        text = span.get_text(strip=True)
        if '€' in text:
            price = text
            break
    
    if not price:
        return None
    
    # Finde Status
    status = "Verfügbar"
    ribbon = product.select_one('div.ribbon')
    if ribbon:
        ribbon_text = ribbon.get_text(strip=True)
        if ribbon_text:
            status = ribbon_text
    
    # Prüfe Verfügbarkeit
    product_text = product.get_text().lower()
    is_available = True
    
    # Prüfe auf Verfügbarkeitsindikatoren
    unavailable_texts = unavailable_indicators.get("text_patterns", [])
    for pattern in unavailable_texts:
        if pattern.lower() in product_text:
            is_available = False
            break
    
    # Prüfe auf Status-Indikatoren
    unavailable_statuses = unavailable_indicators.get("status_values", [])
    if status in unavailable_statuses:
        is_available = False
    
    # Generische Muster
    out_of_stock_patterns = ["lagerbestand", "stock", "verfügbar nicht", "nicht verfügbar", "verkauft"]
    for pattern in out_of_stock_patterns:
        if pattern in product_text:
            is_available = False
            break
    
    return {
        "name": name,
        "price": price,
        "status": status,
        "available": is_available,
        "url": url,
        "shop": shop_config["name"]
    }

def _extract_games_island_product(product, url, shop_config):
    """Spezielle Extraktionslogik für Games Island"""
    unavailable_indicators = shop_config.get("unavailable_indicators", {})
    
    # Games Island ist sehr komplex strukturiert - versuche generisch zu extrahieren
    
    # Name: Suche nach Links
    name_elem = product.select_one('a')
    if not name_elem:
        return None
    name = name_elem.get_text(strip=True)
    if not name or name.isspace():
        return None
    
    # Preis: Suche nach Preis-Information
    price = None
    for span in product.select('span'):
        text = span.get_text(strip=True)
        if ',' in text and any(c.isdigit() for c in text) and ('€' in text or any(c.isdigit() for c in text.split(',')[0])):
            price = text
            break
    
    # Falls kein Preis mit Komma, versuche andere Formate
    if not price:
        for elem in product.find_all(['strong', 'span']):
            text = elem.get_text(strip=True)
            if any(char.isdigit() for char in text):
                price = text
                break
    
    if not price:
        return None
    
    # Status
    status = "Verfügbar"
    status_elem = product.select_one('[class*="status"], [class*="stock"]')
    if status_elem:
        status = status_elem.get_text(strip=True)
    
    # Verfügbarkeit
    product_text = product.get_text().lower()
    is_available = True
    
    # Prüfe auf Verfügbarkeitsindikatoren
    unavailable_texts = unavailable_indicators.get("text_patterns", [])
    for pattern in unavailable_texts:
        if pattern.lower() in product_text:
            is_available = False
            break
    
    # Prüfe auf Status-Indikatoren
    unavailable_statuses = unavailable_indicators.get("status_values", [])
    if status in unavailable_statuses:
        is_available = False
    
    return {
        "name": name[:150],  # Begrenze auf 150 Zeichen
        "price": price,
        "status": status,
        "available": is_available,
        "url": url,
        "shop": shop_config["name"]
    }

def _extract_worldoftcg_product(product, url, shop_config):
    """Spezielle Extraktionslogik für World of TCG"""
    products = []
    
    # World of TCG hat komplexe verschachtelte Struktur
    # Der Produktname setzt sich aus mehreren Teilen zusammen:
    # 1. Ein Link mit Klasse "artikel-name" der den Arikel-Code und Datum enthält
    # 2. Ein span mit Klasse "text-muted" der den Produktnamen enthält
    
    # Finde den Artikel-Namen-Link
    name_link = product.select_one('a.artikel-name')
    name_span = product.select_one('span.text-muted')
    
    if not name_link or not name_span:
        return products
    
    # Extrahiere die Komponenten
    # Name-Link enthält: "[Ausverkauft] OP-15 [EN] [VORVERKAUF - 03.04.2026]"
    # Name-Span enthält: "One Piece - Display"
    
    link_text = name_link.get_text(strip=True)
    span_text = name_span.get_text(strip=True)
    
    # Bereinige den Link-Text von Status-Markern
    link_text_clean = link_text.replace('[Ausverkauft]', '').strip()
    
    # Kombiniere beide zu einem vollständigen Produktnamen
    name_text = f"{link_text_clean} - {span_text}" if link_text_clean and span_text else (link_text_clean or span_text)
    
    if not name_text:
        return products
    
    # Finde den Preis - suche nach span mit €
    price_text = None
    for span in product.select('span'):
        text = span.get_text(strip=True)
        if '€' in text:
            price_text = text
            break
    
    if not price_text:
        return products
    
    # Prüfe Verfügbarkeit
    product_text = product.get_text()
    is_available = True
    
    # Prüfe auf "Ausverkauft"
    if '- Ausverkauft -' in product_text or '[Ausverkauft]' in product_text:
        is_available = False
    
    # Finde Status
    status = "Verfügbar"
    labels = product.select('.artikel-label')
    status_list = []
    for label in labels:
        label_text = label.get_text(strip=True)
        # Überspringe die Sprachen-Bilder und leere Labels
        if label_text and label_text not in ['Neu', '']:
            status_list.append(label_text)
    
    if status_list:
        status = ", ".join(status_list)
    
    products.append({
        "name": name_text.strip(),
        "price": price_text,
        "status": status,
        "available": is_available,
        "url": url,
        "shop": shop_config["name"]
    })
    
    return products

def _extract_yonko_product(product, url, shop_config):
    """Spezielle Extraktionslogik für Yonko TCG"""
    unavailable_indicators = shop_config.get("unavailable_indicators", {})
    
    # Name aus img alt-text
    img = product.select_one('img')
    if not img:
        return None
    
    name = img.get('alt', '').strip()
    if not name:
        return None
    
    # Preis: Suche nach €
    price = None
    text_content = product.get_text()
    for word in text_content.split():
        if '€' in word:
            price = word
            break
    
    # Falls Preis noch nicht gefunden, versuche anders
    if not price:
        import re
        price_match = re.search(r'€[\d,\.]+', text_content)
        if price_match:
            price = price_match.group(0)
    
    if not price:
        return None
    
    # Verfügbarkeit: Suche nach sold-out-badge oder "Ausverkauft" Text
    is_available = True
    if product.select_one('sold-out-badge'):
        is_available = False
    
    # Prüfe auch auf Text-Muster
    product_text = product.get_text().lower()
    unavailable_texts = unavailable_indicators.get("text_patterns", [])
    for pattern in unavailable_texts:
        if pattern.lower() in product_text:
            is_available = False
            break
    
    # Finde Link für URL
    link = product.select_one('a')
    product_url = link.get('href', url) if link else url
    # Falls relative URL, mache sie absolut
    if product_url.startswith('/'):
        product_url = 'https://yonko-tcg.de' + product_url
    
    status = "Ausverkauft" if not is_available else "Verfügbar"
    
    return {
        "name": name[:150],
        "price": price,
        "status": status,
        "available": is_available,
        "url": product_url,
        "shop": shop_config["name"]
    }

def get_all_products():
    """Fetche Produkte von allen konfigurierten Shops"""
    shops_config = load_shops_config()
    all_products = []
    
    for shop in shops_config.get("shops", []):
        if shop.get("enabled", True):
            products = get_products_from_shop(shop)
            all_products.extend(products)
    
    return all_products

def load_previous_products():
    """Lade die vorherigen Produkte aus der Datei"""
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", [])
    return []

def save_products(products):
    """Speichere die aktuellen Produkte"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "count": len(products),
        "products": products
    }
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_new_products(current, previous):
    """Finde neue Produkte"""
    current_names = {p["name"] for p in current}
    previous_names = {p["name"] for p in previous}
    new_names = current_names - previous_names
    return [p for p in current if p["name"] in new_names]

def find_price_changes(current, previous):
    """Finde Preisänderungen"""
    previous_dict = {p["name"]: p["price"] for p in previous}
    changes = []
    for product in current:
        if product["name"] in previous_dict:
            if previous_dict[product["name"]] != product["price"]:
                changes.append({
                    "name": product["name"],
                    "old_price": previous_dict[product["name"]],
                    "new_price": product["price"]
                })
    return changes

def find_status_changes(current, previous):
    """Finde Statusänderungen"""
    previous_dict = {p["name"]: p.get("status", "Neu") for p in previous}
    changes = []
    for product in current:
        old_status = previous_dict.get(product["name"])
        if old_status and old_status != product.get("status", "Neu"):
            changes.append({
                "name": product["name"],
                "old_status": old_status,
                "new_status": product.get("status", "Neu")
            })
    return changes

def find_availability_changes(current, previous):
    """Finde Änderungen der Verfügbarkeit (momentan nicht verfügbar)"""
    previous_dict = {p["name"]: p.get("available", True) for p in previous}
    changes = []
    for product in current:
        old_available = previous_dict.get(product["name"])
        if old_available is not None and old_available != product.get("available", True):
            changes.append({
                "name": product["name"],
                "price": product.get("price", "N/A"),
                "was_available": old_available,
                "now_available": product.get("available", True)
            })
    return changes

def send_email(product_name, product_price, shop_name, product_url):
    """Sende eine Email-Benachrichtigung für ein einzelnes Produkt (veraltet)"""
    # Diese Funktion wird nicht mehr verwendet - siehe send_available_products_email
    pass

def send_available_products_email(available_products):
    """Sende eine Email mit allen verfügbaren Artikeln"""
    try:
        if not GMAIL_ADDRESS or not GMAIL_PASSWORD:
            print("⚠️ Email-Konfiguration nicht gesetzt - überspringe Email")
            return False
        
        if not available_products:
            print("    ℹ️ Keine verfügbaren Artikel zum Versenden")
            return False
        
        print(f"    📧 Sende Email mit {len(available_products)} verfügbaren Artikel(n)...")
        
        # Erstelle die Email
        subject = f"✓ {len(available_products)} verfügbare Artikel gefunden!"
        
        # Erstelle die Produktliste
        products_html = ""
        for product in available_products:
            products_html += f"""
  • {product['name']}
    Preis: {product['price']}
    Shop: {product['shop']}
    Link: {product['url']}
"""
        
        body = f"""
Hallo,

bei der Überprüfung der Webshops wurden {len(available_products)} verfügbare Artikel gefunden:

{products_html}

Schau schnell vorbei, bevor sie wieder ausverkauft sind!

---
WebShop Tracker Bot
Überprüfung: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        # Verbindung zum SMTP Server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        
        # Email versenden
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        server.send_message(msg)
        server.quit()
        
        print(f"    ✉️ Email versendet an {RECIPIENT_EMAIL}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("    ❌ Email-Fehler: Authentifizierung fehlgeschlagen")
        print("       Bitte überprüfe:")
        print("       - GMAIL_ADDRESS und GMAIL_PASSWORD in .env")
        print("       - Verwende ein App-Passwort (nicht dein normales Gmail-Passwort)")
        print("       - Quelle: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"    ❌ Email-Fehler: {e}")
        return False

# Hauptprogramm
print("🔍 Prüfe Webshops...")
current_products = get_all_products()
previous_products = load_previous_products()

print(f"\n📊 Aktuelle Produkte: {len(current_products)}")
print(f"📊 Vorherige Produkte: {len(previous_products)}")

if previous_products:
    # Finde Unterschiede
    new_products = find_new_products(current_products, previous_products)
    removed_products = find_new_products(previous_products, current_products)
    price_changes = find_price_changes(current_products, previous_products)
    status_changes = find_status_changes(current_products, previous_products)
    availability_changes = find_availability_changes(current_products, previous_products)
    
    # Sammle Artikel für Email-Benachrichtigung
    email_products = []
    
    # 1. Neue verfügbare Artikel
    new_available_products = [p for p in new_products if p.get('available', False)]
    if new_available_products:
        email_products.extend(new_available_products)
        print(f"\n✨ {len(new_available_products)} NEUE VERFÜGBARE ARTIKEL:")
        for p in new_available_products:
            shop_tag = f" ({p.get('shop', 'Shop')})" if 'shop' in p else ""
            status_tag = f" [{p['status']}]" if p.get('status') != 'Verfügbar' else ""
            print(f"  • {p['name']} ({p['price']}){status_tag}{shop_tag}")
    
    # 2. Artikel, die wieder verfügbar wurden
    restored_products = [p for p in availability_changes if not p['was_available'] and p['now_available']]
    if restored_products:
        # Konvertiere availability_changes zu vollständigen Product-Objekten
        for change in restored_products:
            product = next((p for p in current_products if p['name'] == change['name']), None)
            if product:
                email_products.append(product)
        
        print(f"\n📦 {len(restored_products)} ARTIKEL WIEDER VERFÜGBAR:")
        for p in restored_products:
            print(f"  • {p['name']}: ❌ Nicht verfügbar → ✓ Verfügbar (wieder in Stock!)")
    
    # Sende Email nur wenn es neue verfügbare Artikel gibt
    if email_products:
        send_available_products_email(email_products)
    
    # Zeige restliche Unterschiede
    if new_products and not new_available_products:
        print(f"\n✨ {len(new_products)} NEUE ARTIKEL (NICHT VERFÜGBAR):")
        for p in new_products[:10]:
            available_tag = "❌ NICHT VERFÜGBAR"
            status_tag = f" [{p['status']}]" if p.get('status') != 'Verfügbar' else ""
            shop_tag = f" ({p.get('shop', 'Shop')})" if 'shop' in p else ""
            print(f"  • {p['name']} ({p['price']}) {available_tag}{status_tag}{shop_tag}")
        if len(new_products) > 10:
            print(f"  ... und {len(new_products) - 10} weitere")
    
    if removed_products:
        print(f"\n❌ {len(removed_products)} ENTFERNTE ARTIKEL:")
        for p in removed_products[:5]:
            shop_tag = f" ({p.get('shop', 'Shop')})" if 'shop' in p else ""
            print(f"  • {p['name']}{shop_tag}")
    
    if price_changes:
        print(f"\n💰 {len(price_changes)} PREISÄNDERUNGEN:")
        for p in price_changes[:5]:
            print(f"  • {p['name']}: {p['old_price']} → {p['new_price']}")
    
    if status_changes:
        print(f"\n⚠️ {len(status_changes)} STATUSÄNDERUNGEN:")
        for p in status_changes[:10]:
            print(f"  • {p['name']}: {p['old_status']} → {p['new_status']}")
    
    # Zeige andere Verfügbarkeitswechsel (nicht verfügbar → nicht verfügbar ist uninteressant)
    other_availability_changes = [p for p in availability_changes if not (not p['was_available'] and p['now_available'])]
    if other_availability_changes:
        print(f"\n📦 {len(other_availability_changes)} WEITERE VERFÜGBARKEITSWECHSEL:")
        for p in other_availability_changes:
            print(f"  • {p['name']}: Verfügbar → ❌ Momentan nicht verfügbar")
    
    if not new_products and not removed_products and not price_changes and not status_changes and not availability_changes:
        print("\n✅ Keine Änderungen erkannt")
else:
    print("\n📝 Erste Prüfung - Speichere Produkte...")

# Speichere aktuelle Produkte
save_products(current_products)
print(f"\n✔️ {len(current_products)} Produkte gespeichert in {PRODUCTS_FILE}")