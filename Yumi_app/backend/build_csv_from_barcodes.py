import requests
import pandas as pd
from data_map import map_off_product
from prices_demo import get_demo_price

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

def fetch_off(barcode: str):
    try:
        r = requests.get(OFF_API.format(barcode=barcode), timeout=15)
        if r.status_code == 404:
            print(f"⚠️ Produit introuvable OFF : {barcode}")
            return None
        r.raise_for_status()
        return r.json().get("product")
    except Exception as e:
        print(f"❌ Erreur requête OFF pour {barcode}: {e}")
        return None

# --- Mets bien des EAN complets (13 chiffres)
barcodes = [
    "3017620422003",  # Nutella
    "3175680011480",  # Pâtes Auchan
    "3228857000852",  # Yaourt Danone
]

rows = []
for ean in barcodes:
    p = fetch_off(ean)
    if not p:
        continue  # saute si produit introuvable
    m = map_off_product(p)
    weight = m.get("serving_quantity_gml") or 100
    priceinfo = get_demo_price(ean, weight_g=weight)
    m.update(priceinfo)
    rows.append(m)

if rows:  # seulement si on a récupéré quelque chose
    df = pd.DataFrame(rows)
    output = "off_products_with_prices.csv"
    df.to_csv(output, index=False, encoding="utf-8")
    print(f"✅ Fichier CSV généré : {output} ({len(rows)} produits)")
else:
    print("⚠️ Aucun produit valide récupéré, CSV non créé")
