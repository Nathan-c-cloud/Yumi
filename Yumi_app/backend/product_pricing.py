"""
Système de génération de prix pour les produits alimentaires
Génère des prix réalistes basés sur les catégories et caractéristiques des produits
"""

import random
import hashlib
from typing import Optional

class ProductPriceGenerator:
    """Générateur de prix cohérents pour les produits alimentaires"""

    # Prix de base par catégorie (en euros)
    CATEGORY_BASE_PRICES = {
        # Produits frais
        'fruits': {'min': 2.50, 'max': 8.00},
        'vegetables': {'min': 1.50, 'max': 6.00},
        'légumes': {'min': 1.50, 'max': 6.00},
        'meat': {'min': 8.00, 'max': 25.00},
        'viandes': {'min': 8.00, 'max': 25.00},
        'poultry': {'min': 6.00, 'max': 15.00},
        'volailles': {'min': 6.00, 'max': 15.00},
        'fish': {'min': 10.00, 'max': 30.00},
        'poissons': {'min': 10.00, 'max': 30.00},
        'seafood': {'min': 15.00, 'max': 40.00},
        'dairy': {'min': 1.20, 'max': 8.00},
        'laitiers': {'min': 1.20, 'max': 8.00},
        'cheese': {'min': 4.00, 'max': 20.00},
        'fromages': {'min': 4.00, 'max': 20.00},

        # Produits d'épicerie
        'cereals': {'min': 2.00, 'max': 8.00},
        'céréales': {'min': 2.00, 'max': 8.00},
        'pasta': {'min': 1.00, 'max': 4.00},
        'pâtes': {'min': 1.00, 'max': 4.00},
        'rice': {'min': 1.50, 'max': 6.00},
        'riz': {'min': 1.50, 'max': 6.00},
        'bread': {'min': 1.00, 'max': 5.00},
        'pain': {'min': 1.00, 'max': 5.00},
        'cookies': {'min': 2.00, 'max': 6.00},
        'biscuits': {'min': 2.00, 'max': 6.00},
        'chocolate': {'min': 1.50, 'max': 12.00},
        'chocolat': {'min': 1.50, 'max': 12.00},
        'snacks': {'min': 1.50, 'max': 5.00},

        # Boissons
        'beverages': {'min': 1.00, 'max': 8.00},
        'boissons': {'min': 1.00, 'max': 8.00},
        'water': {'min': 0.50, 'max': 3.00},
        'eau': {'min': 0.50, 'max': 3.00},
        'juices': {'min': 2.00, 'max': 6.00},
        'jus': {'min': 2.00, 'max': 6.00},
        'sodas': {'min': 1.00, 'max': 4.00},
        'coffee': {'min': 3.00, 'max': 15.00},
        'café': {'min': 3.00, 'max': 15.00},
        'tea': {'min': 2.00, 'max': 10.00},
        'thé': {'min': 2.00, 'max': 10.00},

        # Condiments et sauces
        'sauces': {'min': 1.50, 'max': 8.00},
        'condiments': {'min': 2.00, 'max': 10.00},
        'spices': {'min': 1.00, 'max': 8.00},
        'épices': {'min': 1.00, 'max': 8.00},
        'oils': {'min': 3.00, 'max': 15.00},
        'huiles': {'min': 3.00, 'max': 15.00},

        # Conserves
        'canned': {'min': 1.00, 'max': 5.00},
        'conserves': {'min': 1.00, 'max': 5.00},
        'frozen': {'min': 2.00, 'max': 12.00},
        'surgelés': {'min': 2.00, 'max': 12.00},

        # Produits bio et premium
        'organic': {'min': 3.00, 'max': 20.00},
        'bio': {'min': 3.00, 'max': 20.00},
        'premium': {'min': 5.00, 'max': 25.00},

        # Défaut
        'default': {'min': 1.50, 'max': 8.00}
    }

    # Modificateurs de prix
    BRAND_MULTIPLIERS = {
        'premium': 1.3,    # Marques premium (+30%)
        'bio': 1.4,        # Produits bio (+40%)
        'organic': 1.4,    # Produits bio (+40%)
        'light': 1.1,      # Produits allégés (+10%)
        '0%': 1.1,         # Produits 0% (+10%)
        'sans': 1.2,       # Produits sans (gluten, lactose, etc.) (+20%)
        'artisanal': 1.5,  # Produits artisanaux (+50%)
        'local': 1.2,      # Produits locaux (+20%)
        'équitable': 1.3,  # Commerce équitable (+30%)
        'fair': 1.3,       # Commerce équitable (+30%)
    }

    @classmethod
    def generate_price(cls, product_name: str, categories: list = None, brands: str = "",
                      nutriscore: str = "", barcode: str = "") -> float:
        """
        Génère un prix cohérent pour un produit basé sur ses caractéristiques
        Le prix sera toujours le même pour le même produit (basé sur le barcode)
        """
        # Utiliser le barcode pour générer un prix cohérent
        if barcode:
            # Créer une seed basée sur le barcode pour la cohérence
            seed = int(hashlib.md5(barcode.encode()).hexdigest()[:8], 16)
            random.seed(seed)

        # Déterminer la catégorie principale
        category_info = cls._get_category_price_range(product_name, categories)
        base_min = category_info['min']
        base_max = category_info['max']

        # Prix de base aléatoire dans la fourchette
        base_price = random.uniform(base_min, base_max)

        # Appliquer les modificateurs de marque/type
        price_multiplier = cls._calculate_price_multiplier(product_name, brands)

        # Ajustement selon le Nutriscore (meilleur score = souvent plus cher)
        nutriscore_multiplier = cls._get_nutriscore_multiplier(nutriscore)

        # Prix final
        final_price = base_price * price_multiplier * nutriscore_multiplier

        # Arrondir à des prix réalistes (ex: 2.49, 3.95, etc.)
        final_price = cls._round_to_realistic_price(final_price)

        # Remettre la seed aléatoire
        random.seed()

        return final_price

    @classmethod
    def _get_category_price_range(cls, product_name: str, categories: list = None) -> dict:
        """Détermine la fourchette de prix selon la catégorie du produit"""
        product_lower = product_name.lower()
        categories_lower = [cat.lower() for cat in (categories or [])]

        # Rechercher dans les catégories d'abord
        for category in categories_lower:
            for price_category, price_range in cls.CATEGORY_BASE_PRICES.items():
                if price_category in category:
                    return price_range

        # Rechercher dans le nom du produit
        for price_category, price_range in cls.CATEGORY_BASE_PRICES.items():
            if price_category in product_lower:
                return price_range

        # Retourner le prix par défaut
        return cls.CATEGORY_BASE_PRICES['default']

    @classmethod
    def _calculate_price_multiplier(cls, product_name: str, brands: str) -> float:
        """Calcule le multiplicateur de prix selon les caractéristiques du produit"""
        text_to_check = (product_name + " " + brands).lower()
        multiplier = 1.0

        # Appliquer les multiplicateurs
        for keyword, mult in cls.BRAND_MULTIPLIERS.items():
            if keyword in text_to_check:
                multiplier *= mult

        return multiplier

    @classmethod
    def _get_nutriscore_multiplier(cls, nutriscore: str) -> float:
        """Ajustement de prix selon le Nutriscore"""
        if not nutriscore:
            return 1.0

        nutriscore_multipliers = {
            'a': 1.1,   # Nutriscore A = souvent plus cher (meilleure qualité)
            'b': 1.05,  # Nutriscore B = légèrement plus cher
            'c': 1.0,   # Nutriscore C = prix normal
            'd': 0.95,  # Nutriscore D = légèrement moins cher
            'e': 0.90   # Nutriscore E = souvent moins cher
        }

        return nutriscore_multipliers.get(nutriscore.lower(), 1.0)

    @classmethod
    def _round_to_realistic_price(cls, price: float) -> float:
        """Arrondit à des prix réalistes comme dans les magasins"""
        if price < 1.0:
            # Prix < 1€ : arrondir au centime près
            return round(price, 2)
        elif price < 5.0:
            # Prix entre 1-5€ : arrondir à X.X9 ou X.X5
            base = int(price * 10) / 10
            decimal = price - base
            if decimal < 0.05:
                return base
            elif decimal < 0.09:
                return base + 0.05
            else:
                return base + 0.09
        elif price < 10.0:
            # Prix entre 5-10€ : arrondir à X.X9
            base = int(price)
            decimal = price - base
            if decimal < 0.5:
                return base + 0.49
            else:
                return base + 0.99
        else:
            # Prix > 10€ : arrondir à X.99
            base = int(price)
            return base + 0.99

    @classmethod
    def estimate_weekly_cost_per_person(cls, products: list) -> float:
        """Estime le coût hebdomadaire par personne pour une liste de produits"""
        if not products:
            return 0.0

        total_cost = 0.0
        for product in products:
            price = product.get('price', 0.0)
            quantity = product.get('quantity', 1)

            # Estimer la consommation hebdomadaire (approximative)
            # La plupart des produits durent 1-2 semaines
            weekly_consumption = quantity * 0.7  # 70% du produit consommé par semaine
            total_cost += price * weekly_consumption

        return round(total_cost, 2)

    @classmethod
    def filter_products_by_budget(cls, products: list, weekly_budget: float,
                                 target_percentage: float = 0.8) -> list:
        """
        Filtre une liste de produits pour respecter un budget hebdomadaire
        target_percentage: pourcentage du budget à utiliser (0.8 = 80%)
        """
        if not products or not weekly_budget:
            return products

        target_budget = weekly_budget * target_percentage

        # Trier les produits par rapport qualité/prix (score Yumi / prix)
        def quality_price_ratio(product):
            price = product.get('price', 1.0)
            yumi_score = product.get('yumi_score', 0)
            suitability_score = product.get('suitability_score', yumi_score)
            return suitability_score / price if price > 0 else 0

        products_sorted = sorted(products, key=quality_price_ratio, reverse=True)

        selected_products = []
        current_cost = 0.0

        for product in products_sorted:
            product_price = product.get('price', 0.0)
            estimated_weekly_cost = product_price * 0.7  # Consommation hebdomadaire estimée

            if current_cost + estimated_weekly_cost <= target_budget:
                selected_products.append(product)
                current_cost += estimated_weekly_cost
            elif len(selected_products) < 3:
                # S'assurer d'avoir au moins 3 produits même si ça dépasse un peu
                selected_products.append(product)
                current_cost += estimated_weekly_cost

        return selected_products
