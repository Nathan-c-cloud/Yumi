import requests
import time
import random

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
OFF_SEARCH_API = "https://world.openfoodfacts.org/cgi/search.pl"

def fetch_off(barcode: str):
    r = requests.get(OFF_API.format(barcode=barcode), timeout=15)
    r.raise_for_status()
    js = r.json()
    return js.get("product")

def search_products_by_category(category=None, nutrition_grade=None, page_size=20, page=1):
    """
    Recherche de produits sur OpenFoodFacts par catégorie et critères nutritionnels
    """
    params = {
        'action': 'process',
        'json': 1,
        'page_size': page_size,
        'page': page,
        'sort_by': 'unique_scans_n'  # Trier par popularité
    }

    # Filtres de catégorie
    if category:
        if category == 'spreads':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'spreads'
        elif category == 'breakfast':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'breakfast'
        elif category == 'beverages':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'beverages'
        elif category == 'dairy':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'dairy'
        elif category == 'snacks':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'snacks'
        elif category == 'bread':
            params['tagtype_0'] = 'categories'
            params['tag_contains_0'] = 'contains'
            params['tag_0'] = 'bread'

    # Filtres nutritionnels
    if nutrition_grade:
        params['tagtype_1'] = 'nutrition_grades'
        params['tag_contains_1'] = 'contains'
        params['tag_1'] = nutrition_grade

    try:
        response = requests.get(OFF_SEARCH_API, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        products = []
        for product in data.get('products', []):
            # Vérifier que le produit a les données nutritionnelles de base
            if (product.get('nutriments') and
                product.get('product_name') and
                product.get('code')):
                products.append(product)

        return products

    except Exception as e:
        print(f"Erreur lors de la recherche OpenFoodFacts: {e}")
        return []

def search_better_alternatives(current_categories=None, exclude_barcode=None, max_results=50):
    """
    Recherche d'alternatives saines sur OpenFoodFacts
    """
    products = []

    # Définir les catégories à rechercher
    search_categories = []
    if current_categories:
        for cat in current_categories[:3]:  # Limiter aux 3 premières catégories
            cat_lower = cat.lower()
            if 'spread' in cat_lower or 'pate-a-tartiner' in cat_lower:
                search_categories.append('spreads')
            elif 'breakfast' in cat_lower:
                search_categories.append('breakfast')
            elif 'beverage' in cat_lower or 'drink' in cat_lower:
                search_categories.append('beverages')
            elif 'dairy' in cat_lower or 'milk' in cat_lower:
                search_categories.append('dairy')
            elif 'snack' in cat_lower or 'biscuit' in cat_lower:
                search_categories.append('snacks')
            elif 'bread' in cat_lower or 'pain' in cat_lower:
                search_categories.append('bread')

    # Si pas de catégorie spécifique trouvée, rechercher dans les catégories générales saines
    if not search_categories:
        search_categories = ['dairy', 'breakfast']

    # Rechercher des produits avec de bons nutri-scores
    for category in search_categories[:2]:  # Limiter à 2 catégories pour éviter trop de requêtes
        for grade in ['a', 'b']:  # Chercher les produits avec nutri-score A ou B
            try:
                category_products = search_products_by_category(
                    category=category,
                    nutrition_grade=grade,
                    page_size=25,
                    page=1
                )
                products.extend(category_products)

                # Pause pour éviter de surcharger l'API
                time.sleep(0.5)

                if len(products) >= max_results:
                    break
            except Exception as e:
                print(f"Erreur recherche catégorie {category}: {e}")
                continue

        if len(products) >= max_results:
            break

    # Exclure le produit actuel
    if exclude_barcode:
        products = [p for p in products if p.get('code') != str(exclude_barcode)]

    # Mélanger pour avoir de variété
    random.shuffle(products)

    return products[:max_results]
