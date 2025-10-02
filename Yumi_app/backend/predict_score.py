# predict_score.py - Script standalone pour prédire le score YUmi à partir d'un code-barres
import json
import joblib
import torch
import torch.nn as nn
import numpy as np
from off_client import fetch_off
from data_map import map_off_product
from user_profile import UserProfile, create_adult_profile

# Architecture du modèle (copie de train.py pour éviter l'import)
class ImprovedMLP(nn.Module):
    def __init__(self, in_dim, hid1=256, hid2=128, hid3=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hid1),
            nn.BatchNorm1d(hid1),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hid1, hid2),
            nn.BatchNorm1d(hid2),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hid2, hid3),
            nn.BatchNorm1d(hid3),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hid3, 1),
        )

    def forward(self, x):
        return self.net(x)

class YumiPredictor:
    def __init__(self, model_dir="artifacts"):
        self.model_dir = model_dir
        self.load_model()

    def load_model(self):
        """Charger le modèle et les artefacts"""
        print("🔄 Chargement du modèle YUmi...")

        # Charger le scaler et les métadonnées
        self.scaler = joblib.load(f"{self.model_dir}/scaler.pkl")
        with open(f"{self.model_dir}/meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.feature_order = meta["feature_order"]

        # Charger le modèle
        self.model = ImprovedMLP(in_dim=len(self.feature_order))
        self.model.load_state_dict(torch.load(f"{self.model_dir}/best_yumi_mlp.pt", map_location="cpu"))
        self.model.eval()

        print(f"✅ Modèle chargé avec {len(self.feature_order)} features")

    def create_features_from_product(self, product_data):
        """Créer les features nécessaires à partir des données produit OFF"""
        features = {}

        # Features de base nutritionnelles
        for feature in self.feature_order:
            if feature.endswith('_100g'):
                value = product_data.get(feature)
                # Gestion robuste des valeurs manquantes ou None
                if value is None or value == '' or str(value).lower() in ['nan', 'none']:
                    features[feature] = 0.0
                else:
                    try:
                        features[feature] = float(value)
                    except (ValueError, TypeError):
                        features[feature] = 0.0

        # Features dérivées (comme dans train.py)
        if 'sugar_carb_ratio' in self.feature_order:
            sugars = features.get('sugars_100g', 0.0)
            carbs = features.get('carbohydrates_100g', 0.0)
            features['sugar_carb_ratio'] = sugars / (carbs + 1e-8) if carbs > 0 else 0.0

        return features

    def predict_score(self, features_dict):
        """Prédire le score à partir des features"""
        # Créer le vecteur de features dans le bon ordre
        x = [features_dict.get(feature, 0.0) for feature in self.feature_order]

        # Normaliser avec le scaler
        x_scaled = self.scaler.transform([x])

        # Prédiction de base
        with torch.no_grad():
            y_hat = self.model(torch.tensor(x_scaled, dtype=torch.float32))
            base_score = float(torch.clamp(y_hat, 0, 100))

        return base_score

    def apply_category_adjustments(self, base_score, product_data, features_dict):
        """Appliquer des ajustements selon la catégorie de produit"""
        adjusted_score = base_score

        # Récupérer les catégories et le nom du produit
        categories = product_data.get('categories_tags', [])
        product_name = product_data.get('product_name', '').lower()

        # Identifier le type de produit avec détection d'alcool améliorée
        is_beverage = any('beverage' in cat.lower() for cat in categories)
        is_soda = any(keyword in cat.lower() for cat in categories for keyword in ['soda', 'soft-drink', 'cola'])
        is_candy = any(keyword in cat.lower() for cat in categories for keyword in ['candy', 'confectionery', 'sweets', 'chocolate'])
        is_water = any(keyword in cat.lower() for cat in categories for keyword in ['water', 'mineral-water']) or 'eau' in product_name
        is_snack = any('snack' in cat.lower() for cat in categories)

        # Détection d'alcool améliorée avec mots complets pour éviter les faux positifs
        is_alcohol = False

        # Vérifier les catégories avec mots complets
        for cat in categories:
            cat_lower = cat.lower()
            if any(f'-{keyword}-' in cat_lower or cat_lower.startswith(f'{keyword}-') or cat_lower.endswith(f'-{keyword}') or cat_lower == keyword
                   for keyword in ['alcoholic', 'alcohol', 'wine', 'beer', 'spirits', 'liqueur', 'vodka', 'whisky', 'rum']):
                is_alcohol = True
                break
            # Cas spécial pour "gin" qui peut être dans "virgin" - on vérifie le mot complet
            if 'gin' in cat_lower and ('gin-' in cat_lower or '-gin-' in cat_lower or cat_lower.endswith('-gin') or cat_lower == 'gin'):
                is_alcohol = True
                break

        # Vérifier le nom du produit avec mots complets
        if not is_alcohol:
            product_words = product_name.split()
            alcohol_name_keywords = ['alcool', 'alcohol', 'wine', 'vin', 'bière', 'beer', 'vodka', 'whisky', 'rum', 'gin', 'cognac', 'champagne']
            for word in product_words:
                if word in alcohol_name_keywords:
                    is_alcohol = True
                    break

        # Récupérer les valeurs nutritionnelles
        sugars = features_dict.get('sugars_100g', 0.0)
        energy = features_dict.get('energy_100g', 0.0)

        # RESTRICTION ABSOLUE SUR L'ALCOOL
        if is_alcohol:
            # Score maximal très bas pour tous les produits alcoolisés
            adjusted_score = min(adjusted_score, 10)
            # Pénalité supplémentaire en fonction du degré d'alcool si disponible
            alcohol_by_volume = product_data.get('alcohol_by_volume_100g', 0)
            if alcohol_by_volume > 0:
                # Plus le degré d'alcool est élevé, plus la pénalité est importante
                alcohol_penalty = min(alcohol_by_volume * 0.5, 8)
                adjusted_score -= alcohol_penalty
            # Score minimum de 1 pour éviter les scores négatifs
            adjusted_score = max(adjusted_score, 1)
            return adjusted_score

        # AJUSTEMENTS RESTRICTIFS

        # 1. Boissons sucrées et sodas - TRÈS RESTRICTIF
        if is_soda or (is_beverage and sugars > 5):
            if sugars > 10:
                penalty = min((sugars - 5) * 5, 40)  # Pénalité massive
                adjusted_score -= penalty
            if energy > 150:  # Boissons très caloriques
                adjusted_score -= 20
            # Score plafonné à 30 pour les sodas
            adjusted_score = min(adjusted_score, 30)

        # 2. Bonbons et confiseries - TRÈS RESTRICTIF
        elif is_candy:
            if sugars > 30:
                penalty = min((sugars - 20) * 3, 50)
                adjusted_score -= penalty
            # Score plafonné à 25 pour les bonbons
            adjusted_score = min(adjusted_score, 25)

        # 3. Snacks - RESTRICTIF
        elif is_snack:
            if energy > 400:  # Snacks très caloriques
                penalty = (energy - 400) / 20
                adjusted_score -= penalty
            # Score plafonné à 45 pour les snacks
            adjusted_score = min(adjusted_score, 45)

        # AJUSTEMENTS CLÉMENTS

        # 4. Eau - TRÈS CLÉMENT
        elif is_water:
            # Bonus pour l'eau (hydratation importante)
            adjusted_score = max(adjusted_score, 85)  # Score minimum élevé pour l'eau
            if sugars == 0 and energy < 10:  # Eau pure
                adjusted_score = max(adjusted_score, 95)

        # 5. Produits laitiers de base - CLÉMENT
        elif any('dairy' in cat.lower() for cat in categories):
            if sugars < 15 and energy < 200:  # Produits laitiers non sucrés
                bonus = 10
                adjusted_score += bonus

        # 6. Fruits et légumes - TRÈS CLÉMENT
        elif any(keyword in cat.lower() for cat in categories for keyword in ['fruit', 'vegetable']):
            bonus = 15
            adjusted_score += bonus
            adjusted_score = max(adjusted_score, 75)  # Score minimum élevé

        return max(0, min(100, adjusted_score))

    def predict_from_barcode(self, barcode):
        """Prédire le score YUmi à partir d'un code-barres"""
        try:
            # 1. Récupérer les données produit depuis OpenFoodFacts
            print(f"🔍 Recherche du produit {barcode}...")
            off_product = fetch_off(barcode)

            if not off_product:
                return {
                    'success': False,
                    'error': f"Produit {barcode} introuvable sur OpenFoodFacts"
                }

            # 2. Mapper les données avec data_map
            mapped_product = map_off_product(off_product)
            product_name = mapped_product.get('product_name', 'Nom inconnu')
            print(f"📊 Produit trouvé: {product_name}")

            # 3. Créer les features pour le modèle
            features = self.create_features_from_product(mapped_product)

            # 4. Prédire le score de base
            base_score = self.predict_score(features)

            # 5. Appliquer les ajustements par catégorie
            adjusted_score = self.apply_category_adjustments(base_score, mapped_product, features)

            # 6. Déterminer l'interprétation du score ajusté
            categories = mapped_product.get('categories_tags', [])
            product_name = mapped_product.get('product_name', '').lower()

            # Utiliser la même logique améliorée pour la détection d'alcool
            is_alcohol = False

            # Vérifier les catégories avec mots complets
            for cat in categories:
                cat_lower = cat.lower()
                if any(f'-{keyword}-' in cat_lower or cat_lower.startswith(f'{keyword}-') or cat_lower.endswith(f'-{keyword}') or cat_lower == keyword
                       for keyword in ['alcoholic', 'alcohol', 'wine', 'beer', 'spirits', 'liqueur', 'vodka', 'whisky', 'rum']):
                    is_alcohol = True
                    break
                # Cas spécial pour "gin" qui peut être dans "virgin" - on vérifie le mot complet
                if 'gin' in cat_lower and ('gin-' in cat_lower or '-gin-' in cat_lower or cat_lower.endswith('-gin') or cat_lower == 'gin'):
                    is_alcohol = True
                    break

            # Vérifier le nom du produit avec mots complets
            if not is_alcohol:
                product_words = product_name.split()
                alcohol_name_keywords = ['alcool', 'alcohol', 'wine', 'vin', 'bière', 'beer', 'vodka', 'whisky', 'rum', 'gin', 'cognac', 'champagne']
                for word in product_words:
                    if word in alcohol_name_keywords:
                        is_alcohol = True
                        break

            if is_alcohol:
                interpretation = "⚠️ PRODUIT ALCOOLISÉ - Déconseillé pour la santé"
                color = "🔴"
            elif adjusted_score >= 80:
                interpretation = "Excellent choix nutritionnel 🥇"
                color = "🟢"
            elif adjusted_score >= 60:
                interpretation = "Bon choix nutritionnel ✅"
                color = "🟡"
            elif adjusted_score >= 40:
                interpretation = "Choix modéré ⚠️"
                color = "🟠"
            else:
                interpretation = "À consommer avec modération ⚠️"
                color = "🔴"

            result = {
                'success': True,
                'barcode': barcode,
                'product_name': product_name,
                'brands': mapped_product.get('brands', ''),
                'nutriscore_grade': mapped_product.get('nutriscore_grade', ''),
                'yumi_score': round(adjusted_score, 1),
                'base_score': round(base_score, 1),  # Score avant ajustements
                'interpretation': interpretation,
                'color': color,
                'features_used': features,
                'categories': mapped_product.get('categories_tags', [])
            }

            # 7. Ajouter des recommandations si le score est mauvais
            if adjusted_score < 50:  # Seuil pour un score "mauvais"
                print("💡 Score faible détecté - Recherche de recommandations...")
                recommendations = self.recommend_better_products(
                    features, adjusted_score, categories, user_profile=None, n=3, current_barcode=barcode
                )
                if recommendations:
                    result['recommendations'] = recommendations
                    print(f"✅ {len(recommendations)} recommandations trouvées")
                else:
                    print("⚠️ Aucune recommandation trouvée")

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur lors de la prédiction pour {barcode}: {str(e)}"
            }

    def apply_personalized_adjustments(self, base_score, product_data, features_dict, user_profile: UserProfile):
        """Appliquer des ajustements personnalisés selon le profil utilisateur"""
        adjusted_score = base_score
        warnings = []
        blocked = False

        # Récupérer les catégories et le nom du produit
        categories = product_data.get('categories_tags', [])
        product_name = product_data.get('product_name', '').lower()

        # 1. VÉRIFICATION DES ALLERGIES (BLOQUANT)
        detected_allergens = user_profile.check_allergies(categories, product_data.get('ingredients_tags', []))
        if detected_allergens:
            warnings.append(f"⚠️ ALLERGIE DÉTECTÉE: {', '.join(detected_allergens)}")
            blocked = True
            adjusted_score = 1  # Score très bas pour allergie
            return adjusted_score, warnings, blocked

        # 2. VÉRIFICATION DES RESTRICTIONS ALIMENTAIRES (BLOQUANT)
        dietary_violations = user_profile.check_dietary_restrictions(
            categories,
            product_data.get('labels_tags', []),
            product_data.get('product_name', '')
        )
        if dietary_violations:
            violation_names = [v.value.replace('_', ' ').title() for v in dietary_violations]
            warnings.append(f"🚫 RESTRICTION ALIMENTAIRE: Ne convient pas au régime {', '.join(violation_names)}")
            blocked = True
            adjusted_score = 1
            return adjusted_score, warnings, blocked

        # 3. DÉTECTION D'ALCOOL AVEC PERSONNALISATION CORRIGÉE
        is_alcohol = self._detect_alcohol(categories, product_name)

        if is_alcohol:
            alcohol_restriction = user_profile.get_alcohol_restriction_level()
            if alcohol_restriction >= 0.8:  # Restriction forte
                warnings.append("🚫 ALCOOL INTERDIT selon votre profil")
                blocked = True
                adjusted_score = 1
                return adjusted_score, warnings, blocked
            elif alcohol_restriction > 0:
                # Appliquer d'abord la restriction d'alcool générale (score max 10)
                adjusted_score = min(adjusted_score, 10)
                # Puis la pénalité personnalisée
                penalty = alcohol_restriction * 80  # Pénalité proportionnelle
                adjusted_score -= penalty
                warnings.append(f"⚠️ Produit alcoolisé (restriction: {alcohol_restriction*100:.0f}%)")
                adjusted_score = max(adjusted_score, 1)
            else:
                # Marie a alcohol_allowed=True et pas de restriction spéciale
                # Mais on applique quand même la restriction générale d'alcool
                adjusted_score = min(adjusted_score, 10)
                warnings.append("⚠️ Produit alcoolisé")

        # 4. AJUSTEMENTS NUTRITIONNELS PERSONNALISÉS (plus modérés)
        sugars = features_dict.get('sugars_100g', 0.0)
        sodium = features_dict.get('sodium_100g', 0.0)
        energy = features_dict.get('energy_100g', 0.0)
        salt = features_dict.get('salt_100g', 0.0)

        # Convertir salt en sodium si nécessaire (1g sel = 0.4g sodium)
        if sodium == 0 and salt > 0:
            sodium = salt * 0.4

        # Ajustements pour le sucre (pénalités moins sévères)
        if user_profile.max_sugar_tolerance and sugars > user_profile.max_sugar_tolerance:
            excess = sugars - user_profile.max_sugar_tolerance
            penalty = min(excess * user_profile.get_sugar_penalty_multiplier() * 0.8, 30)  # Encore plus modéré
            adjusted_score -= penalty
            warnings.append(f"⚠️ Trop de sucre: {sugars:.1f}g (limite: {user_profile.max_sugar_tolerance:.1f}g)")

        elif sugars > 35:  # Seuil très élevé pour le sucre général (Nutella = 56g)
            penalty = min((sugars - 35) * user_profile.get_sugar_penalty_multiplier() * 0.4, 15)  # Pénalité très douce
            adjusted_score -= penalty
            if user_profile.sugar_sensitivity > 0.6:  # Seuil très élevé pour l'avertissement
                warnings.append(f"⚠️ Produit très sucré: {sugars:.1f}g/100g")

        # Ajustements pour le sodium (pénalités moins sévères)
        if user_profile.max_sodium_tolerance and sodium > user_profile.max_sodium_tolerance:
            excess = sodium - user_profile.max_sodium_tolerance
            penalty = min(excess * user_profile.get_sodium_penalty_multiplier() * 25, 30)  # Réduire encore
            adjusted_score -= penalty
            warnings.append(f"⚠️ Trop de sodium: {sodium:.2f}g (limite: {user_profile.max_sodium_tolerance:.2f}g)")

        elif sodium > 1.2:  # Seuil encore plus élevé pour le sodium général
            penalty = min((sodium - 1.2) * user_profile.get_sodium_penalty_multiplier() * 15, 15)  # Pénalité plus douce
            adjusted_score -= penalty
            if user_profile.sodium_sensitivity > 0.5:  # Seuil plus élevé pour l'avertissement
                warnings.append(f"⚠️ Produit très salé: {sodium:.2f}g/100g")

        # Ajustements pour les calories (pénalités modérées)
        calorie_threshold = 450  # Seuil encore plus élevé
        if energy > calorie_threshold:
            penalty = min((energy - calorie_threshold) / 40 * user_profile.get_calorie_penalty_multiplier(), 15)  # Pénalité plus douce
            adjusted_score -= penalty
            if user_profile.calorie_sensitivity > 0.5:
                warnings.append(f"⚠️ Produit calorique: {energy:.0f} kcal/100g")

        # 5. BONUS SELON LES OBJECTIFS DE SANTÉ
        from user_profile import HealthGoal

        # Bonus pour les fibres si objectif santé
        fiber = features_dict.get('fiber_100g', 0.0)
        if HealthGoal.IMPROVE_HEALTH in user_profile.health_goals and fiber > 5:
            bonus = min(fiber * 2, 10)
            adjusted_score += bonus

        # Bonus pour les protéines si objectif muscle
        proteins = features_dict.get('proteins_100g', 0.0)
        if HealthGoal.BUILD_MUSCLE in user_profile.health_goals and proteins > 15:
            bonus = min((proteins - 15) * 1.5, 15)
            adjusted_score += bonus

        # 6. APPLIQUER LES AJUSTEMENTS GÉNÉRIQUES MODIFIÉS
        adjusted_score = self._apply_generic_category_adjustments(
            adjusted_score, product_data, features_dict, user_profile
        )

        return max(1, min(100, adjusted_score)), warnings, blocked

    def _detect_alcohol(self, categories, product_name):
        """Méthode helper pour détecter l'alcool"""
        # Vérifier les catégories avec mots complets
        for cat in categories:
            cat_lower = cat.lower()
            if any(f'-{keyword}-' in cat_lower or cat_lower.startswith(f'{keyword}-') or cat_lower.endswith(f'-{keyword}') or cat_lower == keyword
                   for keyword in ['alcoholic', 'alcohol', 'wine', 'beer', 'spirits', 'liqueur', 'vodka', 'whisky', 'rum']):
                return True
            # Cas spécial pour "gin"
            if 'gin' in cat_lower and ('gin-' in cat_lower or '-gin-' in cat_lower or cat_lower.endswith('-gin') or cat_lower == 'gin'):
                return True

        # Vérifier le nom du produit avec mots complets
        product_words = product_name.split()
        alcohol_name_keywords = ['alcool', 'alcohol', 'wine', 'vin', 'bière', 'beer', 'vodka', 'whisky', 'rum', 'gin', 'cognac', 'champagne']
        return any(word in alcohol_name_keywords for word in product_words)

    def _apply_generic_category_adjustments(self, base_score, product_data, features_dict, user_profile):
        """Appliquer les ajustements génériques modifiés selon le profil"""
        adjusted_score = base_score
        categories = product_data.get('categories_tags', [])
        product_name = product_data.get('product_name', '').lower()

        # Identifier le type de produit
        is_beverage = any('beverage' in cat.lower() for cat in categories)
        is_soda = any(keyword in cat.lower() for cat in categories for keyword in ['soda', 'soft-drink', 'cola'])
        is_candy = any(keyword in cat.lower() for cat in categories for keyword in ['candy', 'confectionery', 'sweets', 'chocolate'])
        is_water = any(keyword in cat.lower() for cat in categories for keyword in ['water', 'mineral-water']) or 'eau' in product_name
        is_snack = any('snack' in cat.lower() for cat in categories)

        sugars = features_dict.get('sugars_100g', 0.0)
        energy = features_dict.get('energy_100g', 0.0)

        # Ajustements modifiés selon le profil utilisateur
        sugar_multiplier = user_profile.get_sugar_penalty_multiplier()
        calorie_multiplier = user_profile.get_calorie_penalty_multiplier()

        # 1. Boissons sucrées et sodas
        if is_soda or (is_beverage and sugars > 5):
            if sugars > 10:
                penalty = min((sugars - 5) * 3 * sugar_multiplier, 50)
                adjusted_score -= penalty
            if energy > 150:
                penalty = 15 * calorie_multiplier
                adjusted_score -= penalty
            adjusted_score = min(adjusted_score, 35)  # Plafond moins strict

        # 2. Bonbons et confiseries
        elif is_candy:
            if sugars > 30:
                penalty = min((sugars - 20) * 2 * sugar_multiplier, 60)
                adjusted_score -= penalty
            adjusted_score = min(adjusted_score, 30)  # Plafond moins strict

        # 3. Snacks
        elif is_snack:
            if energy > 400:
                penalty = (energy - 400) / 15 * calorie_multiplier
                adjusted_score -= penalty
            adjusted_score = min(adjusted_score, 50)

        # 4. Eau - toujours très bien noté
        elif is_water:
            adjusted_score = max(adjusted_score, 85)
            if sugars == 0 and energy < 10:
                adjusted_score = max(adjusted_score, 95)

        # 5. Produits laitiers
        elif any('dairy' in cat.lower() for cat in categories):
            if sugars < 15 and energy < 200:
                bonus = 5  # Bonus réduit pour éviter la sur-notation
                adjusted_score += bonus

        # 6. Fruits et légumes
        elif any(keyword in cat.lower() for cat in categories for keyword in ['fruit', 'vegetable']):
            bonus = 10
            adjusted_score += bonus
            adjusted_score = max(adjusted_score, 70)

        return adjusted_score

    def predict_from_barcode_personalized(self, barcode, user_profile: UserProfile):
        """Prédire le score YUmi personnalisé à partir d'un code-barres et d'un profil utilisateur"""
        try:
            # 1. Récupérer les données produit depuis OpenFoodFacts
            print(f"🔍 Recherche du produit {barcode} pour {user_profile.name}...")
            off_product = fetch_off(barcode)

            if not off_product:
                return {
                    'success': False,
                    'error': f"Produit {barcode} introuvable sur OpenFoodFacts"
                }

            # 2. Mapper les données avec data_map
            mapped_product = map_off_product(off_product)
            product_name = mapped_product.get('product_name', 'Nom inconnu')
            print(f"📊 Produit trouvé: {product_name}")

            # 3. Créer les features pour le modèle
            features = self.create_features_from_product(mapped_product)

            # 4. Prédire le score de base
            base_score = self.predict_score(features)

            # 5. Appliquer les ajustements personnalisés
            adjusted_score, warnings, blocked = self.apply_personalized_adjustments(
                base_score, mapped_product, features, user_profile
            )

            # 6. Déterminer l'interprétation personnalisée
            if blocked:
                interpretation = "🚫 PRODUIT NON RECOMMANDÉ pour votre profil"
                color = "🔴"
            elif adjusted_score >= 80:
                interpretation = f"✨ Excellent pour {user_profile.name} 🥇"
                color = "🟢"
            elif adjusted_score >= 60:
                interpretation = f"👍 Bon choix pour {user_profile.name} ✅"
                color = "🟡"
            elif adjusted_score >= 40:
                interpretation = f"⚠️ Choix modéré pour {user_profile.name}"
                color = "🟠"
            else:
                interpretation = f"🚫 À éviter pour {user_profile.name}"
                color = "🔴"

            result = {
                'success': True,
                'barcode': barcode,
                'product_name': product_name,
                'brands': mapped_product.get('brands', ''),
                'nutriscore_grade': mapped_product.get('nutriscore_grade', ''),
                'yumi_score': round(adjusted_score, 1),
                'base_score': round(base_score, 1),
                'interpretation': interpretation,
                'color': color,
                'warnings': warnings,
                'blocked': blocked,
                'user_profile': user_profile.name,
                'features_used': features,
                'categories': mapped_product.get('categories_tags', [])
            }

            # 7. Ajouter des recommandations personnalisées si le score est mauvais
            if adjusted_score < 50:  # Seuil pour un score "mauvais"
                print(f"💡 Score faible détecté pour {user_profile.name} - Recherche de recommandations personnalisées...")
                recommendations = self.recommend_better_products(
                    features, adjusted_score, mapped_product.get('categories_tags', []),
                    user_profile=user_profile, n=3, current_barcode=barcode
                )
                if recommendations:
                    result['recommendations'] = recommendations
                    print(f"✅ {len(recommendations)} recommandations personnalisées trouvées")
                else:
                    print("⚠️ Aucune recommandation personnalisée trouvée")

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur lors de la prédiction personnalisée pour {barcode}: {str(e)}"
            }

    def recommend_better_products_from_off(self, current_features, current_score, current_categories=None, user_profile=None, n=3, current_barcode=None):
        """Recommande n produits avec un meilleur score en cherchant sur OpenFoodFacts"""
        from off_client import search_better_alternatives
        from data_map import map_off_product

        print("🌐 Recherche de recommandations sur OpenFoodFacts...")

        # Rechercher des alternatives sur OpenFoodFacts
        off_products = search_better_alternatives(
            current_categories=current_categories,
            exclude_barcode=current_barcode,
            max_results=100  # Chercher plus de produits pour avoir plus de choix
        )

        if not off_products:
            print("⚠️ Aucun produit trouvé sur OpenFoodFacts")
            return []

        print(f"🔍 {len(off_products)} produits trouvés sur OpenFoodFacts, calcul des scores...")

        recommendations = []

        # Calculer le score YUmi pour chaque produit trouvé
        for product in off_products:
            try:
                # Mapper le produit OpenFoodFacts
                mapped_product = map_off_product(product)

                if not mapped_product.get('product_name'):
                    continue

                # Créer les features
                prod_features = self.create_features_from_product(mapped_product)

                # Calculer le score de base
                base_score = self.predict_score(prod_features)

                # Appliquer les ajustements selon le profil
                if user_profile:
                    product_data = {
                        'product_name': mapped_product.get('product_name', ''),
                        'categories_tags': mapped_product.get('categories_tags', []),
                        'ingredients_tags': mapped_product.get('ingredients_tags', [])
                    }
                    adjusted_score, warnings, blocked = self.apply_personalized_adjustments(
                        base_score, product_data, prod_features, user_profile
                    )
                    if blocked or adjusted_score <= current_score:
                        continue
                else:
                    # Appliquer les ajustements par catégorie standards
                    adjusted_score = self.apply_category_adjustments(base_score, mapped_product, prod_features)
                    if adjusted_score <= current_score:
                        continue

                # Ajouter à la liste si le score est meilleur
                if adjusted_score > current_score + 5:  # Marge de 5 points minimum
                    recommendations.append({
                        'barcode': str(product.get('code', '')),
                        'product_name': mapped_product.get('product_name', 'Nom inconnu'),
                        'brands': mapped_product.get('brands', ''),
                        'yumi_score': round(adjusted_score, 1),
                        'nutriscore_grade': mapped_product.get('nutriscore_grade', ''),
                        'categories': str(mapped_product.get('categories_tags', []))[:100]
                    })

            except Exception as e:
                print(f"Erreur traitement produit {product.get('code', 'unknown')}: {e}")
                continue

        # Trier par score décroissant et diversifier par marque
        recommendations.sort(key=lambda x: x['yumi_score'], reverse=True)

        # Diversifier les recommandations
        diverse_recommendations = []
        used_brands = set()

        for rec in recommendations:
            brand = rec['brands'].strip() if rec['brands'] else 'Unknown'
            if brand not in used_brands or len(diverse_recommendations) < n:
                diverse_recommendations.append(rec)
                used_brands.add(brand)
                if len(diverse_recommendations) >= n:
                    break

        print(f"✅ {len(diverse_recommendations)} recommandations OpenFoodFacts sélectionnées")
        return diverse_recommendations[:n]

    def recommend_better_products(self, current_features, current_score, current_categories=None, user_profile=None, n=3, current_barcode=None):
        """Recommande n produits avec un meilleur score - Version hybride CSV + OpenFoodFacts"""

        # D'abord essayer les recommandations OpenFoodFacts
        off_recommendations = self.recommend_better_products_from_off(
            current_features, current_score, current_categories, user_profile, n, current_barcode
        )

        # Si on a assez de recommandations OpenFoodFacts, les retourner
        if len(off_recommendations) >= n:
            return off_recommendations

        # Sinon, compléter avec le fichier CSV local
        print(f"🔄 Complément avec la base locale (besoin de {n - len(off_recommendations)} produits supplémentaires)")

        import pandas as pd
        try:
            df = pd.read_csv("off_products_with_prices.csv")
        except Exception as e:
            print(f"Erreur chargement produits locaux: {e}")
            return off_recommendations

        # Exclure le produit actuel et ceux déjà recommandés
        if current_barcode:
            df = df[df['barcode'].astype(str) != str(current_barcode)]

        # Exclure les produits déjà recommandés
        recommended_barcodes = {rec['barcode'] for rec in off_recommendations}
        df = df[~df['barcode'].astype(str).isin(recommended_barcodes)]

        # Calculer scores et filtrer comme avant
        def get_product_score(row):
            try:
                prod_features = {}
                for feature in self.feature_order:
                    if feature.endswith('_100g'):
                        val = row.get(feature, 0.0)
                        try:
                            prod_features[feature] = float(val) if val is not None and str(val).lower() not in ['nan', 'none', ''] else 0.0
                        except:
                            prod_features[feature] = 0.0

                if 'sugar_carb_ratio' in self.feature_order:
                    sugars = prod_features.get('sugars_100g', 0.0)
                    carbs = prod_features.get('carbohydrates_100g', 0.0)
                    prod_features['sugar_carb_ratio'] = sugars / (carbs + 1e-8) if carbs > 0 else 0.0

                base_score = self.predict_score(prod_features)

                if user_profile:
                    product_data = {
                        'product_name': row.get('product_name', ''),
                        'categories_tags': str(row.get('categories_tags', '')).split(',') if row.get('categories_tags') else [],
                        'ingredients_tags': str(row.get('ingredients_tags', '')).split(',') if row.get('ingredients_tags') else []
                    }
                    adjusted_score, warnings, blocked = self.apply_personalized_adjustments(
                        base_score, product_data, prod_features, user_profile
                    )
                    return adjusted_score if not blocked else 0
                else:
                    product_data = {
                        'product_name': row.get('product_name', ''),
                        'categories_tags': str(row.get('categories_tags', '')).split(',') if row.get('categories_tags') else []
                    }
                    adjusted_score = self.apply_category_adjustments(base_score, product_data, prod_features)
                    return adjusted_score
            except Exception as e:
                return 0

        df["yumi_score"] = df.apply(get_product_score, axis=1)
        better_products = df[df["yumi_score"] > current_score + 5]

        # Prendre les meilleurs produits locaux
        remaining_needed = n - len(off_recommendations)
        local_products = better_products.nlargest(remaining_needed, "yumi_score")

        # Ajouter aux recommandations
        for _, row in local_products.iterrows():
            off_recommendations.append({
                'barcode': str(row.get('barcode', '')),
                'product_name': row.get('product_name', 'Nom inconnu'),
                'brands': row.get('brands', ''),
                'yumi_score': round(row['yumi_score'], 1),
                'price': row.get('price', None),
                'nutriscore_grade': '',
                'categories': str(row.get('categories_tags', ''))[:100]
            })

        return off_recommendations[:n]

def main():
    """Fonction principale pour tester la prédiction"""
    # Initialiser le prédicteur
    predictor = YumiPredictor()

    # Test avec exemple manuel
    print("\n" + "="*60)
    print("🧪 TEST AVEC EXEMPLE MANUEL")
    sample_features = {
        "proteins_100g": 8.2,
        "carbohydrates_100g": 65,
        "sugars_100g": 28,
        "fat_100g": 12,
        "fiber_100g": 4.2,
        "salt_100g": 0.8,
        "sodium_100g": 0.32,
        "calcium_100g": 0.05,
        "iron_100g": 0.002,
        "potassium_100g": 0.15,
        "iodine_100g": 0.0,
        "energy_100g": 1600,
        "sugar_carb_ratio": 28 / (65 + 1e-8)
    }
    manual_score = predictor.predict_score(sample_features)
    print(f"📝 Score YUmi manuel: {manual_score:.1f}/100")

    # Tests avec codes-barres réels
    test_barcodes = [
        ("3017620422003", "Nutella"),
        ("3228857000852", "Pain de mie Harrys"),
        ("3263670113815", "Sardines à l'huile"),
        ("5060335632302", "Monster"),
        ("7312040017683", "Vodka"),  # Peut ne pas être disponible

    ]

    print("\n" + "="*60)
    print("🧪 TESTS AVEC CODES-BARRES RÉELS")

    for barcode, expected_name in test_barcodes:
        print(f"\n{'='*50}")
        result = predictor.predict_from_barcode(barcode)

        if result['success']:
            print(f"🍽️  {result['product_name']}")
            print(f"📊 Code-barres: {result['barcode']}")
            print(f"{result['color']} Score YUmi: {result['yumi_score']}/100 (base: {result['base_score']}/100)")
            print(f"💭 {result['interpretation']}")
            if result['nutriscore_grade']:
                print(f"🏷️  Nutriscore officiel: {result['nutriscore_grade'].upper()}")
            if result['brands']:
                print(f"🏭 Marque: {result['brands']}")

            # Afficher les recommandations si disponibles
            if 'recommendations' in result and result['recommendations']:
                print(f"\n💡 RECOMMANDATIONS D'ALTERNATIVES PLUS SAINES:")
                for i, rec in enumerate(result['recommendations'], 1):
                    print(f"   {i}. {rec['product_name']}")
                    print(f"      📊 Score YUmi: {rec['yumi_score']}/100")
                    print(f"      🏭 Marque: {rec['brands']}")
                    print(f"      📱 Code-barres: {rec['barcode']}")
                    if rec.get('price'):
                        print(f"      💰 Prix: {rec['price']}€")
                    print()

            # Afficher les catégories pour debug
            print(f"🏷️  Catégories: {result['categories'][:3]}...")  # Afficher seulement les 3 premières
        else:
            print(f"❌ {result['error']}")

    # Test de la prédiction personnalisée
    print("\n" + "="*60)
    print("🧪 TESTS DE PRÉDICTION PERSONNALISÉE")

    # Importer les classes nécessaires
    from user_profile import (UserProfile, AgeGroup, ActivityLevel, DietaryRestriction,
                              HealthGoal, create_child_profile, create_adult_profile)

    # Créer différents profils utilisateurs de test
    profiles = [
        # Enfant avec allergie aux noix
        create_child_profile("Emma (8 ans)", allergies=["nuts", "peanuts"]),

        # Adulte diabétique
        create_adult_profile(
            "Pierre (45 ans)",
            dietary_restrictions=[DietaryRestriction.DIABETIC],
            health_goals=[HealthGoal.REDUCE_SUGAR, HealthGoal.IMPROVE_HEALTH],
            max_sugar_tolerance=5.0
        ),

        # Adulte sportif qui veut prendre du muscle
        create_adult_profile(
            "Marie (28 ans)",
            activity_level=ActivityLevel.VERY_ACTIVE,
            health_goals=[HealthGoal.BUILD_MUSCLE, HealthGoal.INCREASE_PROTEIN],
            alcohol_allowed=True
        ),

        # Senior avec hypertension
        UserProfile(
            name="Robert (70 ans)",
            age_group=AgeGroup.SENIOR,
            activity_level=ActivityLevel.LIGHT,
            dietary_restrictions=[DietaryRestriction.LOW_SODIUM],
            allergies=[],
            health_goals=[HealthGoal.IMPROVE_HEALTH],
            alcohol_allowed=False,
            max_sodium_tolerance=0.3,
            sodium_sensitivity=0.8
        )
    ]

    # Tester seulement 2 produits pour chaque profil (pour ne pas surcharger)
    test_products = [
        ("3017620422003", "Nutella"),  # Retour au bon code-barres du Nutella
        ("7312040017683", "Vodka")
    ]

    for profile in profiles:
        print(f"\n{'='*60}")
        print(f"👤 PROFIL: {profile.name}")
        print(f"   Age: {profile.age_group.value}, Activité: {profile.activity_level.value}")
        print(f"   Restrictions: {[r.value for r in profile.dietary_restrictions]}")
        print(f"   Allergies: {profile.allergies}")
        print(f"   Objectifs: {[g.value for g in profile.health_goals]}")

        for barcode, product_name in test_products:
            result = predictor.predict_from_barcode_personalized(barcode, profile)

            if result['success']:
                print(f"\n🍽️  {result['product_name']}")
                print(f"{result['color']} Score: {result['yumi_score']}/100 (base: {result['base_score']}/100)")
                print(f"💭 {result['interpretation']}")

                # Afficher les avertissements s'il y en a
                if result['warnings']:
                    for warning in result['warnings']:
                        print(f"   {warning}")

                if result['blocked']:
                    print("   🚫 PRODUIT BLOQUÉ pour ce profil")

                # Afficher les recommandations personnalisées si disponibles
                if 'recommendations' in result and result['recommendations']:
                    print(f"\n💡 RECOMMANDATIONS PERSONNALISÉES POUR {profile.name}:")
                    for i, rec in enumerate(result['recommendations'], 1):
                        print(f"   {i}. {rec['product_name']}")
                        print(f"      📊 Score YUmi: {rec['yumi_score']}/100")
                        print(f"      🏭 Marque: {rec['brands']}")
                        print(f"      📱 Code-barres: {rec['barcode']}")
                        if rec.get('price'):
                            print(f"      💰 Prix: {rec['price']}€")
                        print()
            else:
                print(f"❌ {result['error']}")

        print("-" * 50)

if __name__ == "__main__":
    main()
