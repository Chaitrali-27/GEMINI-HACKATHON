"""
streamer.py — Live Data Streamer
Step 3 of the project

Simulates 3 factories sending live sensor data to Flask API every 3 seconds.

Run:
    python streamer.py

Make sure Flask API (app.py) is running first!
"""

import requests
import time
import random
import json
from datetime import datetime

# -------------------------
# Flask API URL
# -------------------------
API_URL = "http://127.0.0.1:5000/predict"

# -------------------------
# 3 Simulated Factories
# Each factory has slightly different sensor ranges
# to simulate different machines
# -------------------------
FACTORIES = {
    "Factory_1_Machine_A": {
        "Air temperature [K]":        (295, 305),   # normal range
        "Process temperature [K]":    (305, 315),
        "Rotational speed [rpm]":     (1400, 1600),
        "Torque [Nm]":                (35, 55),
        "Tool wear [min]":            (0, 100),
        "Vibration Sensor [g]":       (0.2, 0.6),
        "Acoustic Emission [dB]":     (60, 75),
        "Current Draw [A]":           (8, 12),
    },
    "Factory_2_Machine_B": {
        "Air temperature [K]":        (298, 310),   # slightly hotter
        "Process temperature [K]":    (310, 325),
        "Rotational speed [rpm]":     (1500, 1800),
        "Torque [Nm]":                (40, 65),
        "Tool wear [min]":            (50, 180),    # more worn
        "Vibration Sensor [g]":       (0.5, 0.9),   # more vibration
        "Acoustic Emission [dB]":     (70, 85),
        "Current Draw [A]":           (10, 15),
    },
    "Factory_3_Machine_C": {
        "Air temperature [K]":        (300, 315),   # hottest factory
        "Process temperature [K]":    (315, 330),
        "Rotational speed [rpm]":     (1200, 1500),
        "Torque [Nm]":                (50, 80),     # high torque = more stress
        "Tool wear [min]":            (100, 250),   # heavily worn
        "Vibration Sensor [g]":       (0.7, 1.2),   # high vibration = danger
        "Acoustic Emission [dB]":     (75, 95),
        "Current Draw [A]":           (12, 18),
    }
}


# -------------------------
# Helper: generate one sensor reading
# -------------------------
def generate_sensor_reading(factory_name, tick):
    """
    Generate a realistic sensor reading for a factory.
    As tick increases, machine gradually degrades (gets worse).
    """
    ranges = FACTORIES[factory_name]
    sensor_data = {}

    # degradation factor — machine gets worse over time
    degradation = min(1.0, tick / 200)  # 0 to 1 over 200 ticks

    for feature, (low, high) in ranges.items():
        base_value = random.uniform(low, high)

        # add gradual degradation to make it realistic
        if feature in ["Tool wear [min]", "Vibration Sensor [g]", "Acoustic Emission [dB]"]:
            # these increase as machine degrades
            base_value += degradation * (high - low) * 0.5

        elif feature in ["Rotational speed [rpm]"]:
            # speed drops as machine degrades
            base_value -= degradation * (high - low) * 0.3

        sensor_data[feature] = round(base_value, 3)

    return sensor_data


# -------------------------
# Helper: print colored status
# -------------------------
def print_status(machine_id, result, tick):
    priority = result.get("prescription", {}).get("priority", "UNKNOWN")
    rul       = result.get("rul", {}).get("mean", 0)
    health    = result.get("prescription", {}).get("health_score", 0)
    top_mode  = result.get("top_failure_mode", "unknown")
    top_prob  = result.get("top_probability", 0)
    action    = result.get("prescription", {}).get("recommended_action", "")

    # color symbols
    symbol = {"CRITICAL": "🔴", "WARNING": "🟡", "HEALTHY": "🟢"}.get(priority, "⚪")

    print(f"\n{symbol} [{datetime.now().strftime('%H:%M:%S')}] Tick {tick} — {machine_id}")
    print(f"   Priority     : {priority}")
    print(f"   Health Score : {health}/100")
    print(f"   RUL          : {rul:.1f} hrs  (95% CI: {result['rul']['lower']:.1f} – {result['rul']['upper']:.1f})")
    print(f"   Top Failure  : {top_mode} ({top_prob*100:.1f}%)")
    print(f"   Action       : {action}")

    if priority == "CRITICAL":
        print(f"   ⚠️  ALERT: {result['prescription']['alert_message']}")


# -------------------------
# Main streaming loop
# -------------------------
def stream():
    print("=" * 60)
    print("🚀 Predictive Maintenance — Live Data Streamer")
    print("=" * 60)
    print("Simulating 3 factories sending data every 3 seconds...")
    print("Press CTRL+C to stop\n")

    # check if API is running
    try:
        r = requests.get("http://127.0.0.1:5000/health")
        if r.json().get("model_loaded"):
            print("✅ Flask API is running and model is loaded!\n")
        else:
            print("❌ Model not loaded in Flask. Check app.py")
            return
    except:
        print("❌ Flask API not running! Start app.py first.")
        return

    tick = 0

    while True:
        tick += 1
        print(f"\n{'='*60}")
        print(f"📡 Sending data batch — Tick {tick}")
        print(f"{'='*60}")

        # send data for all 3 factories
        machines_data = []
        for machine_id in FACTORIES.keys():
            sensor_data = generate_sensor_reading(machine_id, tick)
            machines_data.append({
                "machine_id": machine_id,
                "sensor_data": sensor_data
            })

        # send batch request to Flask API
        try:
            response = requests.post(
                "http://127.0.0.1:5000/predict/batch",
                json={"machines": machines_data},
                timeout=10
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                for result in results:
                    print_status(result["machine_id"], result, tick)
            else:
                print(f"❌ API error: {response.status_code} — {response.text}")

        except requests.exceptions.ConnectionError:
            print("❌ Lost connection to Flask API. Is app.py still running?")
        except Exception as e:
            print(f"❌ Error: {e}")

        # wait 3 seconds before next reading
        print(f"\n⏳ Next reading in 3 seconds...")
        time.sleep(3)


# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    stream()
