1. Crear entorno virtual 
    python -m venv venv
2. Activar entorno virtual 
    source venv/bin/activate # (Linux/Mac) 
    venv\Scripts\activate # (Windows)
3. Instalar las dependencias 
    pip install -r requirements.txt
4. Inciar alembic para migraciones (primera vez) 
    alembic init alembic 
    alembic revision --autogenerate -m "Primera migracion" 
    alembic upgrade head
5. Ejecutar 
    uvicorn app.main:app --reload
