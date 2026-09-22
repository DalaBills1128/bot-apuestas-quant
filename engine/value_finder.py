import os
import sys

# Agregamos la ruta raíz al sistema para permitir futuras importaciones globales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importación directa ya que ambos archivos están en la misma carpeta (engine)
from .kelly_calculator import calcular_stake_kelly

def evaluar_apuesta(cuota_mercado, probabilidad_real_porcentaje, bankroll_actual):
    """
    Compara la cuota del mercado con la probabilidad real para detectar 
    si existe un Valor Esperado Positivo (EV+) y calcular cuánto invertir.
    """
    p = probabilidad_real_porcentaje / 100.0
    
    # Cuota justa matemática (Ej: 50% de probabilidad real -> Cuota justa 2.00)
    cuota_justa = 1.0 / p if p > 0 else 999.0

    # Valor Esperado (Expected Value - EV)
    # Fórmula: EV = (Probabilidad * Cuota) - 1
    ev = (p * cuota_mercado) - 1.0

    # Definimos si hay valor (Ejemplo: un EV positivo superior al 3%)
    tiene_valor = ev >= 0.03  

    stake_porcentaje, monto_inversion = 0.0, 0.0
    if tiene_valor:
        stake_porcentaje, monto_inversion = calcular_stake_kelly(
            cuota_mercado, probabilidad_real_porcentaje, bankroll_actual
        )

    return {
        "cuota_justa": round(cuota_justa, 2),
        "cuota_mercado": cuota_mercado,
        "ev_porcentaje": round(ev * 100, 2),
        "tiene_valor": tiene_valor,
        "stake_porcentaje": stake_porcentaje,
        "monto_inversion": monto_inversion
    }

# Prueba rápida del motor de valor
if __name__ == "__main__":
    cuota_ofrecida = 1.75
    probabilidad_modelo = 65.0
    bankroll_usuario = 100000  # $100,000 COP iniciales

    resultado = evaluar_apuesta(cuota_ofrecida, probabilidad_modelo, bankroll_usuario)
    
    print("🎯 Prueba del Motor de Valor y Kelly:")
    print(f"Cuota Justa Calculada: {resultado['cuota_justa']}")
    print(f"Cuota del Mercado: {resultado['cuota_mercado']}")
    print(f"Valor Esperado (EV): {resultado['ev_porcentaje']}%")
    print(f"¿Es una Apuesta de Valor?: {'SÍ 🚀' if resultado['tiene_valor'] else 'NO ❌'}")
    if resultado['tiene_valor']:
        print(f"Porcentaje de Bankroll sugerido: {resultado['stake_porcentaje']}%")
        print(f"Monto a invertir: ${resultado['monto_inversion']} COP")