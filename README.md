# Auditoria de Energia — COSERN + Origo
## MB Energia

Ferramenta web para auditoria automática de faturas de energia solar (GDC).
Faz upload de PDFs da COSERN e Origo, extrai os dados automaticamente e calcula o desconto real obtido.

---

## Instalação na Hostinger (VPS)

### 1. Conecte via SSH
```bash
ssh usuario@seuservidor
```

### 2. Instale Python e dependências
```bash
pip install -r requirements.txt
```

### 3. Suba os arquivos
Copie a pasta inteira para `/var/www/mbenergia/auditoria/`

### 4. Rode o servidor
```bash
python app.py
```

---

## Instalação na Hostinger (Shared / cPanel)

A Hostinger shared **suporta Python via Passenger**. Siga:

1. No hPanel → **Gerenciador de Arquivos** → crie a pasta `public_html/auditoria/`
2. Faça upload de todos os arquivos nessa pasta
3. No hPanel → **Python** → crie um app apontando para essa pasta
4. Defina o arquivo de inicialização como `app.py`
5. Clique em **Iniciar**

A URL será: `https://mbenergia.com.br/auditoria/`

---

## Arquivos

```
auditoria/
  app.py          → servidor Flask (backend)
  parser.py       → leitor de PDFs COSERN e Origo
  requirements.txt → dependências Python
  static/
    index.html    → interface web
```

---

## Como usar

1. Acesse `https://mbenergia.com.br/auditoria/`
2. Arraste os PDFs das faturas (COSERN e Origo, qualquer ordem)
3. Configure o desconto contratado (padrão 20%)
4. Clique em **Analisar Faturas**
5. Veja o resultado e exporte o CSV se necessário
