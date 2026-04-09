  import os
import uuid
import time
import json
import threading
import logging
from pathlib import Path
from typing import Dict, Optional
from flask import Flask, render_template_string
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
class AletheiaHub:
    def __init__(self):
        self.config = {
            "HUB_QVAPAY_UUID": os.environ.get('HUB_QVAPAY_UUID'),
            "HUB_QVAPAY_SECRET": os.environ.get('HUB_QVAPAY_SECRET'),
            "HUB_TROPIPAY_CLIENT_ID": os.environ.get('HUB_TROPIPAY_CLIENT_ID'),
            "HUB_TROPIPAY_CLIENT_SECRET": os.environ.get('HUB_TROPIPAY_CLIENT_SECRET'),
            "HUB_BASE_URL": os.environ.get('HUB_BASE_URL')
        }

    def get(self, key):
        return self.config.get(key)

hub = AletheiaHub()
PORTADA = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>ALETHEIA HUB</title>
</head>
<body style="background:#000;color:#D4AF37;text-align:center;padding:100px;font-family:serif;">
    <h1>ALETHEIA HUB</h1>

    <div style="display:flex;flex-direction:column;align-items:center;gap:20px;">

        <a href="/create_payment/qvapay"
           style="background:#4CAF50;color:#fff;padding:20px;width:300px;border-radius:50px;text-decoration:none;">
           PAGAR CON QVAPAY
        </a>

        <a href="/create_payment/tropipay"
           style="background:#2196F3;color:#fff;padding:20px;width:300px;border-radius:50px;text-decoration:none;">
           PAGAR CON TROPIPAY
        </a>

    </div>
</body>
</html>
"""
@app.route('/')
def home():
    return render_template_string(PORTADA)
    class PaymentStatus:
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    class PaymentProvider:
    def create_payment(self, amount, currency, description, metadata):
        raise NotImplementedError()

    def verify_payment(self, payload):
        raise NotImplementedError()
        class QvaPayProvider(PaymentProvider):
    def __init__(self, hub):
        self.hub = hub
        self.api_url = "https://qvapay.com/api/v1/create_invoice"

    def create_payment(self, amount, currency, description, metadata):
        try:
            payload = {
                "app_id": self.hub.get("HUB_QVAPAY_UUID"),
                "app_secret": self.hub.get("HUB_QVAPAY_SECRET"),
                "amount": amount,
                "currency": currency,
                "description": description
            }

            r = requests.post(self.api_url, data=payload, timeout=10)
            data = r.json()

            return {
                "provider": "qvapay",
                "payment_url": data.get("url"),
                "status": PaymentStatus.PENDING
            }

        except Exception as e:
            logging.error(str(e))
            return {"provider": "qvapay", "payment_url": "", "status": PaymentStatus.FAILED}
            class TropiPayProvider(PaymentProvider):
    def __init__(self, hub):
        self.hub = hub
        self.base_url = "https://www.tropipay.com/api/v2"
        self.token = None

    def _auth(self):
        if self.token:
            return self.token

        r = requests.post(f"{self.base_url}/auth/token", data={
            "client_id": self.hub.get("HUB_TROPIPAY_CLIENT_ID"),
            "client_secret": self.hub.get("HUB_TROPIPAY_CLIENT_SECRET"),
            "grant_type": "client_credentials"
        })

        self.token = r.json().get("access_token")
        return self.token

    def create_payment(self, amount, currency, description, metadata):
        try:
            token = self._auth()

            r = requests.post(
                f"{self.base_url}/payment",
                json={
                    "amount": amount,
                    "currency": currency,
                    "concept": description
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            data = r.json()

            return {
                "provider": "tropipay",
                "payment_url": data.get("url"),
                "status": PaymentStatus.PENDING
            }

        except Exception as e:
            logging.error(str(e))
            return {"provider": "tropipay", "payment_url": "", "status": PaymentStatus.FAILED}
            payment_hub = {
    "qvapay": QvaPayProvider(hub),
    "tropipay": TropiPayProvider(hub)
}


@app.route('/create_payment/<provider>')
def create_payment(provider):
    try:
        result = payment_hub[provider].create_payment(
            10, "USD", "Aletheia Access", {}
        )

        if result["payment_url"]:
            return f'<script>window.location="{result["payment_url"]}"</script>'

        return "Error creando pago", 500

    except Exception as e:
        logging.error(str(e))
        return "Error interno", 500


@app.route('/success')
def success():
    return "PAGO COMPLETADO ✅"


@app.route('/cancel')
def cancel():
    return "PAGO CANCELADO ❌"
    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Servidor iniciado en {port}")
    app.run(host="0.0.0.0", port=port)
