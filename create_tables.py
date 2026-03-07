import os, psycopg2

def init_postgress():
    url = os.environ.get('DATABASE_URL')
    if not url: return print("Erro: DATABASE_URL não encontrada.")
    
    conn = psycopg2.connect(url, sslmode='require')
    cur = conn.cursor()
    
    # SQL adaptado para PostgreSQL (Serial em vez de Autoincrement)
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
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Tabelas criadas no Postgres!")

if __name__ == '__main__':
    init_postgress()