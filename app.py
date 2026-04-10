"""
app.py — SentinelIQ Flask API
Updated with Autoencoder + SHAP Root Cause Analysis

Run:
    python app.py
"""

#from flask import Flask, request, jsonify
import joblib
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ─────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────
MODEL_PATH = "rul_multimode_ensemble.joblib"

clf_ens = reg_ens = scaler = label_encoder = feature_cols = None
autoencoder_bundle = None

if os.path.exists(MODEL_PATH):
    bundle             = joblib.load(MODEL_PATH)
    clf_ens            = bundle["clf_ens"]
    reg_ens            = bundle["reg_ens"]
    scaler             = bundle["scaler"]
    label_encoder      = bundle["label_encoder"]
    feature_cols       = bundle["feature_cols"]
    autoencoder_bundle = bundle.get("autoencoder_bundle", None)
    print("✅ Model loaded successfully!")
    print("   Features:", feature_cols)
    print("   Autoencoder:", "✅ Loaded" if autoencoder_bundle else "❌ Not found")
else:
    print("❌ Model not found. Run rul_multimode_predictor.py first.")

# ─────────────────────────────────────────
# SHAP
# ─────────────────────────────────────────
try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False

# ─────────────────────────────────────────
# PRESCRIPTIVE ENGINE
# ─────────────────────────────────────────
def get_prescription(rul, failure_mode, probability):
    action_map = {
        "bearing":       "Inspect and replace bearing unit",
        "electrical":    "Check electrical connections and motor windings",
        "gear":          "Lubricate and inspect gear assembly",
        "overstrain":    "Reduce machine load immediately",
        "heat":          "Check cooling system and ventilation",
        "power failure": "Check power supply and electrical panel",
        "no failure":    "No action required",
        "No Failure":    "No action required"
    }
    if rul < 24:
        priority = "CRITICAL"; color = "red"
    elif rul < 72:
        priority = "WARNING";  color = "orange"
    else:
        priority = "HEALTHY";  color = "green"

    health_score = min(100, max(0, int((rul / 200) * 100)))
    action       = action_map.get(failure_mode.lower(),
                   action_map.get(failure_mode, "Inspect machine immediately"))

    return {
        "priority":           priority,
        "priority_color":     color,
        "health_score":       health_score,
        "recommended_action": action,
        "alert_message":      f"Machine will fail in {rul:.1f} hrs due to {failure_mode} ({probability*100:.1f}%). Action: {action}"
    }

# ─────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────
def detect_anomaly(X_new):
    if not autoencoder_bundle:
        return {"available": False, "is_anomaly": False, "anomaly_score": 0}
    try:
        model     = autoencoder_bundle["model"]
        threshold = autoencoder_bundle["threshold"]
        recon     = model.predict(X_new, verbose=0)
        error     = float(np.mean(np.power(X_new - recon, 2)))
        is_anom   = bool(error > threshold)
        score     = min(100, int((error / (threshold * 2)) * 100))
        return {
            "available":            True,
            "is_anomaly":           is_anom,
            "anomaly_score":        score,
            "reconstruction_error": round(error, 6),
            "threshold":            round(float(threshold), 6),
            "message":              "⚠️ Abnormal machine behavior detected!" if is_anom else "✅ Machine behavior is normal"
        }
    except Exception as e:
        return {"available": False, "is_anomaly": False, "error": str(e)}

# ─────────────────────────────────────────
# ROOT CAUSE ANALYSIS
# ─────────────────────────────────────────
def compute_rca(X_new):
    if not SHAP_AVAILABLE or clf_ens is None:
        return {"available": False, "root_causes": []}
    try:
        clf         = clf_ens[0]
        explainer   = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_new)
        pred_class  = int(np.argmax(clf.predict_proba(X_new)[0]))

        if isinstance(shap_values, list):
            sv = shap_values[pred_class][0]
        else:
            sv = shap_values[0]

        total  = np.sum(np.abs(sv)) + 1e-9
        causes = []
        for i, col in enumerate(feature_cols):
            pct = round((abs(sv[i]) / total) * 100, 1)
            causes.append({
                "feature":      col,
                "contribution": pct,
                "direction":    "↑ Higher than normal" if sv[i] > 0 else "↓ Lower than normal",
                "shap_value":   round(float(sv[i]), 4)
            })

        causes.sort(key=lambda x: x["contribution"], reverse=True)

        # Human readable summary
        top = causes[0] if causes else None
        summary = f"Primary cause: {top['feature']} ({top['contribution']}% impact, {top['direction']})" if top else "Analysis unavailable"

        return {
            "available":   True,
            "root_causes": causes[:5],
            "summary":     summary
        }
    except Exception as e:
        return {"available": False, "root_causes": [], "error": str(e)}

# ─────────────────────────────────────────
# CORE PREDICTION
# ─────────────────────────────────────────
def run_prediction(sensor_values):
    X_new = scaler.transform([sensor_values])

    # ── Failure classification ──
    probs_list = [clf.predict_proba(X_new) for clf in clf_ens]
    probs_arr  = np.stack(probs_list, axis=0)
    mean_probs = probs_arr.mean(axis=0)[0]
    std_probs  = probs_arr.std(axis=0)[0]

    # ── RUL regression ──
    reg_preds = np.stack([reg.predict(X_new) for reg in reg_ens], axis=0)
    mean_rul  = float(reg_preds.mean())
    lower_rul = float(np.percentile(reg_preds, 2.5))
    upper_rul = float(np.percentile(reg_preds, 97.5))

    # ── Top failure mode ──
    top_idx  = int(np.argmax(mean_probs))
    classes  = label_encoder.inverse_transform(np.arange(len(label_encoder.classes_)))
    top_mode = str(classes[top_idx])
    top_prob = float(mean_probs[top_idx])

    failure_breakdown = sorted([
        {"failure_mode": str(cls), "probability": round(float(mean_probs[i]),4),
         "uncertainty": round(float(std_probs[i]),4)}
        for i, cls in enumerate(classes)
    ], key=lambda x: x["probability"], reverse=True)

    # ── Prescriptive ──
    prescription = get_prescription(mean_rul, top_mode, top_prob)

    # ── Autoencoder anomaly detection ──
    anomaly = detect_anomaly(X_new)

    # ── SHAP Root Cause Analysis ──
    rca = compute_rca(X_new)

    return {
        "rul": {
            "mean":  round(mean_rul, 2),
            "lower": round(lower_rul, 2),
            "upper": round(upper_rul, 2)
        },
        "top_failure_mode":  top_mode,
        "top_probability":   round(top_prob, 4),
        "failure_breakdown": failure_breakdown,
        "prescription":      prescription,
        "anomaly_detection": anomaly,
        "root_cause_analysis": rca
    }

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "SentinelIQ API — Predict. Prevent. Protect.",
        "endpoints": {
            "POST /predict":       "Predict failure + RUL + anomaly + root cause",
            "POST /predict/batch": "Predict for multiple machines",
            "GET  /features":      "Get expected input features",
            "GET  /health":        "API health check"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":       "ok",
        "model_loaded": clf_ens is not None,
        "autoencoder":  autoencoder_bundle is not None,
        "shap":         SHAP_AVAILABLE
    })

@app.route("/features", methods=["GET"])
def features():
    if feature_cols is None:
        return jsonify({"error": "Model not loaded"}), 500
    return jsonify({"features": feature_cols, "count": len(feature_cols)})

@app.route("/predict", methods=["POST"])
def predict():
    if clf_ens is None:
        return jsonify({"error": "Model not loaded"}), 500
    data        = request.get_json()
    machine_id  = data.get("machine_id", "Unknown")
    sensor_data = data.get("sensor_data", {})
    missing     = [c for c in feature_cols if c not in sensor_data]
    if missing:
        return jsonify({"error": "Missing features", "missing": missing}), 400
    sensor_values = [float(sensor_data[c]) for c in feature_cols]
    result        = run_prediction(sensor_values)
    result["machine_id"] = machine_id
    return jsonify(result)

@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    if clf_ens is None:
        return jsonify({"error": "Model not loaded"}), 500
    data    = request.get_json()
    results = []
    for machine in data.get("machines", []):
        mid         = machine.get("machine_id","Unknown")
        sensor_data = machine.get("sensor_data",{})
        missing     = [c for c in feature_cols if c not in sensor_data]
        if missing:
            results.append({"machine_id": mid, "error": f"Missing: {missing}"})
            continue
        sensor_values = [float(sensor_data[c]) for c in feature_cols]
        result        = run_prediction(sensor_values)
        result["machine_id"] = mid
        results.append(result)
    return jsonify({"results": results, "count": len(results)})

# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
#if __name__ == "__main__":
   # app.run(debug=True, host="0.0.0.0", port=5000)
