from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import hashlib, os, psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tamoios_secret_key_2026'

# Configurações de Pasta e Banco
UPLOAD_FOLDER = 'static/comprovantes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE_URL = os.environ.get('DATABASE_URL')

MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
         'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
CATEGORIAS = ['Luz', 'Água', 'Limpeza', 'Outros']

def get_db():
    if DATABASE_URL:
        # Conexão Render (PostgreSQL)
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn, conn.cursor(cursor_factory=DictCursor)
    else:
        # Conexão Local (SQLite)
        import sqlite3
        conn = sqlite3.connect('tamoios.db')
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ... (Seus decorators login_required e admin_required permanecem iguais) ...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'casa' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        casa = request.form.get('casa', '').strip()
        senha = request.form.get('senha', '').strip()
        conn, db = get_db()
        # Mudança de ? para %s para compatibilidade Postgres
        db.execute('SELECT * FROM usuarios WHERE casa = %s', (casa,))
        user = db.fetchone()
        conn.close()
        if user and user['senha_hash'] == hash_senha(senha) and user['ativo']:
            session['casa'] = user['casa']; session['is_admin'] = bool(user['is_admin'])
            session['nome'] = user['nome']
            return redirect(url_for('index'))
        flash('Casa ou senha incorretos.', 'error')
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))
    conn, db = get_db()
    db.execute('SELECT * FROM despesas WHERE mes=%s AND ano=%s ORDER BY id', (mes, ano))
    despesas = db.fetchall()
    db.execute('SELECT * FROM pagamentos WHERE mes=%s AND ano=%s', (mes, ano))
    pagamentos = db.fetchall()
    db.execute('SELECT * FROM usuarios ORDER BY id ASC')
    usuarios = db.fetchall()
    conn.close()

    total = sum(d['valor'] for d in despesas)
    cota = round(total / 10, 2) if total > 0 else 0
    casas_pagas = {str(p['casa']) for p in pagamentos if p['pago']}
    return render_template('index.html', despesas=despesas, total=total, cota=cota, 
                           mes=mes, ano=ano, meses=MESES, casas_pagas=casas_pagas, usuarios=usuarios)

# NOTA: Todas as outras rotas (add_despesa, delete, toggle) devem trocar '?' por '%s'
