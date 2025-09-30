import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils.multiclass import unique_labels
import warnings
warnings.filterwarnings("ignore")

def treinar_e_prever_estado(tabuleiro, modelo_usuario=None):
    # 1️⃣ Carregar dataset
    data = pd.read_csv("tic-tac-toe-clean.csv", header=None)
    X = data.iloc[:, :-1]
    y = data.iloc[:, -1]
    X.columns = [f'pos_{i+1}' for i in range(9)]

    # 2️⃣ Label Encoding para DT e RF
    encoders = {}
    X_label = pd.DataFrame()
    for col in X.columns:
        le = LabelEncoder()
        X_label[col] = le.fit_transform(X[col])
        encoders[col] = le

    y_encoder = LabelEncoder()
    y_encoded = y_encoder.fit_transform(y)

    # 3️⃣ OneHotEncoder para k-NN e MLP
    ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_ohe = ohe.fit_transform(X)

    # 4️⃣ Divisão treino/val/test
    X_temp_label, X_test_label, y_temp, y_test = train_test_split(
        X_label, y_encoded, test_size=0.2, random_state=42)
    X_train_label, X_val_label, y_train, y_val = train_test_split(
        X_temp_label, y_temp, test_size=0.2, random_state=42 )

    X_temp_ohe, X_test_ohe, _, _ = train_test_split(
        X_ohe, y_encoded, test_size=0.2, random_state=42)
    X_train_ohe, X_val_ohe, _, _ = train_test_split(
        X_temp_ohe, y_temp, test_size=0.2, random_state=42)

    # Normalização
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_ohe)
    X_val_scaled = scaler.transform(X_val_ohe)
    X_test_scaled = scaler.transform(X_test_ohe)

    # 5️⃣ Treinar modelos
    knn = KNeighborsClassifier(n_neighbors=10)
    mlp = MLPClassifier(
        hidden_layer_sizes=(10,50),
        max_iter=1000,
        activation='relu',
        random_state=42,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=50
    )
    dt = DecisionTreeClassifier(random_state=42)
    rf = RandomForestClassifier(n_estimators=1000, random_state=42)

    knn.fit(X_train_scaled, y_train)
    mlp.fit(X_train_scaled, y_train)
    dt.fit(X_train_label, y_train)
    rf.fit(X_train_label, y_train)

    # 6️⃣ Avaliar todos os modelos
    modelos = {'k-NN': knn, 'MLP': mlp, 'DecisionTree': dt, 'RandomForest': rf}
    resultados = {}
    for nome, modelo in modelos.items():
        X_test_model = X_test_scaled if nome in ['k-NN','MLP'] else X_test_label.values
        y_pred = modelo.predict(X_test_model)

        labels_presentes = unique_labels(y_test, y_pred)
        report = classification_report(y_test, y_pred, labels=labels_presentes, output_dict=True)

        acc = accuracy_score(y_test, y_pred)
        resultados[nome] = {'accuracy': acc, 'report': report}

    # Mostrar tabela com métricas
    print("\n===== Métricas de todos os modelos =====")
    for nome, res in resultados.items():
        f1_macro = res['report']['macro avg']['f1-score']
        print(f"\nModelo: {nome}")
        print(f"Accuracy: {res['accuracy']:.4f}")
        print(f"F1 Macro: {f1_macro:.4f}")
        df_report = pd.DataFrame(res['report']).transpose()
        print(df_report[['precision','recall','f1-score','support']])

    # 7️⃣ Escolher modelo
    if modelo_usuario is not None:
        melhor_modelo_nome = modelo_usuario
        print(f"\nUsuário escolheu o modelo: {melhor_modelo_nome}")
    else:
        melhor_modelo_nome = max(resultados, key=lambda m: resultados[m]['report']['macro avg']['f1-score'])
        print(f"\nModelo escolhido automaticamente com maior F1 macro: {melhor_modelo_nome}")

    melhor_modelo = modelos[melhor_modelo_nome]

    # 8️⃣ Prever novo tabuleiro
    tab_df_label = pd.DataFrame([tabuleiro], columns=X.columns)
    for col in tab_df_label.columns:
        val = tab_df_label[col][0]
        if val not in ['b','o','x']:
            val = 'b'
        tab_df_label[col] = encoders[col].transform([val])

    tab_ohe = ohe.transform([tabuleiro])
    tab_input = scaler.transform(tab_ohe) if melhor_modelo_nome in ['k-NN','MLP'] else tab_df_label.values
    pred_encoded = melhor_modelo.predict(tab_input)[0]
    pred = y_encoder.inverse_transform([pred_encoded])[0]
    print(f"\nPrevisão do estado do tabuleiro pelo modelo {melhor_modelo_nome}: {pred}")

    return melhor_modelo_nome, pred
