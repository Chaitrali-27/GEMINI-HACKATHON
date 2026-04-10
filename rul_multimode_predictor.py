"""
rul_multimode_predictor.py — Updated with Autoencoder + SHAP Root Cause Analysis

Usage:
    python rul_multimode_predictor.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# AUTOENCODER
# ─────────────────────────────────────────
try:
    import tensorflow as tf
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Dense
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️  TensorFlow not installed. Autoencoder will be skipped.")
    print("   Run: pip install tensorflow")

# ─────────────────────────────────────────
# SHAP
# ─────────────────────────────────────────
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not installed. Root Cause Analysis will be skipped.")
    print("   Run: pip install shap")

# ─────────────────────────────────────────
# SYNTHETIC DATA
# ─────────────────────────────────────────
def generate_synthetic_dataset(n=2000, seed=42):
    rng = np.random.RandomState(seed)
    vibration   = rng.normal(0.5, 0.2, size=n) + rng.rand(n) * 0.2
    temperature = rng.normal(60, 8, size=n) + (vibration - 0.5) * 15
    current     = rng.normal(10, 2, size=n) + (temperature - 60) * 0.05
    pressure    = rng.normal(1.0, 0.1, size=n) + 0.2 * (vibration - 0.5)
    base_rul    = 200 - (vibration * 60 + (temperature - 60) * 1.5) + rng.normal(0, 10, size=n)
    time_to_failure = np.clip(base_rul, 1.0, None).round(1)
    mode = []
    for i in range(n):
        if vibration[i] > 0.8:
            mode.append("bearing")
        elif temperature[i] > 70:
            mode.append("electrical")
        elif pressure[i] > 1.12:
            mode.append("gear")
        else:
            mode.append(rng.choice(["bearing","gear","electrical"], p=[0.4,0.3,0.3]))
    return pd.DataFrame({
        "vibration": vibration, "temperature": temperature,
        "current": current, "pressure": pressure,
        "failure_mode": mode, "time_to_failure": time_to_failure
    })

# ─────────────────────────────────────────
# BOOTSTRAP ENSEMBLE
# ─────────────────────────────────────────
def train_bootstrap_ensembles(X, y_mode, y_rul, n_models=30, random_state=0):
    rng = np.random.RandomState(random_state)
    clf_ensemble = []
    reg_ensemble = []
    n = X.shape[0]
    for i in range(n_models):
        idx = rng.randint(0, n, n)
        Xb, y_mode_b, y_rul_b = X[idx], y_mode[idx], y_rul[idx]
        clf = RandomForestClassifier(n_estimators=100, random_state=random_state+i, n_jobs=-1)
        clf.fit(Xb, y_mode_b)
        clf_ensemble.append(clf)
        reg = GradientBoostingRegressor(n_estimators=200, random_state=random_state+i)
        reg.fit(Xb, y_rul_b)
        reg_ensemble.append(reg)
    return clf_ensemble, reg_ensemble

# ─────────────────────────────────────────
# AUTOENCODER TRAINING
# ─────────────────────────────────────────
def train_autoencoder(X_normal, encoding_dim=4):
    """
    Train autoencoder on NORMAL (healthy) machine data only.
    It learns what normal looks like.
    Any deviation = anomaly.
    """
    if not TF_AVAILABLE:
        return None

    print("Training Autoencoder on normal data...")
    input_dim = X_normal.shape[1]

    # Build autoencoder
    inputs  = Input(shape=(input_dim,))
    encoded = Dense(16, activation="relu")(inputs)
    encoded = Dense(encoding_dim, activation="relu")(encoded)
    decoded = Dense(16, activation="relu")(encoded)
    decoded = Dense(input_dim, activation="linear")(decoded)

    autoencoder = Model(inputs, decoded)
    autoencoder.compile(optimizer="adam", loss="mse")

    # Train on normal data only
    early_stop = EarlyStopping(patience=5, restore_best_weights=True)
    autoencoder.fit(
        X_normal, X_normal,
        epochs=50, batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=0
    )

    # Calculate reconstruction error threshold
    reconstructed   = autoencoder.predict(X_normal, verbose=0)
    errors          = np.mean(np.power(X_normal - reconstructed, 2), axis=1)
    threshold       = np.percentile(errors, 95)  # 95th percentile = anomaly threshold

    print(f"✅ Autoencoder trained. Anomaly threshold: {threshold:.4f}")
    return autoencoder, threshold

# ─────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────
def detect_anomaly(autoencoder, threshold, X_new):
    """
    Returns:
        is_anomaly: True/False
        anomaly_score: 0-100 (higher = more abnormal)
        reconstruction_error: raw error value
    """
    if autoencoder is None:
        return False, 0, 0

    reconstructed = autoencoder.predict(X_new, verbose=0)
    error         = float(np.mean(np.power(X_new - reconstructed, 2)))
    is_anomaly    = error > threshold
    # normalize score to 0-100
    anomaly_score = min(100, int((error / (threshold * 2)) * 100))

    return is_anomaly, anomaly_score, error

# ─────────────────────────────────────────
# SHAP ROOT CAUSE ANALYSIS
# ─────────────────────────────────────────
def compute_root_cause(clf_ensemble, X_new, feature_cols, label_encoder):
    """
    Uses SHAP to explain WHY the model made this prediction.
    Returns top contributing features (root causes).
    """
    if not SHAP_AVAILABLE:
        return []

    try:
        # Use first model in ensemble for SHAP
        clf         = clf_ensemble[0]
        explainer   = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_new)

        # Get predicted class
        pred_class  = np.argmax(clf.predict_proba(X_new)[0])

        # SHAP values for predicted class
        if isinstance(shap_values, list):
            sv = shap_values[pred_class][0]
        else:
            sv = shap_values[0]

        # Build root cause list
        feature_impact = []
        total = np.sum(np.abs(sv)) + 1e-9
        for i, col in enumerate(feature_cols):
            contribution = abs(sv[i])
            percentage   = round((contribution / total) * 100, 1)
            direction    = "↑ High" if sv[i] > 0 else "↓ Low"
            feature_impact.append({
                "feature":      col,
                "contribution": percentage,
                "direction":    direction,
                "shap_value":   round(float(sv[i]), 4)
            })

        # Sort by contribution descending
        feature_impact.sort(key=lambda x: x["contribution"], reverse=True)
        return feature_impact[:5]  # top 5 root causes

    except Exception as e:
        print(f"SHAP error: {e}")
        return []

# ─────────────────────────────────────────
# PREDICT WITH ENSEMBLES
# ─────────────────────────────────────────
def predict_with_ensembles(clf_ensemble, reg_ensemble, X_new, label_encoder):
    probs_list = [clf.predict_proba(X_new) for clf in clf_ensemble]
    probs_arr  = np.stack(probs_list, axis=0)
    reg_preds  = np.stack([reg.predict(X_new) for reg in reg_ensemble], axis=0)

    mean_probs = probs_arr.mean(axis=0)
    std_probs  = probs_arr.std(axis=0)
    mean_rul   = reg_preds.mean(axis=0)
    lower_rul  = np.percentile(reg_preds, 2.5, axis=0)
    upper_rul  = np.percentile(reg_preds, 97.5, axis=0)
    classes    = label_encoder.inverse_transform(np.arange(len(label_encoder.classes_)))

    return {
        "mean_probs": mean_probs, "std_probs": std_probs,
        "classes": classes, "mean_rul": mean_rul,
        "lower_rul": lower_rul, "upper_rul": upper_rul
    }

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    print("=== SentinelIQ ML Engine — Autoencoder + SHAP + Ensemble ===")
    path = input("Enter CSV dataset path (or press Enter for synthetic data): ").strip()

    if path == "":
        df = generate_synthetic_dataset(n=2000)
        print("Synthetic dataset generated (n=2000).")
    else:
        if not os.path.exists(path):
            print("ERROR: file not found:", path)
            return
        df = pd.read_csv(path)
        print("Loaded dataset:", df.shape)

    required = {"failure_mode","time_to_failure"}
    if not required.issubset(set(df.columns)):
        print("ERROR: dataset must contain:", required)
        return

    non_feature_cols = ["failure_mode","time_to_failure","UDI","Product ID",
                        "Type","Failure Type","Target","RUL"]
    feature_cols = [c for c in df.columns
                    if c not in non_feature_cols and pd.api.types.is_numeric_dtype(df[c])]

    if not feature_cols:
        print("ERROR: No numeric feature columns found.")
        return

    X         = df[feature_cols].values.astype(float)
    y_mode_raw= df["failure_mode"].values.astype(str)
    y_rul     = df["time_to_failure"].values.astype(float)

    le        = LabelEncoder()
    y_mode    = le.fit_transform(y_mode_raw)
    scaler    = StandardScaler()
    X_scaled  = scaler.fit_transform(X)

    X_train, X_hold, y_mode_train, y_mode_hold, y_rul_train, y_rul_hold = train_test_split(
        X_scaled, y_mode, y_rul, test_size=0.2, random_state=42, stratify=y_mode
    )

    print(f"\nTraining on {X_train.shape[0]} samples...")
    print("Feature columns:", feature_cols)

    # ── Train Random Forest + Gradient Boosting ensemble ──
    clf_ens, reg_ens = train_bootstrap_ensembles(
        X_train, y_mode_train, y_rul_train, n_models=30, random_state=1
    )
    print("✅ Ensemble trained (30 models each)")

    # ── Train Autoencoder on NORMAL data only ──
    autoencoder_bundle = None
    if TF_AVAILABLE:
        # normal = no failure (label 0 or majority class)
        normal_mask    = y_rul_train > np.percentile(y_rul_train, 50)
        X_normal       = X_train[normal_mask]
        ae_result      = train_autoencoder(X_normal)
        if ae_result:
            autoencoder, ae_threshold = ae_result
            autoencoder_bundle = {"model": autoencoder, "threshold": ae_threshold}

    # ── Save everything ──
    bundle = {
        "clf_ens": clf_ens, "reg_ens": reg_ens,
        "scaler": scaler, "label_encoder": le,
        "feature_cols": feature_cols,
        "autoencoder_bundle": autoencoder_bundle
    }
    joblib.dump(bundle, "rul_multimode_ensemble.joblib")
    print("✅ All models saved to rul_multimode_ensemble.joblib")

    # ── Show sample predictions ──
    preds = predict_with_ensembles(clf_ens, reg_ens, X_hold, le)
    print("\n--- Sample Predictions ---")
    for i in range(min(3, X_hold.shape[0])):
        true_mode = le.inverse_transform([y_mode_hold[i]])[0]
        print(f"\nSample {i+1}: True={true_mode}, True RUL={y_rul_hold[i]:.1f}")

        # anomaly
        if autoencoder_bundle:
            is_anom, score, _ = detect_anomaly(
                autoencoder_bundle["model"],
                autoencoder_bundle["threshold"],
                X_hold[i:i+1]
            )
            print(f"  Anomaly: {'⚠️ YES' if is_anom else '✅ No'} (score={score})")

        # failure probs
        for idx, cls in enumerate(preds["classes"]):
            print(f"  {cls}: {preds['mean_probs'][i,idx]:.3f}")
        print(f"  RUL: {preds['mean_rul'][i]:.1f} hrs [{preds['lower_rul'][i]:.1f}–{preds['upper_rul'][i]:.1f}]")

        # root cause
        rca = compute_root_cause(clf_ens, X_hold[i:i+1], feature_cols, le)
        if rca:
            print("  Root Causes:")
            for r in rca[:3]:
                print(f"    {r['feature']}: {r['contribution']}% ({r['direction']})")

if __name__ == "__main__":
    main()
