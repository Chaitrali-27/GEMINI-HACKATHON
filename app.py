from flask import Flask, request, jsonify
import joblib
import os

app = Flask(__name__)

# ─────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────
MODEL_PATH = "federated_results.joblib"

model_data = None

if os.path.exists(MODEL_PATH):
    model_data = joblib.load(MODEL_PATH)
else:
    print("Model not found")

# ─────────────────────────────────────────
# HOME ROUTE
# ─────────────────────────────────────────
@app.route("/")
def home():
    return "✅ SmartPredict Flask App is Running!"

# ─────────────────────────────────────────
# VIEW MODEL DATA
# ─────────────────────────────────────────
@app.route("/data")
def data():
    if model_data is None:
        return jsonify({"error": "Model not loaded"})
    return jsonify(model_data)

# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run()
