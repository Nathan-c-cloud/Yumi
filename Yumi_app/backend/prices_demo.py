import random
import pandas as pd
from off_client import fetch_off

MOCK_PRICES = {
    "3017620422003": {"price": 3.49, "unit_price": 8.72, "store": "Demo Carrefour"},
    "3228857000852": {"price": 1.59, "unit_price": 3.18, "store": "Demo Leclerc"},
    "3560071101017": {"price": 0.95, "unit_price": 1.90, "store": "Demo Auchan"},
}

def get_demo_price(barcode: str, weight_g: float = 100, off_price: float = None):
    """
    Retourne un prix pour un produit.
    - Priorité au prix provenant d'OpenFoodFacts (si disponible).
    - Sinon, cherche dans MOCK_PRICES.
    - Sinon, génère un prix aléatoire de démo.
    """
    # 1. Si OFF a un prix (champ "price")
    if off_price is not None:
        base_price = round(float(off_price), 2)
        unit_price = round(base_price / (weight_g / 1000), 2) if weight_g else None
        return {"price": base_price, "unit_price": unit_price, "store": "OpenFoodFacts"}

    # 1bis. Essayer de récupérer le prix depuis OFF directement
    try:
        off_product = fetch_off(barcode)
        if off_product:
            # Essayer d'extraire le prix du champ 'price' ou 'product_price'
            price = off_product.get("price") or off_product.get("product_price")
            if price:
                try:
                    base_price = round(float(price), 2)
                    unit_price = round(base_price / (weight_g / 1000), 2) if weight_g else None
                    return {"price": base_price, "unit_price": unit_price, "store": "OpenFoodFacts"}
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Si on a un prix mock connu
    if barcode in MOCK_PRICES:
        return MOCK_PRICES[barcode]

    # 3. Sinon, prix aléatoire
    base_price = round(random.uniform(0.8, 4.5), 2)
    unit_price = round(base_price / (weight_g / 1000), 2) if weight_g else None
    return {"price": base_price, "unit_price": unit_price, "store": "Demo Store"}

def attach_demo_prices(df: pd.DataFrame) -> pd.DataFrame:
    def _w(x):
        try:
            return float(x)
        except Exception:
            return 100.0
    weights = df.get("serving_quantity_gml", pd.Series([None]*len(df))).map(_w)
    out = []
    for ean, w in zip(df["barcode"].astype(str), weights):
        out.append(get_demo_price(ean, weight_g=w or 100.0))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(out)], axis=1)
