import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, auc, classification_report
from sklearn.preprocessing import label_binarize

# Constants
DATA_PATH = "data/ml_ready_data.csv"
MODEL_DIR = "models/"
MODEL_PATH = os.path.join(MODEL_DIR, "xgb_model.pkl")
OUTPUT_DIR = "app/components/"
CM_PATH = os.path.join(OUTPUT_DIR, "confusion_matrix.png")
ROC_PATH = os.path.join(OUTPUT_DIR, "roc_curve.png")
TARGET_COL = "Risk_Level"


def generate_publication_plots():
    # 1. Load dataset and pipeline
    print("[INFO] Loading data and model...")
    if not os.path.exists(DATA_PATH) or not os.path.exists(MODEL_PATH):
        print("[ERROR] Required data or model files missing.")
        return

    df = pd.read_csv(DATA_PATH)
    pipeline = joblib.load(MODEL_PATH)

    # 2. Prepare X and y
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # Map labels to integers for metrics calculation if they are strings
    # The pipeline handles mapping internally, but for sklearn metrics we need consistent labels
    risk_map = {"Low": 0, "Medium": 1, "High": 2}
    if y.dtype == "object":
        y_numeric = y.map(risk_map)
    else:
        y_numeric = y

    # Split data (test_size=0.2, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_numeric, test_size=0.2, random_state=42, stratify=y_numeric
    )

    # 3. Generate predictions and probabilities
    print("[INFO] Generating test set predictions...")

    # The model is saved as raw XGBoost classifier (not a Pipeline), so preprocess manually
    classifier = pipeline
    import re

    X_prep = X_test.copy()

    # Drop leakage columns (same as train.py)
    leakage_cols = ["Actual_Days", "Cost_Consumed"]
    X_prep = X_prep.drop(columns=[c for c in leakage_cols if c in X_prep.columns])

    # Drop text/ID columns (same as train.py)
    text_cols = ["Summary", "Description", "Developer_Comments", "Issue_ID", "Issue_key"]
    X_prep = X_prep.drop(columns=[c for c in text_cols if c in X_prep.columns])

    # Encode categoricals with <= 15 unique values; drop the rest
    categorical_cols = X_prep.select_dtypes(include=["object", "category"]).columns
    to_encode, to_drop = [], []
    for col in categorical_cols:
        if X_prep[col].nunique() <= 15:
            to_encode.append(col)
        else:
            to_drop.append(col)
    if to_drop:
        X_prep = X_prep.drop(columns=to_drop)
    if to_encode:
        X_prep = pd.get_dummies(X_prep, columns=to_encode)

    # Sanitize feature names (same as train.py)
    X_prep.columns = [re.sub(r"[\[\]<]", "_", str(c)) for c in X_prep.columns]

    # Align columns to training feature set via feature_columns.pkl if available
    feat_col_path = os.path.join(MODEL_DIR, "feature_columns.pkl")
    if os.path.exists(feat_col_path):
        training_columns = joblib.load(feat_col_path)
        X_prep = X_prep.reindex(columns=training_columns, fill_value=0)

    X_test_transformed = X_prep.values

    y_pred = classifier.predict(X_test_transformed)
    # Ensure y_pred is numeric for the confusion matrix
    if isinstance(y_pred[0], str):
        y_pred = np.array([risk_map[val] for val in y_pred])

    y_prob = classifier.predict_proba(X_test_transformed)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 4. Figure 1: Confusion Matrix
    print("[INFO] Generating Confusion Matrix...")
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Low", "Medium", "High"],
        yticklabels=["Low", "Medium", "High"],
    )
    plt.title("Confusion Matrix: Risk Level Prediction", fontsize=14, pad=20)
    plt.xlabel("Predicted Label", fontsize=12)
    plt.ylabel("True Label", fontsize=12)
    plt.savefig(CM_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved Confusion Matrix to {CM_PATH}")

    # 5. Figure 2: ROC Curve (One-vs-Rest)
    print("[INFO] Generating ROC Curves...")
    plt.figure(figsize=(8, 6))

    # Binarize the output for multi-class ROC
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
    n_classes = 3
    labels = ["Low", "Medium", "High"]

    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_prob[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
        plt.plot(
            fpr[i],
            tpr[i],
            label=f"Class {labels[i]} (AUC = {roc_auc[i]:.2f})",
            linewidth=2,
        )

    plt.plot([0, 1], [0, 1], "k--", lw=2)  # Diagonal dashed line
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate", fontsize=12)
    plt.title("One-vs-Rest ROC Curve: Risk Level Prediction", fontsize=14, pad=20)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.savefig(ROC_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved ROC Curve to {ROC_PATH}")


if __name__ == "__main__":
    try:
        generate_publication_plots()
        print("\n[SUCCESS] All research figures have been generated successfully.")
    except Exception as e:
        print(f"\n[ERROR] Plot generation failed: {e}")
        import traceback

        traceback.print_exc()
