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
        tipo_usuario: str
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
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._generar_asunto(datos_reporte, tipo_usuario)
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = destinatario

            # Generar el contenido HTML
            html_content = self._generar_html_reporte(datos_reporte, nombre_destinatario, tipo_usuario)
            
            # Crear las partes del mensaje
            html_part = MIMEText(html_content, 'html', 'utf-8')
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
            "admin": f"🔧 Reporte Académico Completo - {estudiante.get('nombre', '')} {estudiante.get('apellido', '')}"
        }
        
        return asuntos.get(tipo_usuario, f"📋 Reporte Académico - Gestión {gestion.get('anio', '')}")

    def _generar_html_reporte(self, datos: Dict, nombre_destinatario: str, tipo_usuario: str) -> str:
        """Genera el contenido HTML del reporte"""
        
        template_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Académico</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2rem;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .info-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }
        .info-card h2 {
            color: #667eea;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .estudiante-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .estadisticas {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-item {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1976d2;
        }
        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }
        .materia {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }
        .materia-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .materia-nombre {
            font-size: 1.2rem;
            font-weight: bold;
            color: #333;
        }
        .promedio-materia {
            background: #4caf50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        .promedio-bajo {
            background: #f44336;
        }
        .promedio-medio {
            background: #ff9800;
        }
        .docente-info {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .periodos {
            margin-top: 15px;
        }
        .periodo {
            background: #fafafa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
        }
        .evaluaciones {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .evaluacion {
            background: white;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            text-align: center;
        }
        .prediccion {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .prediccion h4 {
            margin: 0 0 10px 0;
            color: #2d3748;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9rem;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .alert-info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        @media (max-width: 600px) {
            .estudiante-info {
                grid-template-columns: 1fr;
            }
            .estadisticas {
                grid-template-columns: 1fr;
            }
            .evaluaciones {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Reporte Académico Completo</h1>
        <p>Hola {{ nombre_destinatario }}, aquí tienes {{ mensaje_personalizado }}</p>
    </div>

    <div class="info-card">
        <h2>👤 Información del Estudiante</h2>
        <div class="estudiante-info">
            <div><strong>Nombre:</strong> {{ estudiante.nombre }} {{ estudiante.apellido }}</div>
            <div><strong>Código:</strong> {{ estudiante.codigo }}</div>
            <div><strong>Correo:</strong> {{ estudiante.correo or 'No registrado' }}</div>
            <div><strong>Gestión:</strong> {{ gestion.anio }} - {{ gestion.descripcion }}</div>
        </div>
    </div>

    <div class="info-card">
        <h2>📈 Estadísticas Generales</h2>
        <div class="estadisticas">
            <div class="stat-item">
                <div class="stat-number">{{ estadisticas_generales.promedio_general }}</div>
                <div class="stat-label">Promedio General</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ estadisticas_generales.total_materias }}</div>
                <div class="stat-label">Total Materias</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ estadisticas_generales.total_evaluaciones }}</div>
                <div class="stat-label">Evaluaciones</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ estadisticas_generales.promedio_predicciones }}</div>
                <div class="stat-label">Predicción ML</div>
            </div>
        </div>
        
        {% if estadisticas_generales.mejor_materia %}
        <div class="alert alert-info">
            🏆 <strong>Mejor materia:</strong> {{ estadisticas_generales.mejor_materia }}
        </div>
        {% endif %}
    </div>

    {% for materia_data in materias %}
    <div class="info-card">
        <div class="materia">
            <div class="materia-header">
                <div class="materia-nombre">📚 {{ materia_data.materia.nombre }}</div>
                <div class="promedio-materia {% if materia_data.estadisticas.promedio_rendimiento < 60 %}promedio-bajo{% elif materia_data.estadisticas.promedio_rendimiento < 80 %}promedio-medio{% endif %}">
                    {{ materia_data.estadisticas.promedio_rendimiento }}
                </div>
            </div>
            
            <p><strong>Descripción:</strong> {{ materia_data.materia.descripcion }}</p>
            
            {% if materia_data.docente %}
            <div class="docente-info">
                <strong>👨‍🏫 Docente:</strong> {{ materia_data.docente.nombre }} {{ materia_data.docente.apellido }}
                <br><strong>Contacto:</strong> {{ materia_data.docente.correo }}
                {% if materia_data.docente.telefono %}
                | {{ materia_data.docente.telefono }}
                {% endif %}
            </div>
            {% endif %}

            <div class="periodos">
                <h4>📅 Rendimiento por Períodos</h4>
                {% for periodo in materia_data.periodos %}
                <div class="periodo">
                    <h5>{{ periodo.periodo_nombre }} ({{ periodo.fecha_inicio }} - {{ periodo.fecha_fin }})</h5>
                    
                    <div><strong>Nota Final:</strong> {{ periodo.rendimiento.nota_final }}</div>
                    
                    {% if periodo.rendimiento.detalle_evaluaciones %}
                    <div class="evaluaciones">
                        {% for eval in periodo.rendimiento.detalle_evaluaciones %}
                        <div class="evaluacion">
                            <strong>{{ eval.tipo_nombre }}</strong><br>
                            Promedio: {{ eval.promedio }}<br>
                            Peso: {{ eval.peso }}%<br>
                            Aporte: {{ eval.aporte }}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if periodo.prediccion_ml %}
                    <div class="prediccion">
                        <h4>🤖 Predicción de Machine Learning</h4>
                        <div><strong>Predicción Numérica:</strong> {{ periodo.prediccion_ml.resultado_numerico }}</div>
                        <div><strong>Clasificación:</strong> {{ periodo.prediccion_ml.clasificacion }}</div>
                        <div><strong>Asistencia:</strong> {{ periodo.prediccion_ml.porcentaje_asistencia }}%</div>
                        <div><strong>Participación:</strong> {{ periodo.prediccion_ml.promedio_participacion }}</div>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endfor %}

    <div class="footer">
        <p>📧 Reporte generado automáticamente el {{ fecha_generacion }}</p>
        <p>🏫 Sistema de Gestión Académica</p>
        <p><em>Este es un correo automático, por favor no responder directamente.</em></p>
    </div>
</body>
</html>
        """

        # Preparar datos para el template
        template_data = {
            'nombre_destinatario': nombre_destinatario,
            'mensaje_personalizado': self._generar_mensaje_personalizado(tipo_usuario, datos.get("estudiante", {})),
            'estudiante': datos.get("estudiante", {}),
            'gestion': datos.get("gestion", {}),
            'estadisticas_generales': datos.get("estadisticas_generales", {}),
            'materias': datos.get("materias", []),
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        # Renderizar template
        template = Template(template_html)
        return template.render(**template_data)

    def _generar_mensaje_personalizado(self, tipo_usuario: str, estudiante: Dict) -> str:
        """Genera mensaje personalizado según el tipo de usuario"""
        mensajes = {
            "estudiante": "tu reporte académico completo",
            "padre": f"el reporte académico de tu hijo/a {estudiante.get('nombre', '')}",
            "docente": f"el reporte del estudiante {estudiante.get('nombre', '')} en tus materias",
            "admin": f"el reporte académico completo del estudiante {estudiante.get('nombre', '')}"
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
        self, 
        destinatario: str, 
        asunto: str, 
        mensaje: str,
        es_html: bool = False
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
            msg['Subject'] = asunto
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = destinatario

            # Agregar contenido
            if es_html:
                msg.attach(MIMEText(mensaje, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(mensaje, 'plain', 'utf-8'))

            return self._enviar_email(msg)

        except Exception as e:
            logger.error(f"Error enviando email simple a {destinatario}: {str(e)}")
            return False