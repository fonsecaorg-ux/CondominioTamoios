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
    ('Casa 01', 'Casa 01', 'casa1',       0),
    ('Casa 02', 'Casa 02', 'casa2',       0),
    ('Casa 03', 'Casa 03', 'casa3',       0),
    ('Casa 04', 'Casa 04', 'casa4',       0),
    ('Casa 05', 'Casa 05', 'casa5',       0),
    ('Casa 06', 'Ivonete - Casa 06', 'tamoios6',    1),
    ('Casa 07', 'Casa 07', 'casa7',       0),
    ('Casa 08', 'Casa 08', 'casa8',       0),
    ('Casa 09', 'Casa 09', 'casa9',       0),
    ('Casa 10', 'Casa 10', 'casa10',      0),
    ('admin',   'Administração', 'tamoios@dev', 1),
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
