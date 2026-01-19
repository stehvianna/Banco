def calcular_score(saldo_cc: float) -> int:
    #saldo zerado/negativo: score zerado
    #score varia de 0 a 1000

    try:
        saldo = float(saldo_cc)

        if saldo <= 0:
            score_credito = 0
        elif saldo > 10000:
            score_credito = 1000
        elif saldo > 0 or saldo <= 10000:
            score_credito = saldo * 0.1
    except Exception as e:
        raise ValueError(f'Erro ao calcular score: {e}')
    return int(score_credito)