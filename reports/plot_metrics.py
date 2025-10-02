import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent
METRICS_FILE = OUTPUT_DIR / "model_metrics.json"


def add_value_labels(ax, fmt="{:.2f}"):
    """Anota os valores no topo de cada barra."""
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=8)


def main():
    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de métricas não encontrado em {METRICS_FILE}. Execute a coleta antes de gerar gráficos."
        )

    with METRICS_FILE.open(encoding="utf-8") as fp:
        metrics = json.load(fp)

    # Tabela com métricas globais por modelo
    overall_rows = []
    per_class_rows = []
    for model_name, model_metrics in metrics.items():
        overall_rows.append(
            {
                "model": model_name,
                "accuracy": model_metrics["accuracy"],
                "macro_f1": model_metrics["macro_f1"],
            }
        )
        for class_name, class_metrics in model_metrics["per_class"].items():
            per_class_rows.append(
                {
                    "model": model_name,
                    "class": class_name,
                    "f1": class_metrics["f1"],
                }
            )

    overall_df = pd.DataFrame(overall_rows).set_index("model")
    per_class_df = pd.DataFrame(per_class_rows)

    # Gráfico 1: acurácia e F1 macro por modelo
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    overall_df[["accuracy", "macro_f1"]].plot(kind="bar", ax=ax1, color=["#1f77b4", "#ff7f0e"])
    ax1.set_ylim(0, 1)
    ax1.set_ylabel("Pontuação")
    ax1.set_title("Desempenho global por modelo")
    ax1.legend(["Acurácia", "F1 Macro"], loc="lower right")
    add_value_labels(ax1)
    fig1.tight_layout()
    fig1.savefig(OUTPUT_DIR / "overall_metrics.png", dpi=300)

    # Gráfico 2: F1 por classe em cada modelo
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    pivot = per_class_df.pivot(index="class", columns="model", values="f1")
    pivot.plot(kind="bar", ax=ax2)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("F1 por classe")
    ax2.set_title("Comparação de F1 por classe entre modelos")
    ax2.legend(title="Modelo", bbox_to_anchor=(1.02, 1), loc="upper left")
    add_value_labels(ax2)
    fig2.tight_layout()
    fig2.savefig(OUTPUT_DIR / "f1_per_class.png", dpi=300)

    print("Gráficos salvos em:")
    print(OUTPUT_DIR / "overall_metrics.png")
    print(OUTPUT_DIR / "f1_per_class.png")


if __name__ == "__main__":
    main()
