# -------------------------------
# main.py - ALETHEIA HUB STRATEGIC (Bloque 1/10)
# -------------------------------
import os
import uuid
import time
import json
import threading
import logging
from pathlib import Path
from typing import Dict, Optional
from flask import Flask, render_template_string, request
import requests

# Configuración logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Inicializar Flask
app = Flask(__name__)

# -------------------------------
# Configuración y Secrets
# -------------------------------
class AletheiaHub:
    def __init__(self):
        self.config = {
            "GROQ": os.environ.get('GROQ_API_KEY'),
            "GOOGLE": os.environ.get('GOOGLE_API_KEY'),
            "SERPER": os.environ.get('SERPER_API_KEY'),
            "TAVILY": os.environ.get('TAVILY_API_KEY'),
            "AGENTMAIL": os.environ.get('AGENTMAIL_API_KEY'),
            "HUB_QVAPAY_UUID": os.environ.get('HUB_QVAPAY_UUID'),
            "HUB_QVAPAY_SECRET": os.environ.get('HUB_QVAPAY_SECRET'),
            "HUB_TROPIPAY_CLIENT_ID": os.environ.get('HUB_TROPIPAY_CLIENT_ID'),
            "HUB_TROPIPAY_CLIENT_SECRET": os.environ.get('HUB_TROPIPAY_CLIENT_SECRET'),
            "HUB_BASE_URL": os.environ.get('HUB_BASE_URL')
        } 
        self.validate_config()

    def validate_config(self):
        missing = [key for key, value in self.config.items() if not value]
        if missing:
            logging.error(f"⚠️ Variables de entorno críticas faltantes: {missing}")
            raise RuntimeError(f"Faltan variables críticas: {missing}")
        else:
            logging.info("✅ Todas las variables de entorno cargadas correctamente")

    def get(self, key):
        return self.config.get(key)

hub = AletheiaHub()
# -------------------------------
# Frontend y Portada
# -------------------------------
PORTADA = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>ALETHEIA HUB STRATEGIC</title>
</head>
<body style="background:#000;color:#D4AF37;text-align:center;padding:100px;font-family:serif;">
    <h1 style="font-size:3.5rem;">ALETHEIA HUB STRATEGIC</h1>
    <p style="color:#fff;letter-spacing:2px;font-family:sans-serif;">INGRESOS AUTÓNOMOS 24/7</p>
    <br>
    <div style="display:flex; flex-direction:column; align-items:center; gap:20px;">
        <a href="#" id="paypal" style="background:#ffc439;color:#003087;padding:20px;width:300px;border-radius:50px;text-decoration:none;font-weight:bold;border:2px solid #D4AF37;">PAGAR CON PAYPAL</a>
        <a href="#" id="qvapay" style="background:#4CAF50;color:#fff;padding:20px;width:300px;border-radius:50px;text-decoration:none;font-weight:bold;border:2px solid #D4AF37;">PAGAR CON QVAPAY (USDT)</a>
        <a href="#" id="tropipay" style="background:#2196F3;color:#fff;padding:20px;width:300px;border-radius:50px;text-decoration:none;font-weight:bold;border:2px solid #D4AF37;">PAGAR CON TROPIPAY (Tarjeta)</a>
    </div>
    <p style="margin-top:50px; color:#444;">CEO JERY - SISTEMA ACTIVO</p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(PORTADA)
    # -------------------------------
# Estados de Pago
# -------------------------------
class PaymentStatus:
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# -------------------------------
# Clase base de Proveedor de Pago
# -------------------------------
class PaymentProvider:
    def create_payment(self, amount: float, currency: str, description: str, metadata: Dict) -> Dict:
        raise NotImplementedError()
    def verify_payment(self, payload: Dict) -> Dict:
        raise NotImplementedError()
        # -------------------------------
# QvaPay Provider
# -------------------------------
class QvaPayProvider(PaymentProvider):
    def __init__(self, hub_obj: AletheiaHub):
        self.hub = hub_obj
        self.app_id = self.hub.get("HUB_QVAPAY_UUID")
        self.app_secret = self.hub.get("HUB_QVAPAY_SECRET")
        self.api_url = "https://qvapay.com/api/v1/create_invoice"

    def create_payment(self, amount, currency, description, metadata):
        remote_id = f"qva_{uuid.uuid4().hex}"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "amount": amount,
            "currency": currency,
            "description": description,
            "custom": remote_id,
            "callback_url": metadata.get("callback_url"),
            "success_url": metadata.get("success_url"),
            "cancel_url": metadata.get("cancel_url"),
        }
        try:
            r = requests.post(self.api_url, data=payload, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {"provider": "qvapay", "remote_id": remote_id, "payment_url": data.get("url", ""), "status": PaymentStatus.PENDING}
        except Exception as e:
            logging.error(f"QvaPay error: {str(e)}")
            return {"provider": "qvapay", "remote_id": remote_id, "payment_url": "", "status": PaymentStatus.FAILED}

    def verify_payment(self, payload):
        remote_id = payload.get("custom")
        status = PaymentStatus.COMPLETED if payload.get("status","").lower()=="paid" else PaymentStatus.FAILED
        return {"provider":"qvapay","remote_id":remote_id,"status":status}
        # -------------------------------
# TropiPay Provider
# -------------------------------
class TropiPayProvider(PaymentProvider):
    def __init__(self, hub_obj: AletheiaHub):
        self.hub = hub_obj
        self.client_id = self.hub.get("HUB_TROPIPAY_CLIENT_ID")
        self.client_secret = self.hub.get("HUB_TROPIPAY_CLIENT_SECRET")
        self.base_url = "https://www.tropipay.com/api/v2"
        self._token: Optional[str] = None

    def _get_token(self):
        if self._token: return self._token
        try:
            r = requests.post(f"{self.base_url}/auth/token", data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type":"client_credentials"
            }, timeout=10)
            r.raise_for_status()
            self._token = r.json().get("access_token")
            if not self._token: raise RuntimeError("No se pudo obtener token TropiPay")
            return self._token
        except Exception as e:
            logging.error(f"TropiPay auth error: {str(e)}")
            return None

    def create_payment(self, amount, currency, description, metadata):
        token = self._get_token()
        if not token:
            return {"provider":"tropipay","remote_id":None,"payment_url":"","status":PaymentStatus.FAILED}
        remote_id = f"tp_{uuid.uuid4().hex}"
        try:
            r = requests.post(f"{self.base_url}/payment",
                              json={"amount": amount,
                                    "currency": currency,
                                    "concept": description,
                                    "reference": remote_id,
                                    "urlSuccess": metadata.get("success_url"),
                                    "urlFailed": metadata.get("cancel_url"),
                                    "urlNotification": metadata.get("callback_url")},
                              headers={"Authorization": f"Bearer {token}"}, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {"provider":"tropipay","remote_id":remote_id,"payment_url":data.get("url",""),"status":PaymentStatus.PENDING}
        except Exception as e:
            logging.error(f"TropiPay payment error: {str(e)}")
            return {"provider":"tropipay","remote_id":remote_id,"payment_url":"","status":PaymentStatus.FAILED}

    def verify_payment(self, payload):
        remote_id = payload.get("reference")
        status = PaymentStatus.COMPLETED if payload.get("status","").lower()=="success" else PaymentStatus.FAILED
        return {"provider":"tropipay","remote_id":remote_id,"status":status}
        # -------------------------------
# PaymentHub Central
# -------------------------------
class PaymentHub:
    def __init__(self, storage_path="app/data/payments.json"):
        self.hub = hub
        self.storage_path = Path(storage_path)
        self.payments = self._load_payments()
        self.providers = {"qvapay": QvaPayProvider(self.hub), "tropipay": TropiPayProvider(self.hub)}

    def _load_payments(self):
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text())
            except Exception:
                return {}
        return {}

    def _save_payments(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.payments, indent=2))

    def _log_attempt(self, payment_id, provider, status, error=None):
        entry = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "provider": provider,
                 "status": status,
                 "error": error}
        self.payments[payment_id].setdefault("attempts", []).append(entry)
        # -------------------------------
# Crear y manejar pagos
# -------------------------------
    def create_payment(self, amount, currency, description, metadata, preferred_provider="qvapay"):
        payment_id = f"pay_{uuid.uuid4().hex}"
        self.payments[payment_id] = {"payment_id": payment_id,
                                     "amount": amount,
                                     "currency": currency,
                                     "description": description,
                                     "status": PaymentStatus.PENDING,
                                     "provider": None,
                                     "remote_id": None,
                                     "payment_url": None,
                                     "metadata": metadata,
                                     "attempts":[]}
        providers_order = [preferred_provider]+[p for p in self.providers if p!=preferred_provider]
        for attempt in range(3):
            for prov_name in providers_order:
                try:
                    result = self.providers[prov_name].create_payment(amount,currency,description,metadata)
                    self.payments[payment_id].update({"provider":result["provider"],
                                                      "remote_id":result["remote_id"],
                                                      "payment_url":result["payment_url"],
                                                      "status":result["status"]})
                    self._log_attempt(payment_id, prov_name, result["status"])
                    self._save_payments()
                    if result["status"] != PaymentStatus.FAILED:
                        return {"payment_id": payment_id, **result}
                except Exception as e:
                    self._log_attempt(payment_id, prov_name, PaymentStatus.FAILED, str(e))
            time.sleep(2**attempt)
        self.payments[payment_id]["status"]=PaymentStatus.FAILED
        self._save_payments()
        return {"payment_id": payment_id, "provider": None, "remote_id": None, "payment_url": "", "status": PaymentStatus.FAILED}

    def handle_webhook(self, provider, payload):
        if provider not in self.providers: raise ValueError(f"Proveedor no soportado: {provider}")
        result = self.providers[provider].verify_payment(payload)
        remote_id = result["remote_id"]
        status = result["status"]
        payment_id = next((pid for pid,d in self.payments.items() if d.get("remote_id")==remote_id and d.get("provider")==provider), None)
        if payment_id:
            self.payments[payment_id]["status"]=status
            self._log_attempt(payment_id, provider, status)
            self._save_payments()
        return {"payment_id": payment_id, "provider": provider, "remote_id": remote_id, "status": status}
        # -------------------------------
# Pentágono de Poder IA
# -------------------------------
class PentagonAI:
    """
    IA autónoma que coordina todas las funciones del proyecto:
    1. Estrategia
    2. Finanzas
    3. Marketing
    4. Contenido
    5. Operaciones
    """
    def __init__(self, payment_hub: PaymentHub):
        self.payment_hub = payment_hub
        self.capital = 0
        self.is_running = True
        self.ias = {
            "estrategia": self.estrategia,
            "finanzas": self.finanzas,
            "marketing": self.marketing,
            "contenido": self.contenido,
            "operaciones": self.operaciones
        }

    # Funciones IA (pueden implementarse en la Fase 2 para decisiones más complejas)
    def estrategia(self): pass
    def finanzas(self): pass
    def marketing(self): pass
    def contenido(self): pass
    def operaciones(self): pass

    def run(self):
        """
        Ciclo continuo de decisión autónoma según pagos completados.
        """
        while self.is_running:
            try:
                self.capital = sum(p.get("amount",0) for p in self.payment_hub.payments.values() if p["status"]==PaymentStatus.COMPLETED)
                for name, func in self.ias.items():
                    func()
                time.sleep(10)  # loop de 10s, puede ajustarse según necesidad
            except Exception as e:
                logging.error(f"[PentagonAI] Error en loop: {str(e)}")
                time.sleep(5)
 
    # -------------------------------
# Ejecutar App (Web + IA)
# -------------------------------
if __name__ == "__main__":
    

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    # Inicializar PaymentHub
    p_hub = PaymentHub()

    # Inicializar Pentágono de Poder IA
    ai_engine = PentagonAI(p_hub)

    # Ejecutar IA en un hilo separado
    threading.Thread(target=ai_engine.run, daemon=True).start()

    # Ejecutar servidor Flask principal
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Servidor Web iniciado en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
