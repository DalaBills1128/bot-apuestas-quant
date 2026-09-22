import math

def _poisson_pmf(k, lam):
    """Calcula la probabilidad de Poisson de forma nativa para un valor k y media lambda."""
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def predecir_mercados_partido(xg_local, xg_vis):
    """
    Modelo de Poisson Avanzado en Python puro (sin dependencias pesadas de SciPy).
    Incluye factor de localía, penalización de visitante y cálculo de probabilidades 1X2 y Goles.
    """
    # Factores cuantitativos institucionales de rendimiento
    FACTOR_LOCALIA = 1.15  # El local rinde un 15% más en promedio
    FACTOR_VISITANTE = 0.90 # El visitante sufre una leve baja fuera de casa
    
    # Goles esperados ajustados (Lambdas de Poisson)
    lambda_local = max(0.2, xg_local * FACTOR_LOCALIA)
    lambda_vis = max(0.2, xg_vis * FACTOR_VISITANTE)
    
    # Simulación de matriz de goles (hasta 8 goles máximos por equipo)
    max_goles = 8
    
    poisson_local = [_poisson_pmf(i, lambda_local) for i in range(max_goles)]
    poisson_vis = [_poisson_pmf(j, lambda_vis) for j in range(max_goles)]
    
    prob_local = 0.0
    prob_empate = 0.0
    prob_visitante = 0.0
    prob_over_25 = 0.0
    prob_under_25 = 0.0
    
    for i in range(max_goles):
        for j in range(max_goles):
            p = poisson_local[i] * poisson_vis[j]
            
            # Mercados 1X2
            if i > j:
                prob_local += p
            elif i == j:
                prob_empate += p
            else:
                prob_visitante += p
                
            # Mercados de Goles (Over / Under 2.5)
            if (i + j) > 2.5:
                prob_over_25 += p
            else:
                prob_under_25 += p
    
    # Normalización para asegurar que las probabilidades del 1X2 sumen 100%
    total_1x2 = prob_local + prob_empate + prob_visitante
    if total_1x2 > 0:
        prob_local /= total_1x2
        prob_empate /= total_1x2
        prob_visitante /= total_1x2

    return {
        'probabilidad_local': round(prob_local * 100, 2),
        'probabilidad_empate': round(prob_empate * 100, 2),
        'probabilidad_visitante': round(prob_visitante * 100, 2),
        'probabilidad_over_25': round(prob_over_25 * 100, 2),
        'probabilidad_under_25': round(prob_under_25 * 100, 2),
        'lambda_local': round(lambda_local, 2),
        'lambda_vis': round(lambda_vis, 2)
    }