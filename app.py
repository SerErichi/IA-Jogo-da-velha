from flask import Flask, request, jsonify, send_from_directory, abort
from modelos import treinar_e_prever_estado

app = Flask(__name__, static_folder="static", static_url_path="")

# -------------------- rotas --------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.post("/predict/<modelo>")
def predict_route(modelo):
    modelo = (modelo or "").lower()
    modelos_validos = {"mlp": "MLP", "knn": "k-NN", "arvore": "DecisionTree", "rf": "RandomForest"}

    if modelo not in modelos_validos:
        abort(404, description="Modelo inválido. Use: mlp, knn, arvore. ou random forest")

    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if not isinstance(board, list) or len(board) != 9 or not all(v in {"x","o","b"} for v in board):
        abort(400, description="Payload inválido: envie {'board': ['x'|'o'|'b'] * 9, 'turn': 'x'|'o' opcional}")

    # chama função real de modelos.py
    melhor_modelo, pred = treinar_e_prever_estado(board, modelos_validos[modelo])

    return jsonify({
        "model_name": melhor_modelo,
        "prediction": pred
    })

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
