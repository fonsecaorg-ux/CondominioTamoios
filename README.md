# 🏘️ Condomínio Tamoios — Sistema de Gestão

## Como rodar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Inicializar banco de dados
python init_db.py

# 3. Rodar o servidor
python app.py
# Acesse: http://localhost:5000
```

---

## 🔐 Usuários e Senhas Iniciais

| Casa | Usuário | Senha Padrão | Perfil |
|------|---------|-------------|--------|
| Casa 1 | 1 | casa1 | Morador |
| Casa 2 | 2 | casa2 | Morador |
| Casa 3 | 3 | casa3 | Morador |
| Casa 4 | 4 | casa4 | Morador |
| Casa 5 | 5 | casa5 | Morador |
| Casa 6 | 6 | casa6 | Morador |
| Casa 7 | 7 | casa7 | Morador |
| **Casa 8** | **8** | **tamoios8** | **ADMIN (Ivonete)** |
| Casa 9 | 9 | casa9 | Morador |
| Casa 10 | 10 | casa10 | Morador |

⚠️ **Oriente todos os moradores a trocar a senha no primeiro acesso.**

---

## 🚀 Deploy no Render (gratuito)

1. Criar conta em https://render.com
2. Novo projeto → **Web Service**
3. Conectar repositório GitHub (faça upload desse projeto)
4. Configurações:
   - **Build Command:** `pip install -r requirements.txt && python init_db.py`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3

---

## 📱 Funcionalidades

### Ivonete (Admin — Casa 8)
- Lançar despesas (Luz, Água, Limpeza, Outros)
- Anexar foto/PDF do comprovante
- Marcar/desmarcar pagamentos por casa
- Excluir despesas

### Todos os moradores
- Ver resumo do mês atual
- Ver histórico de meses anteriores
- Dashboard com gráficos anuais
- Alterar própria senha

---

## 📁 Estrutura do Projeto

```
tamoios/
├── app.py              # Aplicação principal
├── init_db.py          # Cria banco e usuários iniciais
├── requirements.txt
├── tamoios.db          # Banco SQLite (gerado automaticamente)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── index.html      # Resumo do mês
│   ├── dashboard.html  # Gráficos anuais
│   └── senha.html      # Alterar senha
└── static/
    └── comprovantes/   # Fotos/PDFs enviados pela Ivonete
```
