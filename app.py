from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, tempfile, traceback
from parser import processar_pdf

app = Flask(__name__, static_folder='static')
CORS(app)

UPLOAD_FOLDER = tempfile.gettempdir()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/processar', methods=['POST'])
def processar():
    try:
        files = request.files.getlist('faturas')
        if not files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        resultados = []
        for f in files:
            if not f.filename.lower().endswith('.pdf'):
                continue
            tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            f.save(tmp.name)
            tmp.close()
            try:
                dados = processar_pdf(tmp.name)
                dados['arquivo'] = f.filename
                resultados.append(dados)
            except Exception as e:
                resultados.append({
                    'arquivo': f.filename,
                    'tipo': 'erro',
                    'erro': str(e)
                })
            finally:
                os.unlink(tmp.name)

        # Cruzar pares COSERN + ORIGO
        pares = cruzar_pares(resultados)
        return jsonify({'faturas': resultados, 'pares': pares})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def cruzar_pares(faturas):
    cosern = [f for f in faturas if f.get('tipo') == 'cosern']
    origo  = [f for f in faturas if f.get('tipo') == 'origo']
    pares  = []
    used_c = set()
    used_o = set()

    for oi, o in enumerate(origo):
        for ci, c in enumerate(cosern):
            if ci in used_c: continue
            uc_match   = c.get('uc') and o.get('uc') and c['uc'] == o['uc']
            comp_match = c.get('competencia') == o.get('competencia')
            if uc_match or comp_match:
                pares.append(calcular_auditoria(c, o))
                used_c.add(ci)
                used_o.add(oi)
                break
        else:
            if oi not in used_o:
                pares.append({'sem_cosern': True, 'origo': o,
                              'competencia': o.get('competencia',''),
                              'instalacao': o.get('cliente','') + ' UC ' + o.get('uc','')})

    for ci, c in enumerate(cosern):
        if ci not in used_c:
            pares.append({'sem_origo': True, 'cosern': c,
                          'competencia': c.get('competencia',''),
                          'instalacao': c.get('cliente','') + ' UC ' + c.get('uc','')})

    return pares

def calcular_auditoria(c, o, desc_esp=0.20):
    ref_total    = (c.get('tusd',0) + c.get('te',0) + c.get('bandeira',0) +
                    c.get('iluminacao_publica',0) + c.get('parcelas',0))
    g1_credito   = c.get('g1_credito', 0)
    g2_credito   = c.get('g2_credito', 0)
    # Base para desconto Origo = ref total SEM G2 (G2 é geração própria, não conta)
    ref_origo    = ref_total - g2_credito
    total_cosern = c.get('total_fatura', 0)
    total_origo  = o.get('total_origo', 0)
    total_pago   = total_cosern + total_origo
    economia     = ref_origo - total_pago
    desc_real    = (economia / ref_origo * 100) if ref_origo else 0
    diff         = desc_real - (desc_esp * 100)
    status       = 'conforme' if diff >= -1 else 'atencao' if diff >= -5 else 'nao_conforme'

    cliente = c.get('cliente','') or o.get('cliente','')
    torre   = c.get('torre','')
    nome    = f"{cliente} — Torre {torre}" if torre else cliente

    return {
        'instalacao':    nome,
        'uc':            c.get('uc','') or o.get('uc',''),
        'torre':         torre,
        'competencia':   c.get('competencia','') or o.get('competencia',''),
        'consumo_kwh':   c.get('consumo_kwh', 0),
        'ref_total':     round(ref_total, 2),
        'ref_origo':     round(ref_origo, 2),
        'tusd':          c.get('tusd', 0),
        'te':            c.get('te', 0),
        'bandeira':      c.get('bandeira', 0),
        'ip':            c.get('iluminacao_publica', 0),
        'parcelas':      c.get('parcelas', 0),
        'g1_credito':    round(g1_credito, 2),
        'g1_kwh':        c.get('g1_kwh', 0),
        'g2_credito':    round(g2_credito, 2),
        'g2_kwh':        c.get('g2_kwh', 0),
        'total_cosern':  round(total_cosern, 2),
        'origo_bruto':   o.get('origo_bruto', 0),
        'pis_cofins':    o.get('pis_cofins', 0),
        'desc_comerciais': o.get('descontos_comerciais', 0),
        'cobrancas_adic':  o.get('cobrancas_adicionais', 0),
        'total_origo':   round(total_origo, 2),
        'total_pago':    round(total_pago, 2),
        'economia':      round(economia, 2),
        'desc_real':     round(desc_real, 2),
        'desc_esp':      desc_esp * 100,
        'base_icms':     c.get('base_icms', 0),
        'status':        status,
        'arquivo_cosern': c.get('arquivo',''),
        'arquivo_origo':  o.get('arquivo',''),
    }

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
