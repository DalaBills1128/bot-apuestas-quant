import os
from dotenv import load_dotenv

class AdministradorRiesgo:
    def __init__(self):
        load_dotenv()
        # Cargar parámetros financieros desde el .env
        self.bankroll = float(os.getenv("BANKROLL_INICIAL", 100000))
        self.tolerancia_valor = float(os.getenv("TOLERANCIA_CUOTA", 0.10))
        self.fraccion_kelly = float(os.getenv("FRACCION_KELLY", 0.25))

    def analizar_apuesta(self, probabilidad_real, cuota_casa):
        """
        Calcula el Valor Esperado (EV) y el porcentaje de bankroll a invertir
        usando el Criterio de Kelly Fraccional.
        """
        # 1. Calcular el Valor Esperado (Edge / Ventaja)
        # Un EV > 0 significa que la apuesta tiene valor matemático a largo plazo.
        valor_esperado = (probabilidad_real * cuota_casa) - 1

        # Si la ventaja no supera nuestro margen mínimo de seguridad, rechazamos la apuesta
        if valor_esperado < self.tolerancia_valor:
            return {
                "apuesta_recomendada": False,
                "motivo": f"Edge insuficiente ({valor_esperado:.2%}). Mínimo requerido: {self.tolerancia_valor:.2%}",
                "porcentaje_bankroll": 0,
                "monto_fiat": 0
            }

        # 2. Calcular el Kelly Óptimo
        # Fórmula: (probabilidad * cuota - 1) / (cuota - 1)
        kelly_completo = valor_esperado / (cuota_casa - 1)

        # 3. Aplicar Kelly Fraccional para mitigar la volatilidad
        kelly_fraccional = kelly_completo * self.fraccion_kelly

        # Limitamos la apuesta máxima por seguridad (ej. nunca apostar más del 5% en un solo evento)
        porcentaje_final = min(kelly_fraccional, 0.05)
        monto_fiat = self.bankroll * porcentaje_final

        return {
            "apuesta_recomendada": True,
            "edge": round(valor_esperado, 4),
            "porcentaje_bankroll": round(porcentaje_final, 4),
            "monto_fiat": round(monto_fiat, 2)
        }

# Prueba rápida
if __name__ == "__main__":
    riesgo = AdministradorRiesgo()
    # Ejemplo: El modelo dice que hay 55% de prob de victoria, la casa paga 2.10
    resultado = riesgo.analizar_apuesta(0.55, 2.10)
    print(resultado)