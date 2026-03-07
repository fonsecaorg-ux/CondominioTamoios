import sqlite3, hashlib, os

DB_PATH = 'tamoios.db'

def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            casa      TEXT UNIQUE NOT NULL,
            nome      TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            is_admin  INTEGER DEFAULT 0,
            ativo     INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS despesas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            mes         INTEGER NOT NULL,
            ano         INTEGER NOT NULL,
            descricao   TEXT NOT NULL,
            categoria   TEXT NOT NULL,
            valor       REAL NOT NULL,
            comprovante TEXT,
            criado_em   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS pagamentos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            casa     TEXT NOT NULL,
            mes      INTEGER NOT NULL,
            ano      INTEGER NOT NULL,
            pago     INTEGER DEFAULT 0,
            data_pag TEXT,
            UNIQUE(casa, mes, ano)
        );
    ''')

    # Criar usuários padrão (casa = número para login: 1, 2, ... 8, ... 10; admin = admin geral)
    usuarios = [
        ('1',  'Casa 01',           'casa1',       0),
        ('2',  'Casa 02',           'casa2',       0),
        ('3',  'Casa 03',           'casa3',       0),
        ('4',  'Casa 04',           'casa4',       0),
        ('5',  'Casa 05',           'casa5',       0),
        ('6',  'Casa 06',           'casa6',       0),
        ('7',  'Casa 07',           'casa7',       0),
        ('8',  'Ivonete - Casa 08', 'tamoios8',    1),  # Ivonete – única moradora que pode adicionar dados e uploads
        ('9',  'Casa 09',           'casa9',       0),
        ('10', 'Casa 10',           'casa10',      0),
        ('admin', 'Administração',   'tamoios@dev', 1),  # Admin geral do aplicativo
    ]

    for casa, nome, senha, is_admin in usuarios:
        existing = c.execute('SELECT id FROM usuarios WHERE casa=?', (casa,)).fetchone()
        if not existing:
            c.execute(
                'INSERT INTO usuarios (casa, nome, senha_hash, is_admin) VALUES (?,?,?,?)',
                (casa, nome, hash_senha(senha), is_admin)
            )

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")
    print("\nUsuários criados:")
    print("  Casa 8 (Admin/Ivonete): senha = tamoios8")
    print("  Demais casas: senha = casa1, casa2 ... casa10")
    print("\n⚠️  Oriente cada morador a trocar a senha no primeiro acesso.")

if __name__ == '__main__':
    init_db()
