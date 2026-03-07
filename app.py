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

# 1. FUNÇÕES DE BANCO E UTILITÁRIOS
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

# 2. DECORADORES (ESSENCIAIS NO TOPO)
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'casa' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'casa' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Acesso restrito à administradora.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# 3. FUNÇÃO DE INICIALIZAÇÃO AUTOMÁTICA
def auto_init_db():
    if DATABASE_URL:
        try:
            conn, cur = get_db()
            # cur.execute("DROP TABLE IF EXISTS usuarios CASCADE;") # DESCOMENTE SE O ERRO DE COLUNA PERSISTIR
            cur.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    casa TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    senha_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    ativo INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS despesas (
                    id SERIAL PRIMARY KEY,
                    mes INTEGER NOT NULL, ano INTEGER NOT NULL,
                    descricao TEXT NOT NULL, categoria TEXT NOT NULL,
                    valor NUMERIC NOT NULL, comprovante TEXT
                );
                CREATE TABLE IF NOT EXISTS pagamentos (
                    id SERIAL PRIMARY KEY,
                    casa TEXT NOT NULL,
                    mes INTEGER NOT NULL,
                    ano INTEGER NOT NULL,
                    pago INTEGER DEFAULT 0,
                    data_pag TEXT,
                    UNIQUE(casa, mes, ano)
                );
            ''')
            admin_senha = hash_senha('tamoios8')
            cur.execute("""
                INSERT INTO usuarios (casa, nome, senha_hash, is_admin) 
                VALUES (%s, %s, %s, %s) ON CONFLICT (casa) DO NOTHING
            """, ('Casa 08', 'Ivonete - Casa 08', admin_senha, 1))
            conn.commit()
            conn.close()
            print("✅ Banco sincronizado com sucesso!")
        except Exception as e:
            print(f"❌ Erro no Auto-Init: {e}")

auto_init_db()

# 4. ROTAS
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'casa' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        casa = request.form.get('casa', '').strip()
        senha = request.form.get('senha', '').strip()
        conn, db = get_db()
        db.execute('SELECT * FROM usuarios WHERE casa = %s', (casa,))
        user = db.fetchone()
        conn.close()
        if user and user['senha_hash'] == hash_senha(senha) and user['ativo']:
            session['casa'] = user['casa']
            session['is_admin'] = bool(user['is_admin'])
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
