"""
Rule-based crop advisor.
No AI/ML — pure threshold logic based on
Reoti Block's climate and common crops.
"""


def get_crop_advice(reading: dict) -> list[str]:
    advice = []

    temp      = reading.get("temperature")
    humidity  = reading.get("humidity")
    soil_mois = reading.get("soil_moisture")
    rainfall  = reading.get("rainfall", 0)
    uv_index  = reading.get("uv_index", 0)

    if temp is None:
        return ["Sensor data unavailable. Please check IoT node."]

    # Temperature alerts
    if temp > 40:
        advice.append("🌡️ Bahut zyada garmi hai — fasal ko shade net se dhakein.")
    elif temp > 35:
        advice.append("☀️ Garmi zyada hai — subah ya shaam ko sinchai karein.")
    elif temp < 10:
        advice.append("❄️ Thandi raat — gehun aur sarson ko frost se bachayein.")

    # Soil moisture
    if soil_mois is not None:
        if soil_mois < 20:
            advice.append("💧 Mitti bahut sukhi hai — aaj sinchai zaroori hai.")
        elif soil_mois < 35:
            advice.append("🌱 Mitti thodi sukhi hai — kal tak sinchai kar lein.")
        elif soil_mois > 80:
            advice.append("🚫 Mitti mein zyada paani hai — sinchai band karein, naali banayein.")

    # Humidity
    if humidity is not None:
        if humidity > 85:
            advice.append("🍄 Zyada namak — fungal bimari ka khatra, fungicide spray karein.")
        elif humidity < 30:
            advice.append("🏜️ Hawa bahut sukhi hai — drip sinchai karein.")

    # Rainfall
    if rainfall and rainfall > 50:
        advice.append("🌧️ Bhari barish — khet ka paani nikalen, fasal sadne se bachayein.")
    elif rainfall and rainfall > 20:
        advice.append("🌦️ Acchi barish — aaj sinchai ki zaroorat nahi.")

    # UV Index
    if uv_index and uv_index > 8:
        advice.append("☀️ UV zyada hai — dhup mein kaam karte waqt savdhan rahein.")

    if not advice:
        advice.append("✅ Mausam theek hai — normal khet ka kaam karein.")

    return advice