# app/services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
from jinja2 import Template
from email.header import Header
from email.utils import formataddr

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para envío de correos electrónicos
    """

    def __init__(self):
        # Configuración SMTP (puedes mover esto a variables de entorno)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        self.from_name = os.getenv("FROM_NAME")

    def enviar_reporte_academico(
        self,
        destinatario: str,
        nombre_destinatario: str,
        datos_reporte: Dict,
        tipo_usuario: str,
    ) -> bool:
        """
        Envía el reporte académico completo por correo electrónico

        Args:
            destinatario: Email del destinatario
            nombre_destinatario: Nombre del destinatario
            datos_reporte: Datos del reporte académico
            tipo_usuario: Tipo de usuario (estudiante, padre, docente, admin)

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            # Crear el mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._generar_asunto(datos_reporte, tipo_usuario)
            msg["From"] = formataddr(
                (str(Header(self.from_name, "utf-8")), self.from_email)
            )
            # msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = destinatario

            # Generar el contenido HTML
            html_content = self._generar_html_reporte(
                datos_reporte, nombre_destinatario, tipo_usuario
            )

            # Crear las partes del mensaje
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Enviar el correo
            return self._enviar_email(msg)

        except Exception as e:
            logger.error(f"Error enviando reporte académico a {destinatario}: {str(e)}")
            return False

    def _generar_asunto(self, datos: Dict, tipo_usuario: str) -> str:
        """Genera el asunto del correo según el tipo de usuario"""
        estudiante = datos.get("estudiante", {})
        gestion = datos.get("gestion", {})

        asuntos = {
            "estudiante": f"📊 Tu Reporte Académico - Gestión {gestion.get('anio', '')}",
            "padre": f"👨‍👩‍👧‍👦 Reporte Académico de {estudiante.get('nombre', '')} {estudiante.get('apellido', '')} - Gestión {gestion.get('anio', '')}",
            "docente": f"👨‍🏫 Reporte Académico del Estudiante {estudiante.get('nombre', '')} {estudiante.get('apellido', '')}",
            "admin": f"🔧 Reporte Académico Completo - {estudiante.get('nombre', '')} {estudiante.get('apellido', '')}",
        }

        return asuntos.get(
            tipo_usuario, f"📋 Reporte Académico - Gestión {gestion.get('anio', '')}"
        )

    def _generar_html_reporte(
        self, datos: Dict, nombre_destinatario: str, tipo_usuario: str
    ) -> str:
        """Genera el contenido HTML del reporte"""

        template_html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Reporte Académico</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet" />
  <style>
    body {
      font-family: 'Inter', sans-serif;
      margin: 0;
      background: #f9fafb;
      color: #1e1e1e;
      line-height: 1.7;
    }
    .container {
      max-width: 920px;
      margin: 40px auto;
      padding: 0 20px;
    }
    .header {
      background-color: #003049;
      color: white;
      padding: 40px 30px;
      border-radius: 14px;
      text-align: center;
      box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .header h1 {
      font-size: 2.5rem;
      margin-bottom: 10px;
    }
    .header p {
      font-size: 1rem;
      opacity: 0.95;
    }

    .section {
      background: #ffffff;
      margin-top: 30px;
      border-radius: 14px;
      padding: 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .section h2 {
      font-size: 1.5rem;
      color: #003049;
      border-bottom: 2px solid #e5e5e5;
      padding-bottom: 10px;
      margin-bottom: 25px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }

    .stat {
      background: #e0ecf5;
      padding: 20px;
      border-radius: 10px;
      text-align: center;
    }
    .stat .value {
      font-size: 2rem;
      font-weight: 700;
      color: #003049;
    }
    .stat .label {
      font-size: 0.9rem;
      color: #555;
    }

    .materia-block {
      margin-bottom: 35px;
    }
    .materia-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
    }

    .badge {
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: bold;
      color: white;
    }
    .green { background: #38b000; }
    .orange { background: #f48c06; }
    .red { background: #d00000; }

    .periodo {
      background-color: #f1f5f9;
      padding: 18px 20px;
      border-left: 4px solid #669bbc;
      margin-top: 15px;
      border-radius: 10px;
    }

    .evaluaciones {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }
    .evaluaciones th, .evaluaciones td {
      border: 1px solid #ddd;
      padding: 10px;
      font-size: 0.9rem;
      text-align: center;
    }
    .evaluaciones th {
      background-color: #e9f1f7;
      color: #003049;
    }

    .prediccion {
      margin-top: 20px;
      background: linear-gradient(135deg, #ffffff, #e0fbfc);
      padding: 20px;
      border-radius: 12px;
      border-left: 6px solid #669bbc;
    }

    .prediccion h4 {
      margin-top: 0;
      color: #003049;
    }

    .alert-info {
      margin-top: 20px;
      background-color: #eaf4fc;
      padding: 14px 18px;
      border-left: 4px solid #669bbc;
      border-radius: 8px;
    }

    .footer {
      text-align: center;
      margin: 60px 0 20px;
      font-size: 0.9rem;
      color: #777;
    }

    @media(max-width: 600px) {
      .materia-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📘 Reporte Académico</h1>
      <p>Hola {{ nombre_destinatario }}, aquí tienes {{ mensaje_personalizado }}</p>
    </div>

    <div class="section">
      <h2>👤 Datos del Estudiante</h2>
      <div class="grid">
        <div><strong>Nombre:</strong> {{ estudiante.nombre }} {{ estudiante.apellido }}</div>
        <div><strong>Código:</strong> {{ estudiante.codigo }}</div>
        <div><strong>Correo:</strong> {{ estudiante.correo or 'No registrado' }}</div>
        <div><strong>Gestión:</strong> {{ gestion.anio }} - {{ gestion.descripcion }}</div>
      </div>
    </div>

    <div class="section">
      <h2>📊 Estadísticas Generales</h2>
      <div class="grid">
        <div class="stat">
          <div class="value">{{ estadisticas_generales.promedio_general }}</div>
          <div class="label">Promedio General</div>
        </div>
        <div class="stat">
          <div class="value">{{ estadisticas_generales.total_materias }}</div>
          <div class="label">Materias</div>
        </div>
        <div class="stat">
          <div class="value">{{ estadisticas_generales.total_evaluaciones }}</div>
          <div class="label">Evaluaciones</div>
        </div>
        <div class="stat">
          <div class="value">{{ estadisticas_generales.promedio_predicciones }}</div>
          <div class="label">Predicción ML</div>
        </div>
      </div>

      {% if estadisticas_generales.mejor_materia %}
      <div class="alert-info">
        🏆 <strong>Mejor materia:</strong> {{ estadisticas_generales.mejor_materia }}
      </div>
      {% endif %}
    </div>

    {% for materia_data in materias %}
    <div class="section materia-block">
      <div class="materia-header">
        <h3>📘 {{ materia_data.materia.nombre }}</h3>
        <span class="badge {% if materia_data.estadisticas.promedio_rendimiento < 60 %}red{% elif materia_data.estadisticas.promedio_rendimiento < 80 %}orange{% else %}green{% endif %}">
          {{ materia_data.estadisticas.promedio_rendimiento }}
        </span>
      </div>
      <p><strong>Descripción:</strong> {{ materia_data.materia.descripcion }}</p>

      {% if materia_data.docente %}
      <p><strong>👨‍🏫 Docente:</strong> {{ materia_data.docente.nombre }} {{ materia_data.docente.apellido }}<br/>
      <strong>Correo:</strong> {{ materia_data.docente.correo }}
      {% if materia_data.docente.telefono %} | <strong>Tel:</strong> {{ materia_data.docente.telefono }}{% endif %}</p>
      {% endif %}

      {% for periodo in materia_data.periodos %}
      <div class="periodo">
        <strong>{{ periodo.periodo_nombre }}</strong> ({{ periodo.fecha_inicio }} - {{ periodo.fecha_fin }})<br/>
        <strong>Nota Final:</strong> {{ periodo.rendimiento.nota_final }}

        {% if periodo.rendimiento.detalle_evaluaciones %}
        <table class="evaluaciones">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Promedio</th>
              <th>Peso (%)</th>
              <th>Aporte</th>
            </tr>
          </thead>
          <tbody>
            {% for eval in periodo.rendimiento.detalle_evaluaciones %}
            <tr>
              <td>{{ eval.tipo_nombre }}</td>
              <td>{{ eval.promedio }}</td>
              <td>{{ eval.peso }}</td>
              <td>{{ eval.aporte }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% endif %}

        {% if periodo.prediccion_ml %}
        <div class="prediccion">
          <h4>🔮 Predicción de Rendimiento</h4>
          <p><strong>Resultado:</strong> {{ periodo.prediccion_ml.resultado_numerico }}</p>
          <p><strong>Clasificación:</strong> {{ periodo.prediccion_ml.clasificacion }}</p>
          <p><strong>Asistencia:</strong> {{ periodo.prediccion_ml.porcentaje_asistencia }}%</p>
          <p><strong>Participación:</strong> {{ periodo.prediccion_ml.promedio_participacion }}</p>
        </div>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endfor %}

    <div class="footer">
      📅 Reporte generado el {{ fecha_generacion }}<br/>
      AsistIA - Aula Inteligente<br/>
      <em>Este es un mensaje generado automáticamente.</em>
    </div>
  </div>
</body>
</html>

        """

        # Preparar datos para el template
        template_data = {
            "nombre_destinatario": nombre_destinatario,
            "mensaje_personalizado": self._generar_mensaje_personalizado(
                tipo_usuario, datos.get("estudiante", {})
            ),
            "estudiante": datos.get("estudiante", {}),
            "gestion": datos.get("gestion", {}),
            "estadisticas_generales": datos.get("estadisticas_generales", {}),
            "materias": datos.get("materias", []),
            "fecha_generacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }

        # Renderizar template
        template = Template(template_html)
        return template.render(**template_data)

    def _generar_mensaje_personalizado(
        self, tipo_usuario: str, estudiante: Dict
    ) -> str:
        """Genera mensaje personalizado según el tipo de usuario"""
        mensajes = {
            "estudiante": "tu reporte académico completo",
            "padre": f"el reporte académico de tu hijo/a {estudiante.get('nombre', '')}",
            "docente": f"el reporte del estudiante {estudiante.get('nombre', '')} en tus materias",
            "admin": f"el reporte académico completo del estudiante {estudiante.get('nombre', '')}",
        }
        return mensajes.get(tipo_usuario, "el reporte académico solicitado")

    def _enviar_email(self, msg: MIMEMultipart) -> bool:
        """Envía el email usando SMTP"""
        try:
            # Crear conexión segura
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)

                # Enviar email
                server.send_message(msg)

            logger.info(f"Email enviado correctamente a {msg['To']}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return False

    def enviar_email_simple(
        self, destinatario: str, asunto: str, mensaje: str, es_html: bool = False
    ) -> bool:
        """
        Envía un email simple con texto plano o HTML

        Args:
            destinatario: Email del destinatario
            asunto: Asunto del correo
            mensaje: Contenido del mensaje
            es_html: Si el mensaje está en formato HTML

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            msg = MIMEMultipart()
            msg["Subject"] = asunto
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = destinatario

            # Agregar contenido
            if es_html:
                msg.attach(MIMEText(mensaje, "html", "utf-8"))
            else:
                msg.attach(MIMEText(mensaje, "plain", "utf-8"))

            return self._enviar_email(msg)

        except Exception as e:
            logger.error(f"Error enviando email simple a {destinatario}: {str(e)}")
            return False
