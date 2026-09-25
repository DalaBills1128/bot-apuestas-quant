import os
import time
import pandas as pd
from supabase import create_client, Client
from utils.fuzzy_matcher import encontrar_mejor_coincidencia

from config import Config
from models.dixon_coles import DixonColesModel
from models.kelly import AdministradorRiesgo
from alerts.telegram_bot import NotificadorTelegram
from extractors.odds_fetcher import OddsFetcher
from engine.ai_analyst import AnalistaIA  # 🧠 Analista Híbrido

supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
ARCHIVO_MEMORIA = "data/alertas_enviadas.log"

def cargar_alertas_enviadas():
    if not os.path.exists(ARCHIVO_MEMORIA):
        return set()
    with open(ARCHIVO_MEMORIA, "r") as f:
        return set(f.read().splitlines())

def registrar_alerta(match_id):
    # Usamos os.makedirs para asegurar que la carpeta data/ exista
    os.makedirs(os.path.dirname(ARCHIVO_MEMORIA), exist_ok=True)
    with open(ARCHIVO_MEMORIA, "a") as f:
        f.write(f"{match_id}\n")

def obtener_racha(equipo, df):
    partidos = df[(df['equipo_local'] == equipo) | (df['equipo_visitante'] == equipo)]
    
    if partidos.empty:
        equipos_conocidos = pd.concat([df['equipo_local'], df['equipo_visitante']]).unique().tolist()
        # Umbral estricto (80%) para evitar cruces erróneos entre ligas
        equipo_corregido = encontrar_mejor_coincidencia(equipo, equipos_conocidos, umbral=0.8)
        
        if equipo_corregido:
            partidos = df[(df['equipo_local'] == equipo_corregido) | (df['equipo_visitante'] == equipo_corregido)]
            equipo = equipo_corregido
        else:
            # Mensaje claro cuando el equipo no está en el esquema SQL
            return "Sin datos cualitativos recientes."
            
    ultimos_5 = partidos.sort_values(by='fecha', ascending=False).head(5)
    tendencia = []
    
    for _, row in ultimos_5.iterrows():
        es_local = (row['equipo_local'] == equipo)
        xg_propio = row['xg_local'] if es_local else row['xg_visitante']
        xg_rival = row['xg_visitante'] if es_local else row['xg_local']
        
        margen = xg_propio - xg_rival
        if margen > 0.2: 
            tendencia.append("Dominó")
        elif margen < -0.2: 
            tendencia.append("Dominado")
        else: 
            tendencia.append("Igualado")
            
    return f"Últimos 5 juegos (xG): {', '.join(tendencia)}"

def ejecutar_orquestador_real():
    print("🚀 Iniciando Bot Cuantitativo Híbrido (Matemática + IA)...")

    response = supabase.table('historial_xg').select('*').execute()
    if not response.data:
        print("❌ No hay datos en Supabase para entrenar el modelo.")
        return

    # Preparación limpia del DataFrame
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

    fetcher = OddsFetcher()
    partidos_evaluar = fetcher.obtener_cuotas_actuales()

    riesgo = AdministradorRiesgo()
    telegram = NotificadorTelegram()
    ia = AnalistaIA()
    alertas_previas = cargar_alertas_enviadas()
    
    apuestas_por_liga = {}
    apuestas_encontradas = 0
    
    if not partidos_evaluar:
        print("⚠️ No se encontraron partidos programados para evaluar hoy.")
        return

    for partido in partidos_evaluar:
        # 🎯 1. Filtro Quirúrgico de Casas de Apuestas
        casa_api = partido.get('casa', '').lower()
        casas_colombianas = []
        
        for clave, nombres_locales in Config.CASAS_ESPEJO.items():
            if clave in casa_api:
                casas_colombianas.extend(nombres_locales)
        
        # Saltamos inmediatamente si no es una casa VIP
        if not casas_colombianas:
            continue

        nombres_casas_mostrar = " / ".join(set(casas_colombianas))
        match_id_base = f"{partido['local']}_vs_{partido['visitante']}"
        
        try:
            preds = modelo.predecir_partido(partido['local'], partido['visitante'])
            mercados_a_evaluar = [
                {"tipo": "Local", "nombre_apuesta": f"Gana {partido['local']}", "prob": preds['prob_local'], "cuota": partido.get('cuota_local', 0.0), "id_mercado": f"{match_id_base}_LOCAL"},
                {"tipo": "Empate", "nombre_apuesta": "Empate", "prob": preds['prob_empate'], "cuota": partido.get('cuota_empate', 0.0), "id_mercado": f"{match_id_base}_EMPATE"},
                {"tipo": "Visitante", "nombre_apuesta": f"Gana {partido['visitante']}", "prob": preds['prob_visitante'], "cuota": partido.get('cuota_visitante', 0.0), "id_mercado": f"{match_id_base}_VISITANTE"}
            ]

            for mercado in mercados_a_evaluar:
                if mercado['cuota'] <= 0:
                    continue

                analisis = riesgo.analizar_apuesta(mercado['prob'], mercado['cuota'])

                # 🛑 Filtro 1: Modo Espía Kelly
                if not analisis.get('apuesta_recomendada'):
                    print(f"❌ Descartado: {mercado['nombre_apuesta']} (Cuota: {mercado['cuota']}) - No rentable (Esperanza Negativa)")
                    continue

                edge_porcentaje = analisis.get('edge', 0) * 100

                # 🛑 Filtro 2: Modo Espía Edge
                if edge_porcentaje < Config.MIN_EDGE_PERCENTAGE:
                    print(f"📉 Descartado: {mercado['nombre_apuesta']} - Edge ({edge_porcentaje:.2f}%) no supera el límite configurado.")
                    continue

                # ✅ Pasó todos los filtros VIP
                apuestas_encontradas += 1
                liga = partido.get('liga_nombre', 'Ligas VIP')
                
                if liga not in apuestas_por_liga:
                    apuestas_por_liga[liga] = []
                
                # Extracción de rachas usando el histórico
                racha_local = obtener_racha(partido['local'], df_modelo)
                racha_visitante = obtener_racha(partido['visitante'], df_modelo)

                opinion_ia = ia.evaluar_apuesta(
                    mercado['nombre_apuesta'], 
                    mercado['cuota'], 
                    edge_porcentaje, 
                    racha_local, 
                    racha_visitante
                )
                
                prob_real_porcentaje = mercado['prob'] * 100
                stake_porcentaje = analisis.get('porcentaje_bankroll', 0) * 100

                detalle_partido = (
                    f"⚽ *{partido['local']} vs {partido['visitante']}*\n"
                    f"📈 Apuesta: {mercado['nombre_apuesta']}\n"
                    f"🏛️ Casa (Colombia): *{nombres_casas_mostrar}*\n"
                    f"📊 Prob. Real: {prob_real_porcentaje:.2f}% | Cuota: {mercado['cuota']}\n"
                    f"🔥 Edge: {edge_porcentaje:.2f}%\n"
                    f"💰 Stake: {stake_porcentaje:.2f}% del Bankroll\n"
                    f"🤖 *Veredicto IA:*\n{opinion_ia}\n"
                    f"───────────────"
                )
                
                apuestas_por_liga[liga].append(detalle_partido)
                registrar_alerta(mercado['id_mercado'])
                
        except Exception as e:
            print(f"⚠️ Error procesando {partido.get('local')} vs {partido.get('visitante')}: {e}")
            continue

    # Envío de alertas finales
    if apuestas_por_liga:
        for liga, mensajes_partidos in apuestas_por_liga.items():
            mensaje_liga = f"🏆 *Oportunidades Filtradas ➔ {liga}* 🏆\n\n" + "\n".join(mensajes_partidos)
            telegram.enviar_alerta(mensaje_liga)
            time.sleep(2)

    print(f"🏁 Análisis completado. Alertas VIP enviadas: {apuestas_encontradas}")

if __name__ == "__main__":
    ejecutar_orquestador_real()