from flask import Flask, request, jsonify
import hashlib
import base64
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
import requests

app = Flask(__name__)

# ================= CONFIGURACIÓN =================
CRYPTOMUS_API_KEY = "TU_API_KEY"
SUPABASE_URL = "TU_URL_SUPABASE"
SUPABASE_KEY = "TU_KEY_SUPABASE_SERVICE_ROLE" 
TELEGRAM_TOKEN = "8904518898:AAH3G0io7Y5CVQUxCTQQRH9m2Mr3DsDMoDY"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/webhook/cryptomus', methods=['POST'])
def cryptomus_webhook():
    try:
        raw_body = request.get_data()
        sign_recibido = request.headers.get("sign")

        if not sign_recibido:
            return jsonify({"error": "Falta la firma"}), 400

        payload_b64 = base64.b64encode(raw_body).decode('utf-8')
        sign_calculado = hashlib.md5((payload_b64 + CRYPTOMUS_API_KEY).encode('utf-8')).hexdigest()

        if sign_recibido != sign_calculado:
            return jsonify({"error": "Firma inválida"}), 401

        data = request.json
        status = data.get("status")
        chat_id = data.get("order_id") 

        if status in ["paid", "paid_over"]:
            vencimiento = (datetime.utcnow() + timedelta(days=30)).isoformat()

            supabase.table("usuarios_bot").update({
                "es_vip": True,
                "fecha_vencimiento_vip": vencimiento
            }).eq("chat_id", int(chat_id)).execute()

            mensaje = "🎉 ¡PAGO CONFIRMADO! Tu membresía VIP ha sido activada exitosamente por 30 días. ¡A reventar las casas de apuestas! 🔥"
            url_telegram = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url_telegram, json={"chat_id": chat_id, "text": mensaje})

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Error procesando el webhook: {e}")
        return jsonify({"error": "Error interno"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
