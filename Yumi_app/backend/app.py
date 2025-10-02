from flask import Flask, request, jsonify
from flask_cors import CORS
from predict_score import YumiPredictor
from user_profile import UserProfile, create_adult_profile

app = Flask(__name__)

# Configuration de CORS pour autoriser les requêtes depuis le frontend React
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}} )

predictor = YumiPredictor()

# Simuler un profil utilisateur par défaut pour les tests
default_user_profile = create_adult_profile("Default User")

@app.route("/api/scan", methods=["POST"])
def scan_product():
    data = request.get_json()
    barcode = data.get("barcode")
    user_profile_data = data.get("user_profile")

    if not barcode:
        return jsonify({"success": False, "error": "Code-barres manquant"}), 400

    # Créer un objet UserProfile à partir des données reçues
    # Si user_profile_data est None ou vide, utiliser le profil par défaut
    if user_profile_data:
        current_user_profile = UserProfile.from_dict(user_profile_data)
    else:
        current_user_profile = default_user_profile

    try:
        result = predictor.predict_from_barcode_personalized(barcode, current_user_profile)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/profile", methods=["GET", "POST"])
def manage_profile():
    if request.method == "GET":
        return jsonify(default_user_profile.to_dict())
    elif request.method == "POST":
        data = request.get_json()
        default_user_profile.update_from_dict(data)
        return jsonify({"success": True, "message": "Profil mis à jour", "profile": default_user_profile.to_dict()})

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

if __name__ == "__main__":
    app.run(debug=True, port=5002)



