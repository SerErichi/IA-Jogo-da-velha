import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent
METRICS_FILE = OUTPUT_DIR / "model_metrics.json"
DATASET_FILE = OUTPUT_DIR.parent / "tic_tac_toe_with_threats_and_draws.csv"


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

    # Gráfico 2: Acurácia por modelo
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    overall_df[["accuracy"]].plot(kind="bar", ax=ax2, legend=False, color=["#1f77b4"])
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Acurácia")
    ax2.set_title("Acurácia por modelo")
    add_value_labels(ax2)
    fig2.tight_layout()
    fig2.savefig(OUTPUT_DIR / "accuracy_by_model.png", dpi=300)

    # Gráfico 3: F1 macro por modelo
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    overall_df[["macro_f1"]].plot(kind="bar", ax=ax3, legend=False, color=["#ff7f0e"])
    ax3.set_ylim(0, 1)
    ax3.set_ylabel("F1 Macro")
    ax3.set_title("F1 Macro por modelo")
    add_value_labels(ax3)
    fig3.tight_layout()
    fig3.savefig(OUTPUT_DIR / "macro_f1_by_model.png", dpi=300)

    # Gráfico 4: F1 por classe em cada modelo
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    pivot = per_class_df.pivot(index="class", columns="model", values="f1")
    pivot.plot(kind="bar", ax=ax4)
    ax4.set_ylim(0, 1)
    ax4.set_ylabel("F1 por classe")
    ax4.set_title("Comparação de F1 por classe entre modelos")
    ax4.legend(title="Modelo", bbox_to_anchor=(1.02, 1), loc="upper left")
    add_value_labels(ax4)
    fig4.tight_layout()
    fig4.savefig(OUTPUT_DIR / "f1_per_class.png", dpi=300)

    # Gráfico 5: melhores resultados consolidados
    metric_columns = {"Acurácia": "accuracy", "F1 Macro": "macro_f1"}
    best_metrics = {
        display: overall_df[column].idxmax()
        for display, column in metric_columns.items()
    }
    best_values = {
        display: overall_df.loc[model, metric_columns[display]]
        for display, model in best_metrics.items()
    }

    fig5, ax5 = plt.subplots(figsize=(6, 4))
    bars = ax5.bar(best_metrics.keys(), best_values.values(), color=["#2ca02c", "#d62728"])
    ax5.set_ylim(0, 1)
    ax5.set_ylabel("Pontuação")
    ax5.set_title("Melhores resultados por métrica")
    for bar, (metric, model) in zip(bars, best_metrics.items()):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width() / 2, height + 0.01, f"{model} ({height:.2f})",
                 ha="center", va="bottom", fontsize=8)
    fig5.tight_layout()
    fig5.savefig(OUTPUT_DIR / "best_metrics.png", dpi=300)

    # Gráfico 6: distribuição de amostras por classe no dataset
    if DATASET_FILE.exists():
        df_dataset = pd.read_csv(DATASET_FILE, header=0)
        target_column = df_dataset.columns[-1]
        class_counts = df_dataset[target_column].value_counts().sort_values(ascending=False)

        fig6, ax6 = plt.subplots(figsize=(8, 5))
        class_counts.plot(kind="bar", ax=ax6, color="#9467bd")
        ax6.set_ylabel("Número de amostras")
        ax6.set_xlabel("Classe")
        ax6.set_title("Distribuição de amostras por classe")
        for bar in ax6.patches:
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width() / 2, height + max(class_counts) * 0.01,
                     f"{int(height)}", ha="center", va="bottom", fontsize=8)
        fig6.tight_layout()
        fig6.savefig(OUTPUT_DIR / "class_distribution.png", dpi=300)
    else:
        print(f"Aviso: dataset não encontrado em {DATASET_FILE}, gráfico de distribuição não gerado.")

    print("Gráficos salvos em:")
    generated_files = [
        "overall_metrics.png",
        "accuracy_by_model.png",
        "macro_f1_by_model.png",
        "f1_per_class.png",
        "best_metrics.png",
    ]
    if (OUTPUT_DIR / "class_distribution.png").exists():
        generated_files.append("class_distribution.png")
    for name in generated_files:
        print(OUTPUT_DIR / name)


if __name__ == "__main__":
    main()
