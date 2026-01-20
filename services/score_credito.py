def calcular_score(saldo_cc: float) -> int:
    #saldo zerado/negativo: score zerado
    #score varia de 0 a 1000

    try:
        saldo = float(saldo_cc)

        if saldo <= 0:
            return 0
        elif saldo > 10000:
            return 1000
        return int(saldo * 0.1)
    except Exception as e:
        raise ValueError(f'Erro ao calcular score: {e}')
    