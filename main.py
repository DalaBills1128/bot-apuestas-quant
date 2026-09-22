import os
import time
import pandas as pd
from supabase import create_client, Client

# Importar configuración global
from config import Config

# Importar nuestros módulos Quant
from models.dixon_coles import DixonColesModel
from models.kelly import AdministradorRiesgo
from alerts.telegram_bot import NotificadorTelegram
from extractors.odds_fetcher import OddsFetcher

supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Sistema de memoria local para no repetir alertas
ARCHIVO_MEMORIA = "data/alertas_enviadas.log"

def cargar_alertas_enviadas():
    if not os.path.exists(ARCHIVO_MEMORIA):
        return set()
    with open(ARCHIVO_MEMORIA, "r") as f:
        return set(f.read().splitlines())

def registrar_alerta(match_id):
    with open(ARCHIVO_MEMORIA, "a") as f:
        f.write(f"{match_id}\n")

def ejecutar_orquestador_real():
    print("🚀 Iniciando Bot Cuantitativo con Datos Reales...")

    print("📥 Descargando historial de xG desde Supabase...")
    response = supabase.table('historial_xg').select('*').execute()
    
    if not response.data:
        print("❌ No hay datos en Supabase para entrenar el modelo.")
        return

    df = pd.DataFrame(response.data)
    
    df_modelo = pd.DataFrame({
        'fecha': df['fecha'],
        'equipo_local': df.apply(lambda x: x['equipo'] if x['localia'] == 'Local' else x['rival'], axis=1),
        'equipo_visitante': df.apply(lambda x: x['rival'] if x['localia'] == 'Local' else x['equipo'], axis=1),
        'xg_local': df.apply(lambda x: x['xg_favor'] if x['localia'] == 'Local' else x['xg_contra'], axis=1),
        'xg_visitante': df.apply(lambda x: x['xg_contra'] if x['localia'] == 'Local' else x['xg_favor'], axis=1)
    }).drop_duplicates(subset=['fecha', 'equipo_local', 'equipo_visitante'])

    modelo = DixonColesModel(xi=0.0065)
    modelo.entrenar(df_modelo)

    # 3. Obtener partidos y cuotas reales de The Odds API
    fetcher = OddsFetcher()
    partidos_evaluar = fetcher.obtener_cuotas_actuales()

    riesgo = AdministradorRiesgo()
    telegram = NotificadorTelegram()
    alertas_previas = cargar_alertas_enviadas() if 'cargar_alertas_enviadas' in globals() else set()

    print(f"🔍 Analizando valor matemático en {len(partidos_evaluar)} partidos...")
    
    # Diccionario para agrupar las apuestas por liga
    apuestas_por_liga = {}
    apuestas_encontradas = 0
    
    if partidos_evaluar:
        for partido in partidos_evaluar:
            match_id = f"{partido['local']}_vs_{partido['visitante']}"
            
            if match_id in alertas_previas:
                continue

            try:
                if partido['cuota_local'] == 0 or partido['cuota_visitante'] == 0:
                    continue

                preds = modelo.predecir_partido(partido['local'], partido['visitante'])
                analisis = riesgo.analizar_apuesta(preds['prob_local'], partido['cuota_local'])
                
                if analisis['apuesta_recomendada']:
                    apuestas_encontradas += 1
                    liga = partido.get('liga_nombre', 'Oportunidades Destacadas') # Agrupa por liga
                    
                    if liga not in apuestas_por_liga:
                        apuestas_por_liga[liga] = []
                    
                    edge_porcentaje = analisis['edge'] * 100
                    stake_porcentaje = analisis['porcentaje_bankroll'] * 100
                    
                    # Construir la línea del partido con el formato exacto que te gusta
                    prob_real_porcentaje = preds['prob_local'] * 100
                    edge_porcentaje = analisis['edge'] * 100
                    stake_porcentaje = analisis['porcentaje_bankroll'] * 100

                    # Plantilla exacta basada en tu nueva imagen de referencia
                    detalle_partido = (
                        f"⚽ *{partido['local']} vs {partido['visitante']}*\n"
                        f"📈 Apuesta: Gana {partido['local']}\n"
                        f"📊 Probabilidad Real: {prob_real_porcentaje:.2f}%\n"
                        f"🏛️ Cuota Real Mercado: {partido['cuota_local']}\n"
                        f"🔥 Edge (Ventaja): {edge_porcentaje:.2f}%\n"
                        f"💰 Stake: {stake_porcentaje:.2f}% del Bankroll (${analisis['monto_fiat']} COP)\n"
                        f"───────────────"
                    )
                    
                    apuestas_por_liga[liga].append(detalle_partido)
                    
                    # Registrar en memoria para no repetirlo
                    if 'registrar_alerta' in globals():
                        registrar_alerta(match_id)
                else:
                    print(f"➖ {partido['local']} vs {partido['visitante']}: Sin valor suficiente ({analisis['motivo']})")
                    
            except Exception:
                continue

    # Enviar mensajes agrupados por liga
    if apuestas_por_liga:
        for liga, mensajes_partidos in apuestas_por_liga.items():
            mensaje_liga = f"🏆 *Oportunidades en ➔ {liga}* 🏆\n\n" + "\n".join(mensajes_partidos)
            telegram.enviar_alerta(mensaje_liga)
            time.sleep(2) # Pequeña pausa de seguridad entre mensajes de distintas ligas

    print(f"🏁 Análisis completado. Nuevas alertas enviadas: {apuestas_encontradas}")

    # Reporte de control matutino obligatorio si no hubo nada
    fecha_hoy = pd.Timestamp.now().strftime('%Y-%m-%d')
    if apuestas_encontradas == 0:
        mensaje_vacio = (
            f"🤖 *Reporte Diario - Bot Quant*\n\n"
            f"📅 Fecha: {fecha_hoy}\n"
            f"🔍 Partidos analizados: {len(partidos_evaluar)}\n"
            f"➖ Estado: Monitoreo activo. No hay nuevas oportunidades con el Edge requerido (>10%) para hoy."
        )
        telegram.enviar_alerta(mensaje_vacio)


if __name__ == "__main__":
    ejecutar_orquestador_real()