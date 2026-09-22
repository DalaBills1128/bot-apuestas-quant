import difflib

def encontrar_mejor_coincidencia(nombre_equipo, lista_candidatos, umbral=0.6):
    """
    Busca el nombre de equipo más parecido en una lista de candidatos 
    utilizando coincidencia difusa (fuzzy matching) mediante difflib.
    
    :param nombre_equipo: String con el nombre del equipo a buscar.
    :param lista_candidatos: Lista de strings con los nombres disponibles.
    :param umbral: Valor flotante entre 0 y 1 para la similitud mínima requerida.
    :return: El mejor nombre coincidente o None si no supera el umbral.
    """
    if not lista_candidatos:
        return None
        
    # get_close_matches busca la coincidencia más cercana en la lista
    coincidencias = difflib.get_close_matches(
        nombre_equipo, 
        lista_candidatos, 
        n=1,             # Queremos solo la mejor opción
        cutoff=umbral    # Nivel mínimo de similitud (0.6 = 60%)
    )
    
    if coincidencias:
        return coincidencias[0]
    return None

# Prueba rápida del módulo
if __name__ == "__main__":
    equipos_casa_apuestas = [
        "Real Madrid CF", 
        "FC Barcelona", 
        "Club Atlético de Madrid", 
        "Sevilla FC"
    ]
    
    # Nombre que viene de la API de estadísticas (ligeramente distinto)
    nombre_api_estadisticas = "Real Madrid"
    
    mejor_match = encontrar_mejor_coincidencia(nombre_api_estadisticas, equipos_casa_apuestas, umbral=0.5)
    
    print("🔍 Prueba del Fuzzy Matcher:")
    print(f"Buscando en la casa de apuestas: '{nombre_api_estadisticas}'")
    print(f"Coincidencia alineada con éxito: '{mejor_match}'")