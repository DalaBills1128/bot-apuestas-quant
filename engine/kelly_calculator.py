import sys
import os

# Ajuste para importar la configuración global
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def calcular_stake_kelly(cuota_mercado, probabilidad_real_porcentaje, bankroll_actual):
    """
    Calcula el porcentaje y monto exacto de bankroll a apostar 
    usando el Criterio de Kelly Fraccionado.
    """
    p = probabilidad_real_porcentaje / 100.0  # Probabilidad real convertida a decimal (0 a 1)
    q = 1.0 - p
    b = cuota_mercado - 1.0  # Ganancia neta por unidad apostada

    if b <= 0:
        return 0.0, 0.0

    # Fórmula del Criterio de Kelly: f* = (p * b - q) / b
    kelly_fraction = (p * b - q) / b

    # Si el resultado es negativo o cero, significa que la casa paga menos de lo debido (No apostar)
    if kelly_fraction <= 0:
        return 0.0, 0.0

    # Aplicamos la fracción de seguridad configurada en el .env (ej. 1/4 de Kelly -> 0.25)
    stake_ajustado = kelly_fraction * Config.FRACCION_KELLY
    
    # Monto en dinero real a invertir basado en tu bankroll actual
    monto_inversion = bankroll_actual * stake_ajustado

    return round(stake_ajustado * 100, 2), round(monto_inversion, 2)