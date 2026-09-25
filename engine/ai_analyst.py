from groq import Groq
from config import Config

class AnalistaIA:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        # Modelo actualizado a la versión vigente y ultrarrápida
        self.modelo = "qwen/qwen3.8-27b" 

    def evaluar_apuesta(self, apuesta_recomendada, cuota, edge, racha_equipo, racha_rival):
        if not Config.GROQ_API_KEY:
            return "⚪ IA Desactivada (Falta API Key)"

        prompt = (
            f"Actúa como un analista de apuestas deportivas. "
            f"El modelo recomienda: '{apuesta_recomendada}' (Cuota: {cuota}, Edge: {edge:.2f}%). "
            f"Contexto xG Local: {racha_equipo}. Contexto xG Visitante: {racha_rival}. "
            f"REGLAS ESTRICTAS: "
            f"1. Si el contexto dice 'Sin datos cualitativos recientes', NO INVENTES ANÁLISIS. Tu única respuesta debe ser exactamente esta: "
            f"'⚪ Análisis IA en Pausa: Partido sin historial en la base de datos. Operación respaldada únicamente por la ventaja matemática del {edge:.2f}%.' "
            f"2. Si SÍ hay datos de xG (Dominó, Igualado, Dominado), analiza brevemente si el rendimiento real respalda la cuota (🟢), la pone en duda (🟡) o la contradice (🔴)."
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.modelo,
                temperature=0.3, 
                max_tokens=150
            )
            respuesta = chat_completion.choices[0].message.content.strip()
            # Escudo protector: quitamos caracteres que rompen el formato de Telegram
            respuesta_limpia = respuesta.replace("*", "").replace("_", " ").replace("`", "")
            return respuesta_limpia
            
        except Exception as e:
            # Si hay error, lo limpiamos para que no colapse Telegram
            error_str = str(e).replace("*", "").replace("_", " ").replace("{", "").replace("}", "")
            return f"⚠️ Error IA: {error_str}"