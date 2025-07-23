import cloudinary
import cloudinary.uploader # type: ignore
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUD_API_SECRET"),
)


def subir_imagen_a_cloudinary(file, nombre_completo: str):
    carpeta = f"perfil/{nombre_completo.replace(' ', '_')}"
    result = cloudinary.uploader.upload(file.file, folder=carpeta)
    return result.get("secure_url")
