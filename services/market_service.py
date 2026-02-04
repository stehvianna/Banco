import yfinance as yf

def buscar_ativo(ticker: str):
    try:
        ativo = yf.Ticker(ticker)
        dados = ativo.fast_info

        if dados is None or 'last_price' not in dados:
            return None
        return {
            "preco" : dados['last_price'],
            "moeda" : dados['currency'],
            "ticker" : ticker
        }
    except Exception:
        return None
    
def validar_ticker(ticker: str):
    info = buscar_ativo(ticker)
    if not info:
        raise Exception('Impossível encontrar dados do ativo informado.')
    else:
        return info