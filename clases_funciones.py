
import simpy
import numpy as np


class Maquina:
    def __init__(self, env, tipo, categoria, celda):
        self.maquina_recurso = simpy.Resource(env, capacity=1)
        self.nombre = tipo
        self.celda = celda
        self.categoria = categoria
        # Estdo True es con falla, False si esta operativa
        self.operativa = True
        self.libre = True
class Cliente:
    id = 0
    def __init__(self, tipo):
        self.id = Cliente.id
        Cliente.id += 1
        self.tipo = tipo
        self.toallas = 0
        # Puede cambiar
        self.rutina = []
        self.plan_cardio = False
        self.hora_llegada = 0
        self.celda = 0
        self.se_va = False
        self.lista_flex = []
        self.agua = 0



def alpha_t(t):
    s_j = np.array([0, 180, 360, 540, 720, 840])
    alpha_total = np.array([19.1, 24.89, 23.15, 34.93, 40.6])
    k = np.size(alpha_total) 
    # Tasa del tramo al que pertenece t
    j = np.searchsorted(s_j, t, side='right') - 1
    j = min(j, k - 1)
    return alpha_total[j]

def simular_ppnh_tramos(rng, reescalar = True):
    # Thinning por intervalos ocupando los tramos como intervalos
    # Si reescalar = False, se omite el reescalamiento del Paso 3 (¡incorrecto!)
    alpha_total = np.array([19.1, 24.89, 23.15, 34.93, 40.6])
    s_j = np.array([0, 180, 360, 540, 720, 840])
    k = np.size(alpha_total) 
    # Paso 1: t = 0, primer tramo, lista de eventos vacía
    t = 0.0
    j = 0
    S_n = []

    # Paso 2: simulamos la primera exponencial
    x = rng.exponential(1/alpha_total[j])

    while True:
        # Paso 3: ¿el candidato queda fuera del tramo j?
        if t + x > s_j[j+1]:
            if j == k - 1:
                break
            # Tiempo sobrante después de s_{j+1}
            x = x - (s_j[j+1] - t)
            if reescalar:
                # Reescalamos para el próximo tramo
                x = x * alpha_total[j] / alpha_total[j+1]

            t = s_j[j+1]
            j = j + 1
            continue
        # Paso 4: actualizamos el tiempo y simulamos U ~ Uniforme(0,1)
        t = t + x
        u = rng.uniform()
        # Como alpha_t(t) = alpha_j en el tramo, aceptamos siempre (p(t) = 1)
        if u <= alpha_t(t) / alpha_total[j]:
            S_n.append(t)
        x = rng.exponential(1/alpha_total[j])
    return np.array(S_n)

def generar_lista_cliente(rng, S_n):
    alpha_E = np.array([5.8, 7.48, 6.61, 9.98, 11.6])
    alpha_X = np.array([2.5, 3.31, 3.31, 4.99, 5.8])
    alpha_F = np.array([5.8, 7.48, 6.61, 9.98, 11.6])
    alpha_I = np.array([5, 6.62, 6.62, 9.98, 11.6])
    resultados = []
    for llegada in S_n:
        if 7 <= llegada < 10:
            total = alpha_X[0] + alpha_F[0] + alpha_I[0] + alpha_E[0]
            p_p = [alpha_E[0]/total, alpha_X[0]/total, alpha_F[0]/total, alpha_I[0]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)[0]
        elif 10 <= llegada < 13:
            total = alpha_X[1] + alpha_F[1] + alpha_I[1] + alpha_E[1]
            p_p = [alpha_E[1]/total, alpha_X[1]/total, alpha_F[1]/total, alpha_I[1]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)[0]
        elif 13 <= llegada < 16:
            total = alpha_X[2] + alpha_F[2] + alpha_I[2] + alpha_E[2]
            p_p = [alpha_E[2]/total, alpha_X[2]/total, alpha_F[2]/total, alpha_I[2]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)[0]
        elif 16 <= llegada < 19:
            total = alpha_X[3] + alpha_F[3] + alpha_I[3] + alpha_E[3]
            p_p = [alpha_E[3]/total, alpha_X[3]/total, alpha_F[3]/total, alpha_I[3]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)[0]
        else:
            total = alpha_X[4] + alpha_F[4] + alpha_I[4] + alpha_E[4]
            p_p = [alpha_E[4]/total, alpha_X[4]/total, alpha_F[4]/total, alpha_I[4]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)[0]
        minuto_llegada = llegada * 60
        resultados += [[minuto_llegada, perfil]]
    return resultados

def elegir_rutina(categoria, desglose_rutina, rgn):
    # Puede ser necesario guardar la categoria, por el dict  self.consumo_aguaxw
    rutina = []
    for rutina_escogida in desglose_rutina:
        if categoria == 'Tren superior':
            if rutina_escogida == 'Empuje principal':
                empuje_principal = rgn.choice(['Press de pecho', 'Press de hombros'], p=[0.65, 0.35])
                rutina += [[empuje_principal, 'pen']]
            elif rutina_escogida == 'Jalon principal':
                jalon_principal = rgn.choice(['Jalon al pecho', 'Remo sentado'], p=[0.55, 0.45])
                rutina += [[jalon_principal, 'pen']]
            elif rutina_escogida == 'Empuje secundario':
                if empuje_principal != 'Press de hombros':
                    rutina += [['Press de hombros', 'pen']]
                else: 
                    rutina += [['Aperturas de pecho', 'pen']]
            elif rutina_escogida == 'Jalon secundario':
                if jalon_principal != 'Remo sentado':
                    rutina += [['Remo sentado', 'pen']]
                else:
                    rutina += [['Curl de biceps', 'pen']]
        elif categoria == 'Cuerpo completo':
            if rutina_escogida == 'Piernas':
                eje_pierna = rgn.choice(['Prensa de piernas', 'Extension de piernas', 'Curl femoral'], p=[0.7, 0.2, 0,1])
                rutina += [[eje_pierna, 'pen']]
            elif rutina_escogida == 'Empuje':
                eje_empuje = rgn.choice(['Press de pecho', 'Press de hombros', 'Aperturas de pecho'], p=[0.6, 0.3, 0,1])
                rutina += [[eje_empuje, 'pen']]
            elif rutina_escogida == 'Jalon':
                eje_jalon = rgn.choice(['Jalon al pecho', 'Remo sentado', 'Curl de biceps'], p=[0.5, 0.4, 0,1])
                rutina += [[eje_jalon, 'pen']]
            elif rutina_escogida == 'Complemento':
                principal = rgn.choice(['Piernas', 'Empuje', 'Jalon'], p=[0.4, 0.3, 0,3])
                if principal == 'Piernas':
                    eleccion = ['Prensa de piernas', 'Extension de piernas', 'Curl femoral']
                    eleccion_posible = []
                    for ejercicio in eleccion:
                        if ejercicio != eje_pierna:
                            eleccion_posible += [ejercicio]
                elif principal == 'Empuje':
                    eleccion = ['Press de pecho', 'Press de hombros', 'Aperturas de pecho']
                    eleccion_posible = []
                    for ejercicio in eleccion:
                        if ejercicio != eje_empuje:
                            eleccion_posible += [ejercicio]
                else: 
                    eleccion = ['Jalon al pecho', 'Remo sentado', 'Curl de biceps']
                    eleccion_posible = []
                    for ejercicio in eleccion:
                        if ejercicio != eje_jalon:
                            eleccion_posible += [ejercicio]
                eleccion_posible = rgn.choice(eleccion_posible, p=[0.5, 0.5])
                rutina += [[eleccion_posible, 'pen']]

        else:     
            rutina += [[rutina_escogida, 'pen']] # pen de pendiente :)
        return rutina
