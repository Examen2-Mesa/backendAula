#!/bin/bash
#alembic upgrade head  # aplica migraciones si no están
uvicorn app.main:app --host=0.0.0.0 --port=10000
