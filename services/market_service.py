import yfinance as yf

def buscar_ativo(ticker: str):
    try:
        ticker = ticker.upper().strip()
        ativo = yf.Ticker(ticker)
        info = ativo.fast_info

        if info and 'last_price' in info:
            return{
                "preco" : round(info['last_price'], 2),
                "ticker" : ticker
            }
        historico = ativo.history(period = "1d")

        if not historico.empty:
            #close retorna o preço de fechamento
            ultimo_preco = historico['Close'].iloc[-1]
            return{
                "preco" : round(ultimo_preco, 2),
                "ticker" : ticker
            }
        return None
    except Exception:
        return None
    
#validar se o ticker existe e, se sim, retorna os dados
def validar_ticker(ticker: str):
    if ticker and len(ticker.strip()) >= 2:
        return True
    return False
