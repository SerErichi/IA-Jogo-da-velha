// ====== CONFIG ======
const API_BASE = "http://localhost:8000"; // ajuste se necessário

// ====== ESTADO DO JOGO ======
/**
 * Representação do tabuleiro como array de 9 elementos: "x" | "o" | "b"
 * Índices:  0 1 2
 *           3 4 5
 *           6 7 8
 */
let board = Array(9).fill("b");
let currentPlayer = "x"; // humano começa
let gameOver = false;
let lastRequestId = null;

// cache de elementos
const boardEl = document.getElementById("board");
const buttons = Array.from(boardEl.querySelectorAll("button"));
const whoTurnEl = document.getElementById("who-turn");
const statusModelEl = document.getElementById("status-model");
const statusPredEl = document.getElementById("status-pred");
const statusRealEl = document.getElementById("status-real");
const metricsAccEl = document.getElementById("metrics-acc");
const metricsCountEl = document.getElementById("metrics-count");
const apiBadgeEl = document.getElementById("api-badge");
const resetBtn = document.getElementById("reset-btn");

// ====== UTILS ======
const WIN_LINES = [
  [0,1,2],[3,4,5],[6,7,8],
  [0,3,6],[1,4,7],[2,5,8],
  [0,4,8],[2,4,6]
];

function render() {
  // aplica "X" / "O" nos botões e desabilita células preenchidas
  buttons.forEach((btn, idx) => {
    const v = board[idx];
    if (v === "x") {
      btn.textContent = "X";
      btn.disabled = true;
    } else if (v === "o") {
      btn.textContent = "O";
      btn.disabled = true;
    } else {
      btn.textContent = "";
      btn.disabled = gameOver; // se acabou, trava tudo
    }
  });
  whoTurnEl.textContent = currentPlayer.toUpperCase();
}

function emptyIndexes(b = board) {
  const res = [];
  for (let i = 0; i < 9; i++) if (b[i] === "b") res.push(i);
  return res;
}

function winnerOf(b = board) {
  for (const [a, c, d] of WIN_LINES) {
    if (b[a] !== "b" && b[a] === b[c] && b[c] === b[d]) return b[a]; // "x" | "o"
  }
  return null;
}

function hasThreat(b = board) {
  // "Possibilidade de Fim de Jogo" = alguma linha com 2 iguais + 1 vazio
  for (const [a, c, d] of WIN_LINES) {
    const trio = [b[a], b[c], b[d]];
    const xs = trio.filter(v => v === "x").length;
    const os = trio.filter(v => v === "o").length;
    const bs = trio.filter(v => v === "b").length;
    if (bs === 1 && (xs === 2 || os === 2)) return true;
  }
  return false;
}

function gameStateLabel(b = board) {
  const w = winnerOf(b);
  if (w === "x") return "X vence";
  if (w === "o") return "O vence";
  if (emptyIndexes(b).length === 0) return "Empate";
  if (hasThreat(b)) return "Possibilidade de Fim de Jogo";
  return "Tem jogo";
}

// ====== API ======
async function pingApi() {
  try {
    const r = await fetch(`${API_BASE}/metrics`, { method: "GET" });
    if (!r.ok) throw 0;
    apiBadgeEl.textContent = "online";
    apiBadgeEl.style.color = "green";
  } catch {
    apiBadgeEl.textContent = "offline";
    apiBadgeEl.style.color = "red";
  }
}

async function avaliarEstado(boardArr, turn = currentPlayer) {
  // boardArr: ["x","o","b",...]
  try {
    const res = await fetch(`${API_BASE}/predict-state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board_$: boardArr, turn_$: turn })
    });
    if (!res.ok) throw new Error("Falha na predição");
    const data = await res.json(); // { model_name_$, prediction_$, probs_$, request_id_$ }
    lastRequestId = data.request_id_$ || null;
    statusModelEl.textContent = data.model_name_$ ?? "—";
    statusPredEl.textContent = data.prediction_$ ?? "—";

    // calcula a verdade do estado localmente e loga no backend
    const real = gameStateLabel(boardArr);
    statusRealEl.textContent = real;

    if (lastRequestId) {
      const correct = (real === data.prediction_$);
      await fetch(`${API_BASE}/log-ground-truth`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id_$: lastRequestId,
          ground_truth_$: real,
          correct_$: correct
        })
      }).catch(() => { /* silencioso */ });
    }

    // atualiza métricas
    try {
      const mRes = await fetch(`${API_BASE}/metrics`);
      if (mRes.ok) {
        const m = await mRes.json(); // { acc_$, n_$, hits_$, miss_$ }
        const accPct = Math.round((m.acc_$ || 0) * 100);
        metricsAccEl.textContent = `${accPct}%`;
        metricsCountEl.textContent = `${m.hits_$ || 0}/${m.n_$ || 0}`;
      }
    } catch { /* ignore */ }

  } catch (e) {
    // falha na API: informa e mostra apenas estado real
    apiBadgeEl.textContent = "offline";
    apiBadgeEl.style.color = "red";
    statusModelEl.textContent = "API indisponível";
    statusPredEl.textContent = "—";
    statusRealEl.textContent = gameStateLabel(boardArr);
  }
}

// ====== LOOP DE JOGO ======
window.jogada = async function (idxStr) {
  if (gameOver) return;

  const idx = parseInt(idxStr, 10);

  if (board[idx] !== "b") return; // célula já usada

  // jogada do humano (X)
  board[idx] = "x";
  currentPlayer = "o";
  render();

  // avalia estado após a jogada do humano
  await avaliarEstado(board, "o");

  // checa término após humano
  const realAfterHuman = gameStateLabel(board);
  if (realAfterHuman !== "Tem jogo" && realAfterHuman !== "Possibilidade de Fim de Jogo") {
    finalizarJogo();
    return;
  }

  // jogada simples da máquina (O): aleatória
  await delay(250); // pequeno respiro visual
  const empty = emptyIndexes();
  if (empty.length > 0) {
    const choice = empty[Math.floor(Math.random() * empty.length)];
    board[choice] = "o";
  }
  currentPlayer = "x";
  render();

  // avalia estado após a jogada da máquina
  await avaliarEstado(board, "x");

  // checa término
  const finalState = gameStateLabel(board);
  if (finalState !== "Tem jogo" && finalState !== "Possibilidade de Fim de Jogo") {
    finalizarJogo();
    return;
  }
};

function finalizarJogo() {
  gameOver = true;
  render();
  whoTurnEl.textContent = "—";
}

function resetGame() {
  board = Array(9).fill("b");
  currentPlayer = "x";
  gameOver = false;
  lastRequestId = null;
  statusPredEl.textContent = "—";
  statusRealEl.textContent = "—";
  // mantém modelo e métricas exibidos
  render();
  avaliarEstado(board, currentPlayer); // avalia o estado inicial (vazio)
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ====== BOOT ======
resetBtn.addEventListener("click", resetGame);
render();
pingApi();
avaliarEstado(board, currentPlayer);
