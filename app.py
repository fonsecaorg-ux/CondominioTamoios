from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from functools import wraps
import hashlib, os, psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'tamoios_secret_key_2026'

# Configurações
UPLOAD_FOLDER = 'static/comprovantes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE_URL = os.environ.get('DATABASE_URL')

MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
         'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
CATEGORIAS = ['Luz', 'Água', 'Limpeza', 'Outros']

def get_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn, conn.cursor(cursor_factory=DictCursor)
    else:
        import sqlite3
        conn = sqlite3.connect('tamoios.db')
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()

def run_query(cursor, sql, args=()):
    """Executa query com placeholder correto (PostgreSQL %s, SQLite ?)."""
    if not DATABASE_URL:
        sql = sql.replace('%s', '?')
    cursor.execute(sql, args)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def pode_gerenciar():
    return session.get('casa') in ('Casa 06', 'admin', '6', '06')

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

def gerente_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'casa' not in session:
            return redirect(url_for('login'))
        if not pode_gerenciar():
            flash('Apenas a moradora da Casa 06 (Ivonete) ou o admin podem fazer esta ação.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ─── INIT BANCO (sem DROP — não apaga dados existentes) ──────────────────────
def auto_init_db():
    try:
        conn, cur = get_db()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id         SERIAL PRIMARY KEY,
                casa       TEXT UNIQUE NOT NULL,
                nome       TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                is_admin   INTEGER DEFAULT 0,
                ativo      INTEGER DEFAULT 1
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS despesas (
                id          SERIAL PRIMARY KEY,
                mes         INTEGER NOT NULL,
                ano         INTEGER NOT NULL,
                descricao   TEXT NOT NULL,
                categoria   TEXT NOT NULL,
                valor       NUMERIC NOT NULL,
                comprovante TEXT
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS pagamentos (
                id       SERIAL PRIMARY KEY,
                casa     TEXT NOT NULL,
                mes      INTEGER NOT NULL,
                ano      INTEGER NOT NULL,
                pago     INTEGER DEFAULT 0,
                data_pag TEXT,
                UNIQUE(casa, mes, ano)
            )
        ''')

        # Usuários padrão — só insere se não existirem
        usuarios = [
            ('Casa 01', 'Casa 01',           'casa1',       0),
            ('Casa 02', 'Casa 02',           'casa2',       0),
            ('Casa 03', 'Casa 03',           'casa3',       0),
            ('Casa 04', 'Casa 04',           'casa4',       0),
            ('Casa 05', 'Casa 05',           'casa5',       0),
            ('Casa 06', 'Ivonete - Casa 06', 'tamoios6',    1),
            ('Casa 07', 'Casa 07',           'casa7',       0),
            ('Casa 08', 'Casa 08',           'casa8',       0),
            ('Casa 09', 'Casa 09',           'casa9',       0),
            ('Casa 10', 'Casa 10',           'casa10',      0),
            ('admin',   'Administração',     'tamoios@dev', 1),
        ]

        for casa, nome, senha, is_admin in usuarios:
            cur.execute(
                '''INSERT INTO usuarios (casa, nome, senha_hash, is_admin)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (casa) DO NOTHING''',
                (casa, nome, hash_senha(senha), is_admin)
            )

        conn.commit()
        conn.close()
        print("✅ Banco inicializado!")
    except Exception as e:
        print(f"❌ Erro Init: {e}")

auto_init_db()

# ─── PWA ─────────────────────────────────────────────────────────────────────
@app.route('/manifest.webmanifest')
def manifest():
    return send_file(
        os.path.join(app.static_folder or 'static', 'manifest.webmanifest'),
        mimetype='application/manifest+json',
        max_age=86400,
    )

@app.route('/icon/<int:size>.png')
def icon_png(size):
    if size not in (192, 512):
        size = 192
    try:
        from PIL import Image, ImageDraw
        w = h = size
        img = Image.new('RGB', (w, h), color=(30, 64, 175))
        draw = ImageDraw.Draw(img)
        margin = w // 6
        draw.polygon([
            (w // 2, margin),
            (margin, h // 2 - 5),
            (w - margin, h // 2 - 5),
        ], fill=(14, 165, 233))
        draw.rectangle([margin, h // 2 - 5, w - margin, h - margin], fill=(59, 130, 246))
        draw.rectangle([w // 2 - 15, h // 2 + 10, w // 2 + 15, h - margin - 5], fill=(241, 245, 249))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png', max_age=86400 * 30)
    except Exception:
        buf = BytesIO()
        buf.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        buf.seek(0)
        return send_file(buf, mimetype='image/png', max_age=86400)

# ─── AUTH ─────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'casa' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        casa = request.form.get('casa', '').strip()
        senha = request.form.get('senha', '').strip()
        conn, db = get_db()
        run_query(db, 'SELECT * FROM usuarios WHERE casa = %s', (casa,))
        user = db.fetchone()
        conn.close()
        if user and user['senha_hash'] == hash_senha(senha) and user['ativo']:
            session['casa']     = user['casa']
            session['is_admin'] = bool(user['is_admin'])
            session['nome']     = user['nome']
            return redirect(url_for('index'))
        flash('Casa ou senha incorretos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── INDEX ────────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))
    conn, db = get_db()
    run_query(db, 'SELECT * FROM despesas WHERE mes=%s AND ano=%s ORDER BY id', (mes, ano))
    despesas = db.fetchall()
    run_query(db, 'SELECT * FROM pagamentos WHERE mes=%s AND ano=%s', (mes, ano))
    pagamentos = db.fetchall()
    run_query(db, "SELECT * FROM usuarios WHERE casa != %s ORDER BY id ASC", ('admin',))
    usuarios = db.fetchall()
    conn.close()

    total = sum(float(d['valor']) for d in despesas)
    cota  = round(total / 10, 2) if total > 0 else 0
    casas_pagas = {str(p['casa']) for p in pagamentos if p['pago']}
    anos_disp   = list(range(2024, datetime.now().year + 2))

    return render_template('index.html',
        despesas=despesas, total=total, cota=cota,
        mes=mes, ano=ano, meses=MESES, anos=anos_disp,
        casas_pagas=casas_pagas, usuarios=usuarios,
        categorias=CATEGORIAS,
        pode_gerenciar=pode_gerenciar()
    )

# ─── DESPESAS ────────────────────────────────────────────────────────────────
@app.route('/despesa/add', methods=['POST'])
@login_required
@gerente_required
def add_despesa():
    mes       = request.form.get('mes', type=int) or datetime.now().month
    ano       = request.form.get('ano', type=int) or datetime.now().year
    descricao = request.form.get('descricao', '').strip()
    categoria = request.form.get('categoria', 'Outros').strip()
    valor_str = request.form.get('valor', '0').strip().replace(',', '.')

    try:
        valor = float(valor_str) if valor_str else 0
    except ValueError:
        valor = 0

    if not descricao:
        flash('Informe a descrição da despesa.', 'error')
        return redirect(url_for('index', mes=mes, ano=ano))

    comprovante = None
    if 'comprovante' in request.files:
        f = request.files['comprovante']
        if f and f.filename:
            fn = secure_filename(f.filename)
            if fn:
                ext = os.path.splitext(fn)[1].lower() or '.bin'
                comprovante = f"{mes:02d}_{ano}_{datetime.now().strftime('%H%M%S')}_{fn[:20]}{ext}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], comprovante)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                f.save(path)

    conn, db = get_db()
    run_query(db,
        'INSERT INTO despesas (mes, ano, descricao, categoria, valor, comprovante) VALUES (%s,%s,%s,%s,%s,%s)',
        (mes, ano, descricao, categoria, valor, comprovante)
    )
    conn.commit()
    conn.close()
    flash('Despesa lançada.', 'success')
    return redirect(url_for('index', mes=mes, ano=ano))

@app.route('/despesa/<int:id>/delete', methods=['POST'])
@login_required
@gerente_required
def delete_despesa(id):
    mes = request.form.get('mes', type=int) or datetime.now().month
    ano = request.form.get('ano', type=int) or datetime.now().year
    conn, db = get_db()
    run_query(db, 'DELETE FROM despesas WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('Despesa removida.', 'success')
    return redirect(url_for('index', mes=mes, ano=ano))

# ─── PAGAMENTOS ───────────────────────────────────────────────────────────────
@app.route('/pagamento/toggle', methods=['POST'])
@login_required
@gerente_required
def toggle_pagamento():
    casa = request.form.get('casa', '').strip()
    mes  = request.form.get('mes', type=int) or datetime.now().month
    ano  = request.form.get('ano', type=int) or datetime.now().year

    if not casa or casa == 'admin':
        flash('Casa inválida.', 'error')
        return redirect(url_for('index', mes=mes, ano=ano))

    conn, db = get_db()
    run_query(db, 'SELECT id, pago FROM pagamentos WHERE casa=%s AND mes=%s AND ano=%s', (casa, mes, ano))
    row = db.fetchone()

    if row:
        novo = 0 if row['pago'] else 1
        run_query(db, 'UPDATE pagamentos SET pago=%s, data_pag=%s WHERE id=%s',
                  (novo, datetime.now().isoformat()[:10] if novo else None, row['id']))
    else:
        run_query(db, 'INSERT INTO pagamentos (casa, mes, ano, pago, data_pag) VALUES (%s,%s,%s,1,%s)',
                  (casa, mes, ano, datetime.now().isoformat()[:10]))

    conn.commit()
    conn.close()
    return redirect(url_for('index', mes=mes, ano=ano))

# ─── SENHA ────────────────────────────────────────────────────────────────────
@app.route('/senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'GET':
        return render_template('senha.html')

    atual    = request.form.get('atual', '').strip()
    nova     = request.form.get('nova', '').strip()
    confirma = request.form.get('confirma', '').strip()

    if not atual or not nova or not confirma:
        flash('Preencha todos os campos.', 'error')
        return render_template('senha.html')
    if nova != confirma:
        flash('Nova senha e confirmação não conferem.', 'error')
        return render_template('senha.html')
    if len(nova) < 4:
        flash('A nova senha deve ter no mínimo 4 caracteres.', 'error')
        return render_template('senha.html')

    conn, db = get_db()
    run_query(db, 'SELECT senha_hash FROM usuarios WHERE casa = %s', (session['casa'],))
    user = db.fetchone()

    if not user or user['senha_hash'] != hash_senha(atual):
        conn.close()
        flash('Senha atual incorreta.', 'error')
        return render_template('senha.html')

    run_query(db, 'UPDATE usuarios SET senha_hash = %s WHERE casa = %s', (hash_senha(nova), session['casa']))
    conn.commit()
    conn.close()
    flash('Senha alterada com sucesso!', 'success')
    return redirect(url_for('alterar_senha'))

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    ano = int(request.args.get('ano', datetime.now().year))
    conn, db = get_db()
    run_query(db, 'SELECT mes, categoria, valor FROM despesas WHERE ano = %s', (ano,))
    rows = db.fetchall()
    conn.close()

    dados_mes = {}
    for m in range(1, 13):
        dados_mes[m] = {'Luz': 0, 'Água': 0, 'Limpeza': 0, 'Outros': 0, 'total': 0}

    for r in rows:
        m   = r['mes']
        cat = r['categoria'] if r['categoria'] in dados_mes[m] else 'Outros'
        dados_mes[m][cat]    = float(dados_mes[m][cat]) + float(r['valor'])
        dados_mes[m]['total'] = dados_mes[m]['total']   + float(r['valor'])

    total_ano = sum(d['total'] for d in dados_mes.values())
    media_mes = round(total_ano / 12, 2) if total_ano else 0

    mes_mais_caro = None
    for m, d in dados_mes.items():
        if d['total'] > 0:
            if mes_mais_caro is None or d['total'] > mes_mais_caro[1]['total']:
                mes_mais_caro = (m, dict(d))

    anos_disp = list(range(2024, datetime.now().year + 2))

    return render_template('dashboard.html',
        meses=MESES, ano=ano, anos=anos_disp,
        total_ano=total_ano, media_mes=media_mes,
        mes_mais_caro=mes_mais_caro,
        dados_mes=dados_mes, cat_ano=dados_mes,
        meses_ordem=list(range(1, 13))
    )

# ─── ROTA DE MANUTENÇÃO (só dev) ─────────────────────────────────────────────
@app.route('/recreate-db-tamoios2026')
def recreate_db():
    if request.args.get('key') != 'tamoios@dev':
        return 'Acesso negado', 403
    try:
        auto_init_db()
        return 'Banco recriado com sucesso!'
    except Exception as e:
        return f'Erro: {str(e)}', 500

# ─── START ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)