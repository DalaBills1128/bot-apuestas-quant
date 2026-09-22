import numpy as np
import pandas as pd
from scipy.stats import poisson
from scipy.optimize import minimize
from datetime import datetime

class DixonColesModel:
    def __init__(self, xi=0.0065):
        """
        xi: Factor de decaimiento temporal (Time Decay).
            0.0065 es el estándar Quant: da mucho más peso a los partidos 
            recientes y reduce la relevancia matemática de los antiguos.
        """
        self.xi = xi
        self.equipos = []
        self.params = {}

    def _rho_correction(self, x, y, lambda_x, lambda_y, rho):
        """Ajuste de Dixon-Coles para corregir la subestimación de empates (0-0, 1-1, 1-0, 0-1)."""
        if x == 0 and y == 0:
            return 1 - lambda_x * lambda_y * rho
        elif x == 0 and y == 1:
            return 1 + lambda_x * rho
        elif x == 1 and y == 0:
            return 1 + lambda_y * rho
        elif x == 1 and y == 1:
            return 1 - rho
        else:
            return 1.0

    def _log_likelihood(self, params, df):
        """
        Función de Máxima Verosimilitud. El algoritmo evalúa millones de escenarios
        para encontrar los coeficientes exactos de ataque y defensa.
        """
        num_equipos = len(self.equipos)
        
        # Extraer parámetros de la iteración actual
        ataque = params[:num_equipos]
        defensa = params[num_equipos:2*num_equipos]
        rho, home_adv = params[-2:]

        log_lik = 0.0

        for idx, row in df.iterrows():
            i_local = self.equipos.index(row['equipo_local'])
            i_visitante = self.equipos.index(row['equipo_visitante'])

            # Expected Goals (xG) proyectados usando los coeficientes de fuerza
            lambda_local = np.exp(ataque[i_local] + defensa[i_visitante] + home_adv)
            lambda_visit = np.exp(ataque[i_visitante] + defensa[i_local])

            # Alimentamos con los xG reales de la base de datos (Supabase)
            xg_local = row['xg_local']
            xg_visitante = row['xg_visitante']
            peso_temporal = row['peso']

            # Calcular probabilidad con Poisson
            prob_local = poisson.pmf(round(xg_local), lambda_local)
            prob_visit = poisson.pmf(round(xg_visitante), lambda_visit)
            
            # Ajustar empates
            ajuste = self._rho_correction(round(xg_local), round(xg_visitante), lambda_local, lambda_visit, rho)

            # Verosimilitud ponderada por fecha
            prob_total = prob_local * prob_visit * ajuste
            if prob_total > 0:
                log_lik += peso_temporal * np.log(prob_total)

        # scipy.optimize minimiza funciones, por lo que retornamos el negativo
        return -log_lik

    def entrenar(self, df):
        """
        Entrena el modelo calculando la fuerza real de cada equipo.
        """
        # Calcular días transcurridos para aplicar el Time Decay
        fecha_actual = datetime.now()
        df['dias_pasados'] = (fecha_actual - pd.to_datetime(df['fecha'])).dt.days
        df['peso'] = np.exp(-self.xi * df['dias_pasados'])

        # Obtener lista única de equipos
        self.equipos = list(set(df['equipo_local'].unique().tolist() + df['equipo_visitante'].unique().tolist()))
        num_equipos = len(self.equipos)

        # Semilla inicial para el optimizador: [ataques], [defensas], rho, home_advantage
        init_params = np.concatenate((np.ones(num_equipos), np.zeros(num_equipos), [0.0, 0.2]))

        # Límites: Ataque > 0, Defensa libre, Rho entre -1 y 1
        bounds = [(0, None)] * num_equipos + [(None, None)] * num_equipos + [(-1, 1), (0, None)]

        # Restricción: Para que el sistema converja, el promedio de ataque debe ser 1
        constraints = [{'type': 'eq', 'fun': lambda x: sum(x[:num_equipos]) - num_equipos}]

        print("⏳ Resolviendo matrices de máxima verosimilitud (xG)...")
        # SLSQP es un método de Programación Cuadrática Secuencial perfecto para esto
        res = minimize(self._log_likelihood, init_params, args=(df,), bounds=bounds, constraints=constraints, method='SLSQP')
        
        if res.success:
            print("✅ Modelo Dixon-Coles calibrado con éxito.")
            self.params = {
                'ataque': dict(zip(self.equipos, res.x[:num_equipos])),
                'defensa': dict(zip(self.equipos, res.x[num_equipos:2*num_equipos])),
                'rho': res.x[-2],
                'home_adv': res.x[-1]
            }
        else:
            print("❌ Error de optimización:", res.message)

    def predecir_partido(self, equipo_local, equipo_visitante, max_goles=6):
        """
        Genera las probabilidades reales (1X2) cruzando las fuerzas de ambos equipos.
        """
        if not self.params:
            raise ValueError("El modelo debe ser entrenado con datos históricos primero.")
            
        ataque_loc = self.params['ataque'].get(equipo_local, 1.0)
        defensa_loc = self.params['defensa'].get(equipo_local, 0.0)
        ataque_vis = self.params['ataque'].get(equipo_visitante, 1.0)
        defensa_vis = self.params['defensa'].get(equipo_visitante, 0.0)

        # Proyección final de xG para el partido
        lambda_local = np.exp(ataque_loc + defensa_vis + self.params['home_adv'])
        lambda_visit = np.exp(ataque_vis + defensa_loc)

        # Construir la matriz de resultados exactos (0-0, 1-0, 2-1, etc.)
        matriz = np.zeros((max_goles, max_goles))
        for i in range(max_goles):
            for j in range(max_goles):
                prob = poisson.pmf(i, lambda_local) * poisson.pmf(j, lambda_visit)
                prob *= self._rho_correction(i, j, lambda_local, lambda_visit, self.params['rho'])
                matriz[i, j] = max(0, prob)

        matriz /= np.sum(matriz) # Normalización estadística

        # Probabilidades agregadas (1, X, 2)
        prob_local = np.sum(np.tril(matriz, -1))
        prob_empate = np.sum(np.diag(matriz))
        prob_visit = np.sum(np.triu(matriz, 1))

        return {
            'prob_local': round(prob_local, 4),
            'prob_empate': round(prob_empate, 4),
            'prob_visitante': round(prob_visit, 4),
            'cuota_justa_local': round(1 / prob_local, 2) if prob_local > 0 else 0,
            'cuota_justa_empate': round(1 / prob_empate, 2) if prob_empate > 0 else 0,
            'cuota_justa_visitante': round(1 / prob_visit, 2) if prob_visit > 0 else 0
        }