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
| **Casa 8** | **8** | **tamoios8** | **Ivonete — pode adicionar dados e uploads** |
| Casa 9 | 9 | casa9 | Morador |
| Casa 10 | 10 | casa10 | Morador |
| **Admin geral** | **admin** | **tamoios@dev** | **Administração do aplicativo** |

⚠️ **Oriente todos os moradores a trocar a senha no primeiro acesso.** Qualquer usuário pode alterar a própria senha pelo menu **Senha** (ícone de chave) após o login.

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

## 📱 Mobile: atalho na tela (PWA)

No celular, abra o site no navegador (Chrome/Safari), use **“Adicionar à tela inicial”** / **“Add to Home Screen”**. O app aparecerá como atalho com o nome **Tamoios** e o ícone do condomínio. Ideal para uso no dia a dia.

## 🎨 Tema claro / escuro

O app tem um botão no topo (ícone de sol/lua) para alternar entre **tema escuro** (padrão) e **tema claro**. A escolha é salva no celular e mantida nas próximas visitas.

## 📱 Funcionalidades

### Ivonete (Casa 8) e Admin geral
- A **única moradora** que pode adicionar dados e fazer uploads é a da **Casa 8 (Ivonete)**.
- O **admin geral** (login: casa **admin**, senha padrão **tamoios@dev**) tem acesso total ao aplicativo.
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
