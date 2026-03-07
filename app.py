from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3, hashlib, os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tamoios_secret_key_2026'

DB_PATH = 'tamoios.db'
UPLOAD_FOLDER = 'static/comprovantes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
         'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

CATEGORIAS = ['Luz', 'Água', 'Limpeza', 'Outros']

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# ─── AUTH ────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'casa' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        casa = request.form.get('casa', '').strip()
        senha = request.form.get('senha', '').strip()
        db = get_db()
        user = db.execute('SELECT * FROM usuarios WHERE casa = ?', (casa,)).fetchone()
        db.close()
        if user and user['senha_hash'] == hash_senha(senha) and user['ativo']:
            session['casa'] = user['casa']
            session['is_admin'] = bool(user['is_admin'])
            session['nome'] = user['nome']
            return redirect(url_for('index'))
        flash('Casa ou senha incorretos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── RESUMO DO MÊS ───────────────────────────────────

@app.route('/')
@login_required
def index():
    mes  = int(request.args.get('mes', datetime.now().month))
    ano  = int(request.args.get('ano', datetime.now().year))
    db   = get_db()
    despesas  = db.execute('SELECT * FROM despesas WHERE mes=? AND ano=? ORDER BY id', (mes, ano)).fetchall()
    pagamentos = db.execute('SELECT * FROM pagamentos WHERE mes=? AND ano=?', (mes, ano)).fetchall()
    usuarios  = db.execute('SELECT * FROM usuarios ORDER BY CAST(casa AS INTEGER)').fetchall()
    db.close()

    total = sum(d['valor'] for d in despesas)
    cota  = round(total / 10, 2) if total > 0 else 0
    casas_pagas = {str(p['casa']) for p in pagamentos if p['pago']}

    anos_disp = list(range(2024, datetime.now().year + 2))

    return render_template('index.html',
        despesas=despesas, total=total, cota=cota,
        mes=mes, ano=ano, meses=MESES, anos=anos_disp,
        casas_pagas=casas_pagas, usuarios=usuarios,
        categorias=CATEGORIAS
    )

# ─── DESPESAS (admin) ────────────────────────────────

@app.route('/despesa/add', methods=['POST'])
@admin_required
def add_despesa():
    descricao  = request.form.get('descricao', '').strip()
    categoria  = request.form.get('categoria', 'Outros')
    valor_str  = request.form.get('valor', '0').replace(',', '.')
    mes        = int(request.form.get('mes', datetime.now().month))
    ano        = int(request.form.get('ano', datetime.now().year))

    try:
        valor = float(valor_str)
        if valor <= 0 or not descricao:
            raise ValueError
    except ValueError:
        flash('Dados inválidos.', 'error')
        return redirect(url_for('index', mes=mes, ano=ano))

    comprovante = None
    if 'comprovante' in request.files:
        f = request.files['comprovante']
        if f and f.filename and allowed_file(f.filename):
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(f.filename)}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            comprovante = fname

    db = get_db()
    db.execute(
        'INSERT INTO despesas (mes, ano, descricao, categoria, valor, comprovante) VALUES (?,?,?,?,?,?)',
        (mes, ano, descricao, categoria, valor, comprovante)
    )
    db.commit()
    db.close()
    flash('Despesa lançada com sucesso!', 'success')
    return redirect(url_for('index', mes=mes, ano=ano))

@app.route('/despesa/delete/<int:id>', methods=['POST'])
@admin_required
def delete_despesa(id):
    mes = int(request.form.get('mes', datetime.now().month))
    ano = int(request.form.get('ano', datetime.now().year))
    db = get_db()
    d = db.execute('SELECT * FROM despesas WHERE id=?', (id,)).fetchone()
    if d and d['comprovante']:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], d['comprovante']))
        except: pass
    db.execute('DELETE FROM despesas WHERE id=?', (id,))
    db.commit()
    db.close()
    flash('Despesa removida.', 'success')
    return redirect(url_for('index', mes=mes, ano=ano))

# ─── PAGAMENTOS (admin) ──────────────────────────────

@app.route('/pagamento/toggle', methods=['POST'])
@admin_required
def toggle_pagamento():
    casa = request.form.get('casa')
    mes  = int(request.form.get('mes'))
    ano  = int(request.form.get('ano'))
    db   = get_db()
    reg  = db.execute('SELECT * FROM pagamentos WHERE casa=? AND mes=? AND ano=?', (casa, mes, ano)).fetchone()
    if reg:
        novo = 0 if reg['pago'] else 1
        db.execute('UPDATE pagamentos SET pago=?, data_pag=? WHERE id=?',
                   (novo, datetime.now().strftime('%Y-%m-%d') if novo else None, reg['id']))
    else:
        db.execute('INSERT INTO pagamentos (casa, mes, ano, pago, data_pag) VALUES (?,?,?,1,?)',
                   (casa, mes, ano, datetime.now().strftime('%Y-%m-%d')))
    db.commit()
    db.close()
    return redirect(url_for('index', mes=mes, ano=ano))

# ─── DASHBOARD ───────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    ano = int(request.args.get('ano', datetime.now().year))
    db  = get_db()

    rows = db.execute(
        'SELECT mes, categoria, SUM(valor) as total FROM despesas WHERE ano=? GROUP BY mes, categoria ORDER BY mes',
        (ano,)
    ).fetchall()

    # Montar estrutura por mês
    dados_mes = {}
    for r in rows:
        m = r['mes']
        if m not in dados_mes:
            dados_mes[m] = {'Luz': 0, 'Água': 0, 'Limpeza': 0, 'Outros': 0, 'total': 0}
        dados_mes[m][r['categoria']] = round(r['total'], 2)
        dados_mes[m]['total'] = round(dados_mes[m]['total'] + r['total'], 2)

    # Totais por categoria no ano
    cat_ano = db.execute(
        'SELECT categoria, SUM(valor) as total FROM despesas WHERE ano=? GROUP BY categoria',
        (ano,)
    ).fetchall()

    # Resumo geral
    total_ano = sum(r['total'] for r in cat_ano)
    media_mes = round(total_ano / 12, 2)
    mes_mais_caro = max(dados_mes.items(), key=lambda x: x[1]['total'], default=(None, {}))

    anos_disp = list(range(2024, datetime.now().year + 2))
    db.close()

    return render_template('dashboard.html',
        dados_mes=dados_mes, cat_ano=cat_ano,
        total_ano=total_ano, media_mes=media_mes,
        mes_mais_caro=mes_mais_caro,
        ano=ano, anos=anos_disp, meses=MESES
    )

# ─── ALTERAR SENHA ───────────────────────────────────

@app.route('/senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        atual = request.form.get('atual', '')
        nova  = request.form.get('nova', '')
        conf  = request.form.get('confirma', '')
        db    = get_db()
        user  = db.execute('SELECT * FROM usuarios WHERE casa=?', (session['casa'],)).fetchone()
        if user['senha_hash'] != hash_senha(atual):
            flash('Senha atual incorreta.', 'error')
        elif nova != conf:
            flash('Nova senha e confirmação não coincidem.', 'error')
        elif len(nova) < 4:
            flash('Senha deve ter pelo menos 4 caracteres.', 'error')
        else:
            db.execute('UPDATE usuarios SET senha_hash=? WHERE casa=?', (hash_senha(nova), session['casa']))
            db.commit()
            flash('Senha alterada com sucesso!', 'success')
        db.close()
    return render_template('senha.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
