from flask import Flask, request, jsonify
from flask_cors import CORS
from predict_score import YumiPredictor
from user_profile import UserProfile, AgeGroup, ActivityLevel, DietaryRestriction, HealthGoal, create_adult_profile

app = Flask(__name__)

CORS(app)

predictor = YumiPredictor()

# Stockage en mémoire des paniers (en production, utiliser une base de données)
shopping_carts = {}

# Stockage en mémoire des profils utilisateurs (en production, utiliser une base de données)
user_profiles = {}

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

print(f"Backend Flask démarré sur http://127.0.0.1:5002 avec CORS activé pour toutes les origines." )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
