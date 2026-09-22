def sincronizar_historico(self):
        print("🧠 Iniciando sincronización inteligente de histórico (xG)...")
        
        # ID 39: Premier League | ID 239: Colombia Primera A
        ligas_a_sincronizar = [39, 239]
        
        db_response = supabase.table("historial_xg").select("fecha, equipo").execute()
        registros_existentes = { f"{r['fecha']}_{r['equipo']}" for r in db_response.data }
        
        peticiones_usadas = 0
        nuevos_guardados = 0
        
        for liga_id in ligas_a_sincronizar:
            if peticiones_usadas >= self.limite_diario:
                break
                
            partidos = self.obtener_partidos_terminados(league_id=liga_id)
            if not partidos:
                continue
            
            for p in partidos:
                if peticiones_usadas >= self.limite_diario:
                    print("🛑 Límite de seguridad diario alcanzado (80). El resto se descargará mañana.")
                    break
                    
                fixture_id = p["fixture"]["id"]
                fecha = p["fixture"]["date"].split("T")[0]
                equipo_local = p["teams"]["home"]["name"]
                equipo_visitante = p["teams"]["away"]["name"]
                goles_local = p["goals"]["home"]
                goles_contra = p["goals"]["away"]
                
                llave_local = f"{fecha}_{equipo_local}"
                
                if llave_local in registros_existentes:
                    continue 
                    
                print(f"📥 Descargando xG para: {equipo_local} vs {equipo_visitante} (Liga {liga_id})...")
                xg_local, xg_visitante = self.obtener_xg_partido(fixture_id)
                peticiones_usadas += 1
                
                if xg_local is None or xg_visitante is None:
                    continue 
                    
                # Guardar Local
                supabase.table('historial_xg').upsert({
                    "fecha": fecha, "equipo": equipo_local, "rival": equipo_visitante,
                    "localia": "Local", "goles_favor": int(goles_local), "goles_contra": int(goles_contra),
                    "xg_favor": xg_local, "xg_contra": xg_visitante
                }, on_conflict="fecha,equipo,rival").execute()
                
                # Guardar Visitante
                supabase.table('historial_xg').upsert({
                    "fecha": fecha, "equipo": equipo_visitante, "rival": equipo_local,
                    "localia": "Visitante", "goles_favor": int(goles_contra), "goles_contra": int(goles_local),
                    "xg_favor": xg_visitante, "xg_contra": xg_local
                }, on_conflict="fecha,equipo,rival").execute()
                
                nuevos_guardados += 2
            
        print(f"✅ Sincronización completa. {nuevos_guardados} nuevos registros en Supabase.")