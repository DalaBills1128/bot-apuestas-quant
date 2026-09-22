import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection

# Caché en memoria para velocidad instantánea
_POWER_RATINGS_CACHE = None

def _cargar_cache_power_ratings():
    global _POWER_RATINGS_CACHE
    if _POWER_RATINGS_CACHE is not None:
        return _POWER_RATINGS_CACHE

    _POWER_RATINGS_CACHE = {}
    conn = get_connection()
    if not conn:
        return _POWER_RATINGS_CACHE
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT nombre_equipo, xg_base FROM power_ratings;")
            rows = cur.fetchall()
            for row in rows:
                if row[0] and row[1] is not None:
                    _POWER_RATINGS_CACHE[row[0].strip().lower()] = float(row[1])
    except Exception as e:
        print(f"❌ Error al cargar caché de power_ratings: {e}")
    finally:
        conn.close()
    
    return _POWER_RATINGS_CACHE

def obtener_xg_equipo(nombre_equipo, liga_id=None, temporada=None):
    """
    Obtiene el xG del equipo. Si no existe en Supabase, lo auto-registra 
    automáticamente para evitar errores manuales.
    """
    if not nombre_equipo:
        return 1.35

    cache = _cargar_cache_power_ratings()
    nombre_limpio = nombre_equipo.strip().lower()

    # 1. Búsqueda exacta
    if nombre_limpio in cache:
        return cache[nombre_limpio]

    # 2. Búsqueda parcial
    for eq_db, xg in cache.items():
        if eq_db in nombre_limpio or nombre_limpio in eq_db:
            return xg

    # 3. Búsqueda por primera palabra clave
    palabra_principal = nombre_limpio.split()[0]
    if len(palabra_principal) > 3:
        for eq_db, xg in cache.items():
            if palabra_principal in eq_db:
                return xg

    # --- AUTO-INSERCIÓN INTELIGENTE ---
    # Si el equipo no está en la base de datos, lo creamos automáticamente
    default_xg = 1.35
    print(f"✨ Equipo nuevo detectado y auto-registrado en Supabase: {nombre_equipo}")
    
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO power_ratings (nombre_equipo, xg_base) VALUES (%s, %s) ON CONFLICT (nombre_equipo) DO NOTHING;",
                    (nombre_equipo, default_xg)
                )
                conn.commit()
            # Guardarlo en caché local para que no vuelva a consultar en este ciclo
            cache[nombre_limpio] = default_xg
        except Exception as e:
            print(f"❌ Error al auto-registrar {nombre_equipo}: {e}")
        finally:
            conn.close()

    return default_xg