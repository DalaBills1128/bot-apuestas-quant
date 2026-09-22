import time
from datetime import datetime, timedelta
import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import ejecutar_orquestador_real 

ARCHIVO_MEMORIA = "data/alertas_enviadas.log"

def limpiar_memoria_diaria():
    if os.path.exists(ARCHIVO_MEMORIA):
        os.remove(ARCHIVO_MEMORIA)
        print("🧹 Memoria de alertas limpia para los partidos de hoy.")

def dormir_hasta_la_manana(hora_despertar=7):
    """Calcula los segundos hasta las 7:00 AM y duerme el script"""
    ahora = datetime.now()
    futuro = ahora.replace(hour=hora_despertar, minute=0, second=0, microsecond=0)
    
    if ahora.hour >= hora_despertar:
        futuro += timedelta(days=1) # Si ya pasaron las 7 AM, calcular para mañana
        
    segundos_espera = (futuro - ahora).total_seconds()
    horas_espera = int(segundos_espera / 3600)
    print(f"\n💤 Jornada finalizada. El bot despertará a las {hora_despertar}:00 AM (en {horas_espera} horas)...")
    time.sleep(segundos_espera)

def iniciar_ciclo_diario():
    print("🤖 Bot Quant: Modo Matutino Activado (Ejecución 7:00 AM)")
    
    ultimo_dia_sincronizado = None

    while True:
        ahora = datetime.now()
        dia_actual = ahora.strftime("%Y-%m-%d")
        
        try:
            if dia_actual != ultimo_dia_sincronizado:
                print(f"========================================\n🌞 [ {dia_actual} ] Analizando el mercado del día...\n========================================")
                print("📅 Descargando histórico faltante (API-Football)...")
                subprocess.run([sys.executable, "-m", "extractors.xg_extractor"], check=True)
                limpiar_memoria_diaria()
                ultimo_dia_sincronizado = dia_actual

            ejecutar_orquestador_real() 
            
            # Una vez enviado el reporte, dormimos hasta mañana
            dormir_hasta_la_manana(7)
            
        except Exception as e:
            print(f"❌ Error crítico: {e}")
            time.sleep(300) # Si falla la red, intenta de nuevo en 5 minutos

if __name__ == "__main__":
    try:
        iniciar_ciclo_diario()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido.")