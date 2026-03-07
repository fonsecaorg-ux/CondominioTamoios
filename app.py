from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import hashlib, os, psycopg2 # Adicionado psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import urlparse # Para tratar a URL do Render

app = Flask(__name__)
app.secret_key = 'tamoios_secret_key_2026'

# --- CONFIGURAÇÃO DE BANCO DINÂMICA ---
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL:
        # Conexão para o RENDER (PostgreSQL)
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # Faz o Postgres retornar dicionários igual ao SQLite Row
        from psycopg2.extras import DictCursor
        return conn, conn.cursor(cursor_factory=DictCursor)
    else:
        # Conexão para CASA (SQLite)
        import sqlite3
        conn = sqlite3.connect('tamoios.db')
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()

# --- ATUALIZAÇÃO DAS CHAMADAS NO SEU CÓDIGO ---
# Exemplo de como você deve ajustar suas funções de rota:
@app.route('/')
@login_required
def index():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))
    
    conn, db = get_db()
    db.execute('SELECT * FROM despesas WHERE mes=%s AND ano=%s ORDER BY id', (mes, ano)) # Use %s para Postgres
    despesas = db.fetchall()
    
    # ... restante do seu cálculo ...
    conn.close()
    return render_template('index.html', ...)
