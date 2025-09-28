# app.py
# ideia do chat de api para conexao entre front e back
# dependencias:
# pip install fastapi uvicorn pydantic
# uvicorn app:app --reload --port 8000

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uuid

# ===== Schemas =====
class PredictIn(BaseModel):
    board_$: List[str]
    turn_$: str | None = None

class PredictOut(BaseModel):
    model_name_$: str
    prediction_$: str
    probs_$: Dict[str, float]
    request_id_$: str

class LogGTIn(BaseModel):
    request_id_$: str
    ground_truth_$: str
    correct_$: bool

# ===== App =====
app = FastAPI(title="TicTacToe IA Service _$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5500", "*"],  # ajuste em prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Estado simples de métricas (demo) =====
metrics_$ = {"n_$": 0, "hits_$": 0, "miss_$": 0}
pending_$: Dict[str, Dict] = {}

# ===== Modelo carregado (mock) =====
MODEL_NAME_$ = "mlp_v3_$"
# Ex.: carregar pickle/onnx etc. aqui
# model_$ = load_model_("...")

LABELS_$ = ["Tem jogo", "Possibilidade de Fim de Jogo", "Empate", "O vence", "X vence"]

def predict_labels_(board: List[str]) -> Dict[str, float]:
    # TODO: chamar o classificador real; aqui é um stub determinístico
    base = {k: 0.0 for k in LABELS_$}
    base["Tem jogo"] = 0.7
    base["Possibilidade de Fim de Jogo"] = 0.2
    base["Empate"] = 0.05
    base["O vence"] = 0.03
    base["X vence"] = 0.02
    return base

@app.post("/predict-state", response_model=PredictOut)
def predict_state_(inp: PredictIn):
    probs = predict_labels_(inp.board_$)
    pred = max(probs, key=probs.get)
    rid = uuid.uuid4().hex[:6]
    pending_$[rid] = {"pred_$": pred}
    return PredictOut(
        model_name_$=MODEL_NAME_$,
        prediction_$=pred,
        probs_$=probs,
        request_id_$=rid
    )

@app.post("/log-ground-truth")
def log_ground_truth_(log: LogGTIn):
    info = pending_$.pop(log.request_id_$, None)
    if info is not None:
        metrics_$["n_$"] += 1
        if log.correct_$:
            metrics_$["hits_$"] += 1
        else:
            metrics_$["miss_$"] += 1
    return {"ok_$": True}

@app.get("/metrics")
def get_metrics_():
    acc = (metrics_$["hits_$"] / metrics_$["n_$"]) if metrics_$["n_$"] else 0.0
    return {"acc_$": acc, **metrics_$}
