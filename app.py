import streamlit as st
import joblib
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────
MODEL_PATH = "federated_results.joblib"
clf_ens = reg_ens = scaler = label_encoder = feature_cols = None

if os.path.exists(MODEL_PATH):
    bundle        = joblib.load(MODEL_PATH)
    clf_ens       = bundle["clf_ens"]
    reg_ens       = bundle["reg_ens"]
    scaler        = bundle["scaler"]
    label_encoder = bundle["label_encoder"]
    feature_cols  = bundle["feature_cols"]
else:
    st.error("❌ Model not found")

# ─────────────────────────────────────────
# PREDICTION FUNCTION
# ─────────────────────────────────────────
def run_prediction(sensor_values):
    X_new = scaler.transform([sensor_values])

    probs_list = [clf.predict_proba(X_new) for clf in clf_ens]
    probs_arr  = np.stack(probs_list, axis=0)
    mean_probs = probs_arr.mean(axis=0)[0]

    reg_preds = np.stack([reg.predict(X_new) for reg in reg_ens], axis=0)
    mean_rul  = float(reg_preds.mean())

    top_idx  = int(np.argmax(mean_probs))
    classes  = label_encoder.inverse_transform(np.arange(len(label_encoder.classes_)))
    top_mode = str(classes[top_idx])
    top_prob = float(mean_probs[top_idx])

    return mean_rul, top_mode, top_prob

# ─────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────
st.title("🔧 SmartPredict ML System")

if feature_cols:
    st.write("Enter sensor values:")

    inputs = []
    for col in feature_cols:
        val = st.number_input(f"{col}", value=0.0)
        inputs.append(val)

    if st.button("Predict"):
        rul, mode, prob = run_prediction(inputs)

        st.success(f"RUL: {round(rul,2)} hours")
        st.write(f"Failure Mode: {mode}")
        st.write(f"Probability: {round(prob*100,2)}%")

else:
    st.warning("Model not loaded properly")
