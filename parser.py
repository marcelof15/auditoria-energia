import pdfplumber, re

def br_float(s):
    s = re.sub(r'[^0-9,]', '', s).replace(',','.')
    try: return float(s)
    except: return 0.0

def extrair_cosern(path):
    with pdfplumber.open(path) as pdf:
        texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    r = {}

    # UC
    m = re.search(r'CÓDIGO DA INSTALAÇÃO\s*\n?\s*(\d{7})', texto)
    if not m: m = re.search(r'\b(2\d{6})\b', texto)
    r['uc'] = m.group(1) if m else ''

    # Torre
    m = re.search(r'TORRE\s+(\w+)\s+BL', texto)
    r['torre'] = m.group(1).capitalize() if m else ''

    # Competência
    m = re.search(r'(\d{2}/20\d{2})\s+[\d,]+\s+\d{2}/\d{2}/20\d{2}', texto)
    if not m: m = re.search(r'\b((?:0[1-9]|1[0-2])/20\d{2})\b', texto)
    r['competencia'] = m.group(1) if m else ''

    # Consumo kWh
    m = re.search(r'Energia Ativa\s+Único\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)', texto)
    r['consumo_kwh'] = br_float(m.group(1)) if m else 0

    # TUSD
    m = re.search(r'Consumo-TUSD\s+kWh\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)', texto)
    r['tusd'] = br_float(m.group(1)) if m else 0

    # TE
    m = re.search(r'Consumo-TE\s+kWh\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)', texto)
    r['te'] = br_float(m.group(1)) if m else 0

    # Bandeira
    bandeiras = re.findall(r'Acrés\.?\s*(?:Band?\.?\s*)?VERMELHA(?:-P\d)?\s+([\d.,]+)', texto)
    r['bandeira'] = round(sum(br_float(v) for v in bandeiras), 2)

    # Iluminação pública
    m = re.search(r'Ilum\.\s*Púb\.\s*Municipal\s+([\d.,]+)', texto)
    r['iluminacao_publica'] = br_float(m.group(1)) if m else 0

    # Parcelas
    parcelas = re.findall(r'Parc\d+/\d+\s+\*\d+\s+([\d.,]+)', texto)
    r['parcelas'] = round(sum(br_float(v) for v in parcelas), 2)

    # G1 — créditos ORIGO (entram na base de desconto)
    g1_vals = re.findall(r'G1-Comp\.oUC-Ma-(?:TUSD|TE)\s+kWh\s+[\d.,]+-\s+[\d.,]+\s+([\d.,]+)-', texto)
    r['g1_credito'] = round(sum(br_float(v) for v in g1_vals), 2)
    g1_kwh = re.findall(r'G1-Comp\.oUC-Ma-TUSD\s+kWh\s+([\d.,]+)-', texto)
    r['g1_kwh'] = br_float(g1_kwh[0]) if g1_kwh else 0

    # G2 — geração própria (NÃO entram na base de desconto Origo)
    g2_vals = re.findall(r'G2Comp\.mUC-nM-(?:TUSD|TE)\s+kWh\s+[\d.,]+-\s+[\d.,]+\s+([\d.,]+)-', texto)
    r['g2_credito'] = round(sum(br_float(v) for v in g2_vals), 2)
    g2_kwh = re.findall(r'G2Comp\.mUC-nM-TUSD\s+kWh\s+([\d.,]+)-', texto)
    r['g2_kwh'] = br_float(g2_kwh[0]) if g2_kwh else 0

    # Total fatura
    m = re.search(r'TOTAL\s+([\d.,]+)\s+(?:OUT|NOV|DEZ|JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET)\d{2}', texto)
    r['total_fatura'] = br_float(m.group(1)) if m else 0

    # Base ICMS
    m = re.search(r'ICMS\s+([\d.,]+)\s+20,00', texto)
    r['base_icms'] = br_float(m.group(1)) if m else 0

    # Cliente
    m = re.search(r'NOME DO CLIENTE:\s*\n(.*?)(?:CNPJ|CÓDIGO)', texto, re.DOTALL)
    r['cliente'] = re.sub(r'\s+',' ', m.group(1)).strip().split('CÓDIGO')[0].strip() if m else ''

    r['tipo'] = 'cosern'
    return r

def extrair_origo(path):
    with pdfplumber.open(path) as pdf:
        texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    r = {}

    m = re.search(r'UC\s+(\d{6,8})', texto)
    r['uc'] = m.group(1) if m else ''

    meses = {'Jan':'01','Fev':'02','Mar':'03','Abr':'04','Mai':'05','Jun':'06',
             'Jul':'07','Ago':'08','Set':'09','Out':'10','Nov':'11','Dez':'12'}
    m = re.search(r'Ref\.\s+([A-Za-z]{3})/(\d{2})', texto)
    r['competencia'] = f"{meses.get(m.group(1).capitalize(),'00')}/20{m.group(2)}" if m else ''

    m = re.search(r'Comprador:\s*\n(.*?)\n', texto)
    r['cliente'] = m.group(1).strip() if m else ''

    m = re.search(r'Origo Energia - UC.*?R\$\s*([\d.,]+)', texto)
    r['origo_bruto'] = br_float(m.group(1)) if m else 0

    m = re.search(r'Pis Cofins.*?R\$\s*-?([\d.,]+)', texto)
    r['pis_cofins'] = br_float(m.group(1)) if m else 0

    m = re.search(r'Descontos? Comerciais.*?R\$\s*-?([\d.,]+)', texto)
    r['descontos_comerciais'] = br_float(m.group(1)) if m else 0

    m = re.search(r'Cobranças? Adicionais.*?R\$\s*([\d.,]+)', texto)
    r['cobrancas_adicionais'] = br_float(m.group(1)) if m else 0

    m = re.search(r'^Total\s+R\$\s*([\d.,]+)', texto, re.MULTILINE)
    r['total_origo'] = br_float(m.group(1)) if m else 0

    r['tipo'] = 'origo'
    return r

def detectar_tipo(path):
    with pdfplumber.open(path) as pdf:
        texto = (pdf.pages[0].extract_text() or "").upper()
    if 'ORIGO' in texto: return 'origo'
    if 'COSERN' in texto or 'NEOENERGIA' in texto or 'COMPANHIA ENERGÉTICA' in texto: return 'cosern'
    return 'desconhecido'

def processar_pdf(path):
    tipo = detectar_tipo(path)
    if tipo == 'cosern': return extrair_cosern(path)
    if tipo == 'origo':  return extrair_origo(path)
    return {'tipo': 'desconhecido', 'erro': 'Formato não reconhecido'}
