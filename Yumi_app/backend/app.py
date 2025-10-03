from flask import Flask, request, jsonify
from flask_cors import CORS
from predict_score import YumiPredictor
from user_profile import UserProfile, AgeGroup, ActivityLevel, DietaryRestriction, HealthGoal, create_adult_profile
from datetime import datetime

app = Flask(__name__)

CORS(app)

predictor = YumiPredictor()

# Stockage en mémoire des paniers (en production, utiliser une base de données)
shopping_carts = {}

# Stockage en mémoire des profils utilisateurs (en production, utiliser une base de données)
user_profiles = {}

# Stockage en mémoire de l'historique des scans (en production, utiliser une base de données)
scan_history = {}

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

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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

            profile = UserProfile.from_dict(data)
            user_profiles[user_id] = profile

            return jsonify({"success": True, "message": "Profile saved successfully"}), 200

        except KeyError as e:
            return jsonify({"success": False, "error": f"Missing data for field: {e}"}), 400
        except ValueError as e:
            return jsonify({"success": False, "error": f"Invalid value provided: {e}"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/api/cart", methods=["GET", "POST", "DELETE"])
def manage_cart():
    if request.method == "GET":
        return jsonify({"cart_items": []})
    elif request.method == "POST":
        item = request.get_json()
        return jsonify({"success": True, "message": "Produit ajouté au panier", "item": item})
    elif request.method == "DELETE":
        item_id = request.args.get("item_id")
        return jsonify({"success": True, "message": f"Produit {item_id} retiré du panier"})

@app.route("/api/checkout", methods=["POST"])
def checkout():
    return jsonify({"success": True, "message": "Commande passée avec succès (simulé)"})

@app.route("/api/history", methods=["GET"])
def get_scan_history():
    """Récupérer l'historique des scans pour un utilisateur"""
    user_id = request.headers.get("X-User-ID", "default")

    history = scan_history.get(user_id, [])
    # Trier par timestamp décroissant (plus récent en premier)
    history_sorted = sorted(history, key=lambda x: x["timestamp"], reverse=True)

    return jsonify({
        "success": True,
        "history": history_sorted
    }), 200

@app.route("/api/history/<int:item_index>", methods=["DELETE"])
def delete_scan_history_item():
    """Supprimer un élément spécifique de l'historique des scans pour un utilisateur"""
    user_id = request.headers.get("X-User-ID", "default")
    item_index = int(request.view_args.get("item_index"))

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

@app.route("/api/history", methods=["DELETE"])
def clear_scan_history():
    """Effacer l'historique des scans pour un utilisateur"""
    user_id = request.headers.get("X-User-ID", "default")

    if user_id in scan_history:
        scan_history[user_id] = []

    return jsonify({
        "success": True,
        "message": "Historique effacé avec succès"
    }), 200

print(f"Backend Flask démarré sur http://127.0.0.1:5002 avec CORS activé pour toutes les origines." )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
