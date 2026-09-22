import os
import psycopg2
from config import Config

def get_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL en Supabase."""
    try:
        # Se conecta directamente usando la dirección URI de Supabase
        conn = psycopg2.connect(Config.DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos en la nube: {e}")
        return None

def init_db():
    """Inicializa la base de datos creando las tablas necesarias si no existen."""
    conn = get_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cur:
            # 1. Tabla de Caché de xG para Estadísticas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cache_estadisticas (
                    nombre_equipo VARCHAR(150) PRIMARY KEY,
                    xg NUMERIC(5, 2),
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 2. Tabla de Bitácora Contable de Apuestas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS registro_apuestas (
                    id_registro SERIAL PRIMARY KEY,
                    partido VARCHAR(150),
                    casa_apuestas VARCHAR(100),
                    seleccion VARCHAR(100),
                    cuota_mercado NUMERIC(5, 2),
                    ev_porcentaje NUMERIC(6, 2),
                    stake_recomendado NUMERIC(6, 2),
                    fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Tabla de Power Ratings (Calibración de Poder)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS power_ratings (
                    nombre_equipo VARCHAR(150) PRIMARY KEY,
                    xg_base NUMERIC(5, 2) NOT NULL,
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
        conn.commit()
        print("✅ Base de datos inicializada. Tablas creadas correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar tablas: {e}")
    finally:
        conn.close()

def guardar_xg_cache(nombre_equipo, xg):
    """Guarda o actualiza el xG en la caché de PostgreSQL."""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cache_estadisticas (nombre_equipo, xg, ultima_actualizacion)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (nombre_equipo) 
                DO UPDATE SET xg = EXCLUDED.xg, ultima_actualizacion = CURRENT_TIMESTAMP;
            """, (nombre_equipo, xg))
        conn.commit()
    except Exception as e:
        print(f"❌ Error al guardar caché xG: {e}")
    finally:
        conn.close()

def obtener_xg_cache(nombre_equipo):
    """Consulta la caché de xG en PostgreSQL."""
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT xg FROM cache_estadisticas WHERE nombre_equipo ILIKE %s;", (nombre_equipo,))
            res = cur.fetchone()
            if res:
                try:
                    return float(res[0])
                except (IndexError, TypeError, ValueError):
                    pass
        return None
    except Exception:
        return None
    finally:
        conn.close()

def guardar_registro_apuesta(partido, casa, seleccion, cuota, ev, stake):
    """Guarda en la bitácora contable cada apuesta de valor encontrada."""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO registro_apuestas 
                (partido, casa_apuestas, seleccion, cuota_mercado, ev_porcentaje, stake_recomendado)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (partido, casa, seleccion, cuota, ev, stake))
        conn.commit()
    except Exception as e:
        print(f"❌ Error al guardar en la bitácora: {e}")
    finally:
        conn.close()

def obtener_power_rating_db(nombre_equipo):
    """
    Busca el xG base en la tabla power_ratings con manejo defensivo absoluto de tuplas.
    """
    conn = get_connection()
    if not conn: return 1.35
    
    try:
        with conn.cursor() as cur:
            # 1. Verificar si la tabla tiene datos de forma ultra-segura
            count = 0
            try:
                cur.execute("SELECT COUNT(*) FROM power_ratings;")
                resultado_count = cur.fetchone()
                if resultado_count:
                    count = resultado_count[0]
            except Exception:
                count = 0
            
            if count == 0:
                seed_data = [
                    # 🇬🇧 Premier League
                    ("Manchester City", 2.45), ("Arsenal", 2.20), ("Liverpool", 2.25),
                    ("Chelsea", 1.75), ("Tottenham Hotspur", 1.85), ("Manchester United", 1.65),
                    ("Aston Villa", 1.60), ("Newcastle United", 1.70), ("Brighton", 1.55),
                    ("West Ham", 1.40), ("Crystal Palace", 1.35), ("Brentford", 1.40),
                    ("Everton", 1.20), ("Bournemouth", 1.35), ("Sunderland", 1.25),
                    # 🇪🇸 La Liga
                    ("Real Madrid", 2.35), ("Barcelona", 2.30), ("Atletico Madrid", 1.80),
                    ("Real Sociedad", 1.55), ("Athletic Club", 1.60), ("Villarreal", 1.50),
                    ("Real Betis", 1.45), ("Getafe", 1.15), ("Celta Vigo", 1.30),
                    ("Alavés", 1.10), ("Rayo Vallecano", 1.25), ("Espanyol", 1.20),
                    ("Valencia", 1.30), ("Osasuna", 1.20), ("Málaga", 1.15),
                    # 🇮🇹 Serie A
                    ("Inter", 2.20), ("Juventus", 1.75), ("AC Milan", 1.85),
                    ("Napoli", 1.80), ("Atalanta BC", 1.90), ("AS Roma", 1.65),
                    ("Bologna", 1.50), ("Lazio", 1.60), ("Fiorentina", 1.55),
                    ("Torino", 1.30), ("Udinese", 1.25), ("Lecce", 1.15),
                    ("Sassuolo", 1.20), ("Como", 1.25), ("Venezia", 1.10), ("Frosinone", 1.15),
                    # 🇩🇪 Bundesliga
                    ("Bayern Munich", 2.50), ("Bayer Leverkusen", 2.25), ("Borussia Dortmund", 1.95),
                    ("RB Leipzig", 1.85), ("Stuttgart", 1.80), ("Eintracht Frankfurt", 1.60),
                    ("Wolfsburg", 1.35), ("Augsburg", 1.25), ("Mainz", 1.20),
                    ("Werder Bremen", 1.30), ("Union Berlin", 1.25),
                    # 🇦🇷 Argentina y 🇧🇷 Brasil / 🇨🇴 Colombia (Guardados en Power Ratings por si deseas usarlos localmente)
                    ("River Plate", 1.95), ("Boca Juniors", 1.85), ("Racing Club", 1.70),
                    ("Independiente", 1.50), ("San Lorenzo", 1.45), ("Estudiantes", 1.55),
                    ("Flamengo", 2.10), ("Palmeiras", 2.05), ("Atlético Mineiro", 1.80),
                    ("Fluminense", 1.75), ("São Paulo", 1.70), ("Botafogo", 1.85),
                    ("Millonarios", 1.60), ("Junior", 1.55), ("Atlético Nacional", 1.70),
                    ("Independiente Medellín", 1.50), ("América de Cali", 1.55), ("Santa Fe", 1.45),
                    ("Deportivo Cali", 1.40), ("Deportes Tolima", 1.55), ("Once Caldas", 1.40),
                    ("Águilas Doradas", 1.35), ("La Equidad", 1.35)
                ]
                cur.executemany("""
                    INSERT INTO power_ratings (nombre_equipo, xg_base) 
                    VALUES (%s, %s) ON CONFLICT (nombre_equipo) DO NOTHING;
                """, seed_data)
                conn.commit()

            # 2. Búsqueda exacta segura
            cur.execute("SELECT xg_base FROM power_ratings WHERE nombre_equipo ILIKE %s;", (nombre_equipo,))
            res = cur.fetchone()
            if res:
                try:
                    val = res[0]
                    if val is not None:
                        return float(val)
                except (IndexError, TypeError, ValueError):
                    pass
                
            # 3. Búsqueda parcial segura
            cur.execute("SELECT xg_base FROM power_ratings WHERE %s ILIKE '%' || nombre_equipo || '%';", (nombre_equipo,))
            res = cur.fetchone()
            if res:
                try:
                    val = res[0]
                    if val is not None:
                        return float(val)
                except (IndexError, TypeError, ValueError):
                    pass
                
            return 1.35
            
    except Exception:
        # Silenciamos cualquier excepción menor devolviendo el xG por defecto
        return 1.35
    finally:
        conn.close()

def ya_fue_alertado(partido, seleccion):
    """Verifica si ya se envió una alerta para este partido y selección en las últimas 12 horas."""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM registro_apuestas 
                WHERE partido = %s AND seleccion = %s 
                AND fecha_deteccion >= NOW() - INTERVAL '12 HOURS';
            """, (partido, seleccion))
            res = cur.fetchone()
            if res and res[0] > 0:
                return True
            return False
    except Exception:
        return False
    finally:
        conn.close()