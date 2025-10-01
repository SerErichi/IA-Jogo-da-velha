// === Config ===
const API_BASE = "http://127.0.0.1:8000"; // mesma origem -> fetch("/predict/<modelo>")

// === Estado do jogo ===
let board = Array(9).fill("b"); // "x" | "o" | "b"
let currentPlayer = "x";
let gameOver = false;

// métricas locais (por modelo, opcionalmente poderíamos separar por modelo)
let totalPreds = 0;
let hits = 0;

const boardEl = document.getElementById("board");
const buttons = Array.from(boardEl.querySelectorAll("button"));
const whoTurnEl = document.getElementById("who-turn");
const statusPredEl = document.getElementById("status-pred");
const statusRealEl = document.getElementById("status-real");
const hitsTotalEl = document.getElementById("hits-total");
const accEl = document.getElementById("acc");
const resetBtn = document.getElementById("reset-btn");
const modelSelectEl = document.getElementById("model-select");

// === Helpers ===
const WIN_LINES = [
  [0,1,2],[3,4,5],[6,7,8],
  [0,3,6],[1,4,7],[2,5,8],
  [0,4,8],[2,4,6]
];

function coordToIndex(c){ const [i,j]=c.split(",").map(Number); return 3*i+j; }

function render(){
  buttons.forEach((btn, i) => {
    const v = board[i];
    btn.textContent = v==="b" ? "" : v.toUpperCase();
    btn.disabled = v!=="b" || gameOver;
  });
  whoTurnEl.textContent = gameOver ? "—" : currentPlayer.toUpperCase();
}

function emptyIndexes(b=board){ return b.map((v,i)=>v==="b"?i:null).filter(i=>i!==null); }

function winnerOf(b=board){
  for(const [a,c,d] of WIN_LINES) if(b[a]!=="b" && b[a]===b[c] && b[c]===b[d]) return b[a];
  return null;
}

function hasThreat(b=board){
  for(const [a,c,d] of WIN_LINES){
    const trio=[b[a],b[c],b[d]];
    const e = trio.filter(v=>v==="b").length;
    const x = trio.filter(v=>v==="x").length;
    const o = trio.filter(v=>v==="o").length;
    if(e===1 && (x===2 || o===2)) return true;
  }
  return false;
}

function gameStateLabel(b=board){
  const w = winnerOf(b);
  if(w==="x") return "X vence";
  if(w==="o") return "O vence";
  if(emptyIndexes(b).length===0) return "Empate";
  if(hasThreat(b)) return "Possibilidade de Fim de Jogo";
  return "Tem jogo";
}

function updateMetricsUI(){
  hitsTotalEl.textContent = `${hits}/${totalPreds}`;
  const acc = totalPreds ? Math.round((hits/totalPreds)*100) : 0;
  accEl.textContent = `${acc}%`;
}

// === Comunicação com Flask (por modelo) ===
function currentModel(){
  return modelSelectEl.value; // "mlp" | "knn" | "arvore"
}

async function avaliarEstadoAPI(boardArr, turn=currentPlayer){
  const modelo = currentModel();
  try{
    const res = await fetch(`${API_BASE}/predict/${modelo}`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ board: boardArr, turn })
    });
    if(!res.ok) throw new Error(await res.text());
    const data = await res.json(); // {model_name, prediction, probs}

    // estado real local
    const real = gameStateLabel(boardArr);
    statusRealEl.textContent = real;

    // predição
    statusPredEl.textContent = `${data.prediction} (${data.model_name})`;

    // contabilizador de acertos
    totalPreds += 1;
    if (data.prediction === real) hits += 1;
    updateMetricsUI();

    return data;
  }catch(err){
    statusPredEl.textContent = "API offline";
    // mesmo se offline, mostramos estado real
    statusRealEl.textContent = gameStateLabel(boardArr);
    return null;
  }
}

// === Jogo ===
window.jogada = async function(coordStr){
  if(gameOver) return;
  const idx = coordToIndex(coordStr);
  if(board[idx] !== "b") return;

  // Humano (X)
  board[idx] = "x";
  currentPlayer = "o";
  render();
  await avaliarEstadoAPI(board, "o");

  // fim após humano?
  const afterHuman = gameStateLabel(board);
  if(["X vence","O vence","Empate"].includes(afterHuman)){
    gameOver = true; render(); return;
  }

  // Máquina (O) aleatória (placeholder)
  await new Promise(r=>setTimeout(r,200));
  const empty = emptyIndexes();
  if(empty.length){
    const choice = empty[Math.random()*empty.length|0];
    board[choice] = "o";
  }
  currentPlayer = "x";
  render();
  await avaliarEstadoAPI(board, "x");

  // fim após máquina?
  const afterBot = gameStateLabel(board);
  if(["X vence","O vence","Empate"].includes(afterBot)){
    gameOver = true; render();
  }
};

function resetGame(){
  board = Array(9).fill("b");
  currentPlayer = "x";
  gameOver = false;
  statusPredEl.textContent = "—";
  statusRealEl.textContent = "—";
  render();
  // opcional: não zeramos o contador de acertos para acompanhar sessão;
  // se quiser zerar junto com a partida, descomente:
  // hits = 0; totalPreds = 0; updateMetricsUI();

  avaliarEstadoAPI(board, currentPlayer); // estado inicial
}

resetBtn.addEventListener("click", resetGame);

// mudar modelo no meio da sessão não reseta contagem (mantemos histórico)
modelSelectEl.addEventListener("change", () => {
  // reavalia o estado atual com o modelo selecionado
  avaliarEstadoAPI(board, currentPlayer);
});

render();
updateMetricsUI();
avaliarEstadoAPI(board, currentPlayer);
