import streamlit as st
import joblib
import numpy as np
import os

# ─────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────
MODEL_PATH = "federated_results.joblib"

model = None

if os.path.exists(MODEL_PATH):
    bundle = joblib.load(MODEL_PATH)
    
    st.write("DEBUG - Model content:", bundle)  # show structure
    
    # Try common formats
    if isinstance(bundle, dict):
        model = bundle.get("model", None)
    else:
        model = bundle
else:
    st.error("❌ Model not found")

# ─────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────
st.title("🔧 SmartPredict ML System")

# Simple input (since we don’t know features yet)
input_val = st.number_input("Enter input value")

if st.button("Predict"):
    if model is not None:
        try:
            result = model.predict([[input_val]])
            st.success(f"Prediction: {result}")
        except Exception as e:
            st.error(f"Prediction error: {e}")
    else:
        st.warning("Model not loaded properly")
