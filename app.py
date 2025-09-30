from flask import Flask, request, jsonify, send_from_directory, abort

app = Flask(__name__, static_folder="static", static_url_path="")

# -------------------- utilidades de estado real --------------------
WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),
             (0,3,6),(1,4,7),(2,5,8),
             (0,4,8),(2,4,6)]

def winner_of(b):
    for a,c,d in WIN_LINES:
        if b[a] != "b" and b[a] == b[c] == b[d]:
            return b[a]  # "x" ou "o"
    return None

def has_threat(b):
    for a,c,d in WIN_LINES:
        trio = [b[a], b[c], b[d]]
        if trio.count("b") == 1 and (trio.count("x") == 2 or trio.count("o") == 2):
            return True
    return False

def label_of(b):
    w = winner_of(b)
    if w == "x": return "X vence"
    if w == "o": return "O vence"
    if b.count("b") == 0: return "Empate"
    if has_threat(b): return "Possibilidade de Fim de Jogo"
    return "Tem jogo"

# -------------------- "modelos" (stubs) --------------------
# Aqui você troca pelo seu MLP/KNN/Árvore reais.
def predict_mlp(board, turn=None):
    label = label_of(board)
    probs = {"Tem jogo": 0.68, "Possibilidade de Fim de Jogo": 0.2, "Empate": 0.06, "O vence": 0.03, "X vence": 0.03}
    probs[label] = max(probs.values(), 0.9)
    return {"model_name": "MLP", "prediction": label, "probs": probs}

def predict_knn(board, turn=None):
    label = label_of(board)
    probs = {"Tem jogo": 0.60, "Possibilidade de Fim de Jogo": 0.25, "Empate": 0.08, "O vence": 0.04, "X vence": 0.03}
    probs[label] = max(probs.values(), 0.9)
    return {"model_name": "k-NN", "prediction": label, "probs": probs}

def predict_arvore(board, turn=None):
    label = label_of(board)
    probs = {"Tem jogo": 0.65, "Possibilidade de Fim de Jogo": 0.22, "Empate": 0.07, "O vence": 0.03, "X vence": 0.03}
    probs[label] = max(probs.values(), 0.9)
    return {"model_name": "Árvore de Decisão", "prediction": label, "probs": probs}

PREDICTORS = {
    "mlp": predict_mlp,
    "knn": predict_knn,
    "arvore": predict_arvore,   # sem acento para a rota
}

# -------------------- rotas --------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.post("/predict/<modelo>")
def predict_route(modelo):
    modelo = (modelo or "").lower()
    if modelo not in PREDICTORS:
        abort(404, description="Modelo inválido. Use: mlp, knn ou arvore.")
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if not isinstance(board, list) or len(board) != 9 or not all(v in {"x","o","b"} for v in board):
        abort(400, description="Payload inválido: envie {'board': ['x'|'o'|'b'] * 9, 'turn': 'x'|'o' opcional}")
    turn = data.get("turn")
    out = PREDICTORS[modelo](board, turn)
    return jsonify(out)

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
