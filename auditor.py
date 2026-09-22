import os
import sys
import pandas as pd

# Asegurar que la ruta raíz esté disponible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.database import get_connection

def auditar_base_datos():
    conn = get_connection()
    if not conn:
        print("❌ No se pudo conectar a PostgreSQL.")
        return
        
    print("📊 --- AUDITORÍA DEL SISTEMA CUANTITATIVO --- 📊\n")
    
    try:
        # 1. Revisar la memoria del bot (Caché de Estadísticas)
        print("🧠 1. MEMORIA RAM (Últimos xG calculados con RapidAPI):")
        query_cache = "SELECT nombre_equipo, xg, ultima_actualizacion FROM cache_estadisticas ORDER BY ultima_actualizacion DESC LIMIT 10;"
        df_cache = pd.read_sql_query(query_cache, conn)
        
        if df_cache.empty:
            print("   -> El caché está vacío. El bot aún no ha descargado estadísticas.")
        else:
            print(df_cache.to_string(index=False))
            
        print("\n" + "="*70 + "\n")
        
        # 2. Revisar el libro contable (Registro de Apuestas)
        print("📖 2. BITÁCORA CONTABLE (Últimas apuestas de valor encontradas):")
        query_apuestas = "SELECT partido, casa_apuestas, seleccion, cuota_mercado, ev_porcentaje FROM registro_apuestas ORDER BY fecha_deteccion DESC LIMIT 10;"
        df_apuestas = pd.read_sql_query(query_apuestas, conn)
        
        if df_apuestas.empty:
            print("   -> La bitácora está limpia. No se han guardado apuestas aún.")
        else:
            # Formateamos el EV para que se vea como porcentaje
            df_apuestas['ev_porcentaje'] = df_apuestas['ev_porcentaje'].apply(lambda x: f"+{x}%")
            print(df_apuestas.to_string(index=False))
            
    except Exception as e:
        print(f"❌ Error al consultar PostgreSQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    auditar_base_datos()