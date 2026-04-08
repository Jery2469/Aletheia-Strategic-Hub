import os
import logging
from flask import Flask, render_template_string

# Configuración básica de logs (visible en Railway)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

class AletheiaHub:
    def __init__(self):
        self.config = {
            "GROQ": os.environ.get('GROQ_API_KEY'),
            "TAVILY": os.environ.get('TAVILY_API_KEY'),
            "TROPI_ID": os.environ.get('HUB_TROPIPAY_CLIENT_ID'),
            "BASE_URL": os.environ.get('HUB_BASE_URL')
        }
        self.validate_config()

    def validate_config(self):
        missing = [key for key, value in self.config.items() if value is None]
        if missing:
            logging.warning(f"⚠️ Faltan variables de entorno: {missing}")
        else:
            logging.info("✅ Todas las variables de entorno cargadas correctamente")

hub = AletheiaHub()

PORTADA = """
<!DOCTYPE html>
<html>
<head>
    <title>Aletheia Strategic Hub</title>
</head>
<body style="background:#000;color:#D4AF37;text-align:center;padding:100px;font-family:serif;">
    <h1 style="font-size:3.5rem;letter-spacing:3px;">ALETHEIA STRATEGIC HUB</h1>
    
    <p style="color:#fff;letter-spacing:2px;font-family:sans-serif;">
        INGRESOS AUTÓNOMOS 24/7
    </p>

    <p style="color:#aaa;font-family:sans-serif;max-width:600px;margin:auto;">
        Plataforma estratégica impulsada por inteligencia artificial para la generación de capital líquido de forma autónoma, escalable y sin intervención humana.
    </p>

    <br><br>

    <a href="#" style="
        background:#ffc439;
        color:#003087;
        padding:18px 40px;
        border-radius:50px;
        text-decoration:none;
        font-weight:bold;
        font-family:sans-serif;
        border:2px solid #D4AF37;
        box-shadow:0 0 20px rgba(212,175,55,0.4);
    ">
        PAGAR CON PAYPAL
    </a>

    <br><br>

    <p style="color:#555;font-size:12px;">
        Sistema activo • Operando 24/7
    </p>
</body>
</html>
"""

@app.route('/')
def home():
    logging.info("🌐 Acceso a la página principal")
    return render_template_string(PORTADA)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port)
