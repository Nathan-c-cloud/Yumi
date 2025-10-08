from flask import Flask, request, jsonify
from flask_cors import CORS
from predict_score import YumiPredictor
from user_profile import UserProfile, AgeGroup, ActivityLevel, DietaryRestriction, HealthGoal, create_adult_profile
from product_pricing import ProductPriceGenerator
from datetime import datetime

app = Flask(__name__)

CORS(app)

predictor = YumiPredictor()

# Stockage en mémoire des paniers (en production, utiliser une base de données)
shopping_carts = {}

# Stockage en mémoire des paniers intelligents automatiques
intelligent_carts = {}

# Stockage en mémoire des profils utilisateurs (en production, utiliser une base de données)
user_profiles = {}

# Stockage en mémoire de l'historique des scans (en production, utiliser une base de données)
scan_history = {}

# Stockage en mémoire des recommandations sauvegardées (en production, utiliser une base de données)
saved_recommendations = {}

@app.route("/api/scan", methods=["POST"])
def scan_product():
    data = request.get_json()
    barcode = data.get("barcode")
    user_id = request.headers.get("X-User-ID", "default") # Get user_id from header

    if not barcode:
        return jsonify({"success": False, "error": "Code-barres manquant"}), 400

    # Retrieve user profile from storage
    current_user_profile = user_profiles.get(user_id)

    # Si pas de profil utilisateur, créer un profil par défaut temporaire
    if not current_user_profile:
        current_user_profile = create_adult_profile("Utilisateur par défaut")
        print(f"⚠️ Aucun profil trouvé pour {user_id}, utilisation d'un profil par défaut")

    try:
        result = predictor.predict_from_barcode_personalized(barcode, current_user_profile)

        # Sauvegarder dans l'historique si le scan est réussi
        if result.get("success", True):  # Assume success if not specified
            if user_id not in scan_history:
                scan_history[user_id] = []

            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "barcode": barcode,
                "product_name": result.get("product_name", "Produit inconnu"),
                "brands": result.get("brands", "Marque inconnue"),
                "yumi_score": result.get("yumi_score", 0),
                "nutriscore_grade": result.get("nutriscore_grade", ""),
                "interpretation": result.get("interpretation", ""),
                "color": result.get("color", "")
            }
            scan_history[user_id].append(history_entry)

            # Garder seulement les 50 derniers scans par utilisateur
            if len(scan_history[user_id]) > 50:
                scan_history[user_id] = scan_history[user_id][-50:]

            # NOUVELLE FONCTIONNALITÉ: Sauvegarder automatiquement les recommandations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print(f"🔄 Sauvegarde automatique de {len(recommendations)} recommandations pour {user_id}")
                save_recommendations_automatically(user_id, recommendations, barcode)

                # NOUVEAU: Remplir automatiquement le panier après avoir sauvé les recommandations
                auto_fill_cart_from_recommendations(user_id)

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def save_recommendations_automatically(user_id, recommendations, source_barcode):
    """Sauvegarder automatiquement les recommandations générées lors d'un scan"""
    if user_id not in saved_recommendations:
        saved_recommendations[user_id] = []

    current_time = datetime.now().isoformat()
    saved_count = 0

    for rec in recommendations:
        # Vérifier si cette recommandation n'est pas déjà sauvegardée
        existing = next((item for item in saved_recommendations[user_id]
                        if item["barcode"] == rec.get("barcode")), None)

        if not existing:
            # Générer un prix pour le produit
            price = ProductPriceGenerator.generate_price(
                product_name=rec.get("product_name", ""),
                categories=rec.get("categories", []),
                brands=rec.get("brands", ""),
                nutriscore=rec.get("nutriscore_grade", ""),
                barcode=rec.get("barcode", "")
            )

            recommendation_entry = {
                "barcode": rec.get("barcode", ""),
                "product_name": rec.get("product_name", "Produit inconnu"),
                "brands": rec.get("brands", "Marque inconnue"),
                "yumi_score": rec.get("yumi_score", 0),
                "nutriscore_grade": rec.get("nutriscore_grade", ""),
                "interpretation": rec.get("interpretation", ""),
                "color": rec.get("color", ""),
                "image_url": rec.get("image_url", ""),
                "price": price,  # Nouveau champ prix
                "saved_at": current_time,
                "source": "auto_recommendation",
                "source_scan_barcode": source_barcode,
                "auto_saved": True
            }

            saved_recommendations[user_id].append(recommendation_entry)
            saved_count += 1

    # Garder seulement les 200 dernières recommandations par utilisateur (plus que les scans)
    if len(saved_recommendations[user_id]) > 200:
        # Trier par date pour garder les plus récentes
        saved_recommendations[user_id].sort(key=lambda x: x["saved_at"], reverse=True)
        saved_recommendations[user_id] = saved_recommendations[user_id][:200]

    if saved_count > 0:
        print(f"✅ {saved_count} nouvelles recommandations sauvegardées automatiquement pour {user_id}")

    return saved_count

@app.route("/api/profile", methods=["GET", "POST", "PUT"])
def manage_profile():
    """Gérer le profil utilisateur"""
    user_id = request.headers.get("X-User-ID", "default")

    if request.method == "GET":
        # Récupérer le profil
        profile = user_profiles.get(user_id)
        if profile:
            return jsonify({"success": True, "profile": profile.to_dict()}), 200
        else:
            return jsonify({"success": True, "profile": None}), 200

    elif request.method in ["POST", "PUT"]:
        try:
            data = request.json
            if not data:
                return jsonify({"success": False, "error": "Request body cannot be empty"}), 400
            required_fields = ["name", "age_group", "activity_level"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

            # Ensure enum values are valid
            if data["age_group"].upper() not in AgeGroup.__members__:
                return jsonify({"success": False, "error": f"Invalid age_group: {data['age_group']}"}), 400

            if data["activity_level"].upper() not in ActivityLevel.__members__:
                return jsonify({"success": False, "error": f"Invalid activity_level: {data['activity_level']}"}), 400
            for dr in data.get("dietary_restrictions", []):
                if dr.upper() not in DietaryRestriction.__members__:
                    return jsonify({"success": False, "error": f"Invalid dietary_restriction: {dr}"}), 400
            for hg in data.get("health_goals", []):
                if hg.upper() not in HealthGoal.__members__:
                    return jsonify({"success": False, "error": f"Invalid health_goal: {hg}"}), 400

            # Convertir le budget en float s'il est fourni
            weekly_budget = data.get("weekly_budget", 50.0)
            if weekly_budget is not None:
                try:
                    weekly_budget = float(weekly_budget)
                except (ValueError, TypeError):
                    weekly_budget = 50.0  # Valeur par défaut si conversion échoue

            # Créer le dictionnaire avec le budget corrigé
            profile_data = {
                "name": data["name"],
                "age_group": data["age_group"],
                "activity_level": data["activity_level"],
                "dietary_restrictions": data.get("dietary_restrictions", []),
                "allergies": data.get("allergies", []),
                "health_goals": data.get("health_goals", []),
                "alcohol_allowed": data.get("alcohol_allowed", False),
                "weekly_budget": weekly_budget
            }

            profile = UserProfile.from_dict(profile_data)
            user_profiles[user_id] = profile

            # NOUVEAU: Régénérer automatiquement le panier intelligent quand le profil change
            auto_fill_cart_from_recommendations(user_id)

            return jsonify({"success": True, "message": "Profile saved successfully"}), 200

        except KeyError as e:
            return jsonify({"success": False, "error": f"Missing data for field: {e}"}), 400
        except ValueError as e:
            return jsonify({"success": False, "error": f"Invalid value provided: {e}"}), 400
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement du profil: {str(e)}")  # Log pour debug
            return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500

def auto_fill_cart_from_recommendations(user_id):
    """Remplir automatiquement le panier avec les meilleures recommandations"""
    print(f"🛒 Remplissage automatique du panier pour {user_id}")

    # Construire le panier intelligent
    intelligent_products = build_intelligent_cart(user_id)

    if not intelligent_products:
        print(f"❌ Aucun produit intelligent trouvé pour {user_id}")
        return

    # Initialiser le panier si nécessaire
    if user_id not in shopping_carts:
        shopping_carts[user_id] = []

    # Prendre les 8 meilleurs produits automatiquement
    auto_selected = intelligent_products[:8]
    added_count = 0

    for product in auto_selected:
        barcode = product.get("barcode")
        if not barcode:
            continue

        # Vérifier s'il n'est pas déjà dans le panier
        existing = next((item for item in shopping_carts[user_id] if item["barcode"] == barcode), None)
        if not existing:
            cart_item = {
                "barcode": barcode,
                "product_name": product.get("product_name", ""),
                "brands": product.get("brands", ""),
                "yumi_score": product.get("yumi_score", 0),
                "price": product.get("price", 0.0),  # Ajouter le prix
                "quantity": 1,
                "added_from": "auto_intelligent",
                "suitability_score": product.get("suitability_score", 0),
                "auto_added": True
            }
            shopping_carts[user_id].append(cart_item)
            added_count += 1

    print(f"✅ {added_count} produits ajoutés automatiquement au panier pour {user_id}")

@app.route("/api/checkout", methods=["POST"])
def checkout():
    return jsonify({"success": True, "message": "Commande passée avec succès (simulé)"})

def build_intelligent_cart(user_id):
    """Construire automatiquement un panier intelligent basé sur le profil et les recommandations"""
    user_profile = user_profiles.get(user_id)
    user_recommendations = saved_recommendations.get(user_id, [])

    if not user_profile:
        print(f"❌ Pas de profil pour {user_id}, impossible de créer un panier intelligent")
        return []

    print(f"🧠 Construction du panier intelligent pour {user_id}")
    print(f"👤 Profil: {user_profile.health_goals}, Restrictions: {user_profile.dietary_restrictions}")
    print(f"💰 Budget hebdomadaire: {user_profile.weekly_budget}€")
    print(f"💡 {len(user_recommendations)} recommandations disponibles")

    # Filtrer et scorer les recommandations selon le profil
    suitable_products = []

    for rec in user_recommendations:
        score = rec.get("yumi_score", 0)
        product_name = rec.get("product_name", "").lower()
        price = rec.get("price", 0.0)

        # Score de base
        suitability_score = score

        # Bonus selon les objectifs de santé
        for goal in user_profile.health_goals:
            if goal == HealthGoal.LOSE_WEIGHT:
                if "light" in product_name or "0%" in product_name or "sans sucre" in product_name:
                    suitability_score += 15
                elif "bio" in product_name or "naturel" in product_name:
                    suitability_score += 10
            elif goal == HealthGoal.BUILD_MUSCLE:
                if "protéin" in product_name or "fromage" in product_name:
                    suitability_score += 15
            elif goal == HealthGoal.IMPROVE_HEALTH:
                if "omega" in product_name or "huile d'olive" in product_name:
                    suitability_score += 15

        # Malus pour les restrictions alimentaires (vérification basique)
        penalty = 0
        for restriction in user_profile.dietary_restrictions:
            if restriction == DietaryRestriction.GLUTEN_FREE and "gluten" in product_name:
                penalty -= 50
            elif restriction == DietaryRestriction.LACTOSE_FREE and ("lait" in product_name or "fromage" in product_name):
                penalty -= 50
            elif restriction == DietaryRestriction.VEGETARIAN and ("viande" in product_name or "porc" in product_name):
                penalty -= 50

        final_score = max(0, suitability_score + penalty)

        if final_score >= 60:  # Seuil minimum pour être inclus
            suitable_products.append({
                **rec,
                "suitability_score": final_score,
                "auto_selected": True,
                "selection_reason": f"Score adapté à votre profil: {final_score}/100",
                "price": price
            })

    # Trier par rapport qualité/prix (score d'adéquation / prix)
    def quality_price_ratio(product):
        price = product.get("price", 1.0)
        suitability_score = product.get("suitability_score", 0)
        return suitability_score / price if price > 0 else 0

    suitable_products.sort(key=quality_price_ratio, reverse=True)

    # Filtrer selon le budget si défini
    if user_profile.weekly_budget and user_profile.weekly_budget > 0:
        selected_products = ProductPriceGenerator.filter_products_by_budget(
            suitable_products,
            user_profile.weekly_budget,
            target_percentage=0.8  # Utiliser 80% du budget
        )
        print(f"💰 Filtrage selon budget: {len(selected_products)} produits dans le budget")
    else:
        # Pas de budget défini, prendre les 12 meilleurs
        selected_products = suitable_products[:12]

    print(f"✅ {len(selected_products)} produits sélectionnés automatiquement")

    return selected_products

@app.route("/api/history", methods=["GET", "DELETE", "OPTIONS"])
def manage_scan_history():
    """Gérer l'historique des scans pour un utilisateur"""
    if request.method == "OPTIONS":
        # Gérer la requête preflight CORS
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-User-ID')
        response.headers.add('Access-Control-Allow-Methods', 'GET,DELETE,OPTIONS')
        return response

    user_id = request.headers.get("X-User-ID", "default")

    if request.method == "GET":
        # Récupérer l'historique des scans
        history = scan_history.get(user_id, [])
        # Trier par timestamp décroissant (plus récent en premier)
        history_sorted = sorted(history, key=lambda x: x["timestamp"], reverse=True)

        return jsonify({
            "success": True,
            "history": history_sorted
        }), 200

    elif request.method == "DELETE":
        # Effacer tout l'historique des scans
        if user_id in scan_history:
            scan_history[user_id] = []

        return jsonify({
            "success": True,
            "message": "Historique effacé avec succès"
        }), 200

@app.route("/api/history/<int:item_index>", methods=["DELETE", "OPTIONS"])
def delete_scan_history_item(item_index):
    """Supprimer un élément spécifique de l'historique des scans pour un utilisateur"""
    if request.method == "OPTIONS":
        # Gérer la requête preflight CORS
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-User-ID')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE,OPTIONS')
        return response

    user_id = request.headers.get("X-User-ID", "default")

    if user_id not in scan_history:
        return jsonify({
            "success": False,
            "error": "Aucun historique trouvé pour cet utilisateur"
        }), 404

    history = scan_history[user_id]

    if item_index < 0 or item_index >= len(history):
        return jsonify({
            "success": False,
            "error": "Index d'élément invalide"
        }), 400

    # Supprimer l'élément à l'index spécifié
    deleted_item = history.pop(item_index)

    return jsonify({
        "success": True,
        "message": f"Élément '{deleted_item.get('product_name', 'Produit')}' supprimé avec succès"
    }), 200

@app.route("/api/cart/intelligent", methods=["GET", "POST"])
def manage_intelligent_cart():
    """Gérer le panier intelligent automatique"""
    user_id = request.headers.get("X-User-ID", "default")

    if request.method == "GET":
        # Construire automatiquement le panier intelligent
        intelligent_cart = build_intelligent_cart(user_id)
        intelligent_carts[user_id] = intelligent_cart

        return jsonify({
            "success": True,
            "intelligent_cart": intelligent_cart,
            "message": f"Panier intelligent généré avec {len(intelligent_cart)} produits"
        }, 200)

    elif request.method == "POST":
        # Transférer le panier intelligent vers le panier classique
        data = request.get_json()
        selected_barcodes = data.get("selected_products", [])

        if user_id not in intelligent_carts:
            return jsonify({"success": False, "error": "Aucun panier intelligent trouvé"}), 404

        # Initialiser le panier classique si nécessaire
        if user_id not in shopping_carts:
            shopping_carts[user_id] = []

        added_count = 0
        for barcode in selected_barcodes:
            # Trouver le produit dans le panier intelligent
            product = next((p for p in intelligent_carts[user_id] if p.get("barcode") == barcode), None)
            if product:
                # Vérifier s'il n'est pas déjà dans le panier classique
                existing = next((item for item in shopping_carts[user_id] if item["barcode"] == barcode), None)
                if existing:
                    existing["quantity"] += 1
                else:
                    cart_item = {
                        "barcode": barcode,
                        "product_name": product.get("product_name", ""),
                        "brands": product.get("brands", ""),
                        "yumi_score": product.get("yumi_score", 0),
                        "quantity": 1,
                        "added_from": "intelligent_cart",
                        "suitability_score": product.get("suitability_score", 0)
                    }
                    shopping_carts[user_id].append(cart_item)
                added_count += 1

        return jsonify({
            "success": True,
            "message": f"{added_count} produits ajoutés au panier depuis le panier intelligent"
        }, 200)

@app.route("/api/cart", methods=["GET"])
def get_cart():
    """Récupérer le panier classique"""
    user_id = request.headers.get("X-User-ID", "default")
    cart = shopping_carts.get(user_id, [])

    return jsonify({
        "success": True,
        "cart": cart
    }), 200

@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    """Ajouter un produit au panier classique"""
    user_id = request.headers.get("X-User-ID", "default")
    data = request.get_json()

    barcode = data.get("barcode")
    if not barcode:
        return jsonify({"success": False, "error": "Code-barres manquant"}), 400

    # Initialiser le panier si nécessaire
    if user_id not in shopping_carts:
        shopping_carts[user_id] = []

    # Vérifier si le produit est déjà dans le panier
    existing = next((item for item in shopping_carts[user_id] if item["barcode"] == barcode), None)
    if existing:
        existing["quantity"] += 1
    else:
        cart_item = {
            "barcode": barcode,
            "product_name": data.get("product_name", "Produit inconnu"),
            "brands": data.get("brands", "Marque inconnue"),
            "yumi_score": data.get("yumi_score", 0),
            "quantity": 1,
            "added_from": "manual"
        }
        shopping_carts[user_id].append(cart_item)

    return jsonify({
        "success": True,
        "message": "Produit ajouté au panier"
    }), 200

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    """Supprimer un produit du panier"""
    user_id = request.headers.get("X-User-ID", "default")
    data = request.get_json()

    barcode = data.get("barcode")
    if not barcode:
        return jsonify({"success": False, "error": "Code-barres manquant"}), 400

    if user_id in shopping_carts:
        shopping_carts[user_id] = [item for item in shopping_carts[user_id] if item["barcode"] != barcode]

    return jsonify({
        "success": True,
        "message": "Produit supprimé du panier"
    }), 200

@app.route("/api/cart/update", methods=["POST"])
def update_cart_quantity():
    """Mettre à jour la quantité d'un produit dans le panier"""
    user_id = request.headers.get("X-User-ID", "default")
    data = request.get_json()

    barcode = data.get("barcode")
    quantity = data.get("quantity", 1)

    if not barcode:
        return jsonify({"success": False, "error": "Code-barres manquant"}), 400

    if user_id in shopping_carts:
        for item in shopping_carts[user_id]:
            if item["barcode"] == barcode:
                if quantity <= 0:
                    shopping_carts[user_id].remove(item)
                else:
                    item["quantity"] = quantity
                break

    return jsonify({
        "success": True,
        "message": "Quantité mise à jour"
    }), 200

@app.route("/api/cart/checkout", methods=["POST"])
def checkout_cart():
    """Finaliser la commande"""
    user_id = request.headers.get("X-User-ID", "default")

    if user_id in shopping_carts:
        cart_items = len(shopping_carts[user_id])
        shopping_carts[user_id] = []  # Vider le panier

        return jsonify({
            "success": True,
            "message": f"Commande de {cart_items} articles passée avec succès (simulation)"
        }), 200

    return jsonify({
        "success": False,
        "error": "Panier vide"
    }), 400

print(f"Backend Flask démarré sur http://127.0.0.1:5002 avec CORS activé pour toutes les origines." )




if __name__ == "__main__":
    app.run(debug=True, port=5002)
