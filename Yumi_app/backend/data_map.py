import re
import requests
import pandas as pd
import random

from prices_demo import attach_demo_prices


def _g(nutr, key):
    return None if not nutr else nutr.get(key)

def _to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None

def parse_serving(serving_size, serving_quantity):
    qty = _to_float(serving_quantity)
    if qty:
        return qty
    if not serving_size:
        return None
    m = re.search(r"([\d\.,]+)\s*(g|ml)", serving_size.lower())
    if not m:
        return None
    val = _to_float(m.group(1))
    unit = m.group(2)
    return val if unit in ("g", "ml") else None

def _safe_div(a, b):
    a = _to_float(a); b = _to_float(b)
    if a is None or b in (None, 0):
        return None
    return a / b

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

def fetch_off(barcode: str):
    r = requests.get(OFF_API.format(barcode=barcode), timeout=15)
    r.raise_for_status()
    js = r.json()
    return js.get("product")

# ---------- Flags lexicaux ----------
SUCRES_AJOUTES = [
    "sirop de glucose", "sirop de glucose-fructose", "maltodextrine", "dextrose",
    "sucre inverti", "saccharose", "fructose", "glucose"
]
PROTEINES_VEG = [
    "protéine de pois", "protéine de soja", "isolat de soja", "protéine de blé"
]

def has_any(text, keywords):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in keywords)



def map_off_product(p: dict) -> dict:
    nutr = p.get("nutriments", {}) or {}

    energy_kcal = _to_float(_g(nutr, "energy-kcal_100g"))
    proteins    = _to_float(_g(nutr, "proteins_100g"))
    carbs       = _to_float(_g(nutr, "carbohydrates_100g"))
    sugars      = _to_float(_g(nutr, "sugars_100g"))
    fat         = _to_float(_g(nutr, "fat_100g"))
    sat_fat     = _to_float(_g(nutr, "saturated-fat_100g"))
    fiber       = _to_float(_g(nutr, "fiber_100g"))
    salt        = _to_float(_g(nutr, "salt_100g"))
    sodium      = _to_float(_g(nutr, "sodium_100g"))
    trans_fat   = _to_float(_g(nutr, "trans-fat_100g"))

    calcium     = _to_float(_g(nutr, "calcium_100g"))
    iron        = _to_float(_g(nutr, "iron_100g"))
    potassium   = _to_float(_g(nutr, "potassium_100g"))
    iodine      = _to_float(_g(nutr, "iodine_100g"))
    vit_b9      = _to_float(_g(nutr, "vitamin-b9_100g"))
    vit_d       = _to_float(_g(nutr, "vitamin-d_100g"))

    serving_size     = p.get("serving_size")
    serving_quantity = p.get("serving_quantity")
    serving_q        = parse_serving(serving_size, serving_quantity)

    # --- Dérivées par 100 kcal
    proteins_per_100kcal = _safe_div(proteins, energy_kcal/100) if energy_kcal else None
    fiber_per_100kcal    = _safe_div(fiber,    energy_kcal/100) if energy_kcal else None
    sugar_per_100kcal    = _safe_div(sugars,   energy_kcal/100) if energy_kcal else None

    # --- Ratios
    ratio_prot_sugar  = _safe_div(proteins, sugars)
    ratio_fiber_sugar = _safe_div(fiber, sugars)
    ratio_sat_total   = _safe_div(sat_fat, fat)

    # --- Flags NLP simples
    ingredients_text = p.get("ingredients_text")
    added_sugars_flag = has_any(ingredients_text, SUCRES_AJOUTES)
    veg_proteins_flag = has_any(ingredients_text, PROTEINES_VEG)

    return {
        # Identité utile
        "barcode": p.get("code"),
        "product_name": p.get("product_name"),
        "brands": p.get("brands"),
        "nutriscore_grade": p.get("nutriscore_grade"),
        # A) Nutriments
        "energy_kcal_100g": energy_kcal,
        "proteins_100g": proteins,
        "carbohydrates_100g": carbs,
        "sugars_100g": sugars,
        "fat_100g": fat,
        "saturated_fat_100g": sat_fat,
        "fiber_100g": fiber,
        "salt_100g": salt,
        "sodium_100g": sodium,
        "trans_fat_100g": trans_fat,
        "calcium_100g": calcium,
        "iron_100g": iron,
        "potassium_100g": potassium,
        "iodine_100g": iodine,
        "vitamin_b9_100g": vit_b9,
        "vitamin_d_100g": vit_d,
        "serving_size": serving_size,
        "serving_quantity_gml": serving_q,
        # B) Ingrédients & additifs
        "ingredients_text": ingredients_text,
        "ingredients_tags": p.get("ingredients_tags"),
        "additives_tags": p.get("additives_tags"),
        "allergens_tags": p.get("allergens_tags"),
        "added_sugars_flag": added_sugars_flag,
        "veg_proteins_flag": veg_proteins_flag,
        # C) Labels & catégories
        "labels_tags": p.get("labels_tags"),
        "categories_tags": p.get("categories_tags"),
        # D) Process
        "nova_group": p.get("nova_group"),
        # E) Packaging / environnement
        "packaging_text": p.get("packaging_text"),
        "packaging_tags": p.get("packaging_tags"),
        "packaging_material_tags": p.get("packaging_materials_tags"),
        "packaging_recycling_tags": p.get("packaging_recycling_tags"),
        # F) Marché (souvent vide côté OFF)
        "stores_tags": p.get("stores_tags"),
        "price": p.get("price"),
        # --- Dérivées ---
        "proteins_per_100kcal": proteins_per_100kcal,
        "fiber_per_100kcal": fiber_per_100kcal,
        "sugar_per_100kcal": sugar_per_100kcal,
        "ratio_prot_sugar": ratio_prot_sugar,
        "ratio_fiber_sugar": ratio_fiber_sugar,
        "ratio_sat_total": ratio_sat_total,
    }


