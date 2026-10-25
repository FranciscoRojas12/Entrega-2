
import simpy
import numpy as np


class Maquina:
    def __init__(self, env, tipo, categoria, celda):
        self.maquina_recurso = simpy.Resource(env, capacity=1)
        self.list_id_cliente = []
        self.nombre = tipo
        self.celda = celda
        self.categoria = categoria
        # Estado True es con falla, False si esta operativa
        self.operativa = True
        self.libre = True
        self.evento = simpy.Event(env)

class Cliente:
    id = 0
    def __init__(self, tipo, agua, toallas, T_max):
        self.id = Cliente.id
        Cliente.id += 1
        self.tiempo_acumulado_cardio = 0
        self.fallo_maquina = False
        self.admitido = False
        self.velocidad = 0
        self.tipo = tipo
        self.toallas = toallas
        self.rutina = []
        self.tiempo_acumulado = []
        self.plan_cardio = False
        self.cardio_completado = False
        self.hora_llegada = 0
        self.espera_recepcion = 0
        self.espera_fuerza = 0
        self.espera_cardio = 0
        self.espera_asistente = 0
        self.espera_agua = 0
        self.espera_toallas = 0
        self.celda = 0
        self.se_va = False
        self.T_max = T_max
        self.lista_flex = []
        self.agua = agua
        self.pedir_maquina = ''
        self.seguir_ejercicio = True
        
    def completo_rutina_fuerza(self):
        completo = True
        for ejercicio in self.rutina:
            if ejercicio[1] != 'compl':
                completo = False
                break
        return completo
    def cumplimento_ejercicio(self):
        n_total_rutina = 0
        n_completado = 0
        for ejercicio in self.rutina:
            n_total_rutina += 1
            if ejercicio[1] == 'compl':
                n_completado += 1
        return n_completado, n_total_rutina
    def n_ejercicios_pendientes_omitidos(self):
        n_pendientes = 0
        n_omitidos = 0
        for ejercicio in self.rutina:
            if ejercicio[1] == 'omit':
                n_omitidos += 1
            elif ejercicio[1] == 'pen':
                n_pendientes += 1
        return n_pendientes, n_omitidos
    def insatisfaccion_usuario(self, dict_insatisfaccion):
        n_completado = 0
        n_ejercicios = 0
        for ejercicio in self.rutina:
            n_ejercicios += 1
            if ejercicio[1] == 'compl':
                n_completado += 1
        D_iR = 1 - (n_completado/n_ejercicios)
        D_iW = min(1, (self.espera_cardio + self.espera_recepcion + self.espera_asistente + self.espera_fuerza)/self.T_max)
        if self.plan_cardio == True:
            D_iC = 1 if self.cardio_completado == False else 0
        else:
            D_iC = 0
        D_iS = min(1, (self.espera_agua + self.espera_toallas)/self.T_max)
        D_i = dict_insatisfaccion[self.tipo]['R'] * D_iR + dict_insatisfaccion[self.tipo]['W'] *  D_iW + dict_insatisfaccion[self.tipo]['C'] * D_iC + dict_insatisfaccion[self.tipo]['S'] * D_iS
        return D_i, D_iR, D_iW, D_iC, D_iS








def alpha_t(t):
    s_j = np.array([0, 180, 360, 540, 720, 840])
    alpha_total = np.array([19.1 / 60, 24.89 / 60, 23.15 / 60, 34.93 / 60, 40.6 / 60])
    k = np.size(alpha_total) 
    # Tasa del tramo al que pertenece t
    j = np.searchsorted(s_j, t, side='right') - 1
    j = min(j, k - 1)
    return alpha_total[j]

def simular_ppnh_tramos(rng, reescalar = True):
    # Thinning por intervalos ocupando los tramos como intervalos
    # Si reescalar = False, se omite el reescalamiento del Paso 3 (¡incorrecto!)
    alpha_total = np.array([19.1 / 60, 24.89 / 60, 23.15 / 60, 34.93 / 60, 40.6 / 60])
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
    alpha_E = np.array([5.8 / 60, 7.48 / 60, 6.61 / 60, 9.98 / 60, 11.6 / 60])
    alpha_X = np.array([2.5 / 60, 3.31 / 60, 3.31 / 60, 4.99 / 60, 5.8 / 60])
    alpha_F = np.array([5.8 / 60, 7.48 / 60, 6.61 / 60, 9.98 / 60, 11.6 / 60])
    alpha_I = np.array([5 / 60, 6.62 / 60, 6.62 / 60, 9.98 / 60, 11.6 / 60])
    resultados = []
    for llegada in S_n:
        if 0 <= llegada < 180:
            total = alpha_X[0] + alpha_F[0] + alpha_I[0] + alpha_E[0]
            p_p = [alpha_E[0]/total, alpha_X[0]/total, alpha_F[0]/total, alpha_I[0]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)
        elif 180 <= llegada < 360:
            total = alpha_X[1] + alpha_F[1] + alpha_I[1] + alpha_E[1]
            p_p = [alpha_E[1]/total, alpha_X[1]/total, alpha_F[1]/total, alpha_I[1]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)
        elif 360 <= llegada < 540:
            total = alpha_X[2] + alpha_F[2] + alpha_I[2] + alpha_E[2]
            p_p = [alpha_E[2]/total, alpha_X[2]/total, alpha_F[2]/total, alpha_I[2]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)
        elif 540 <= llegada < 720:
            total = alpha_X[3] + alpha_F[3] + alpha_I[3] + alpha_E[3]
            p_p = [alpha_E[3]/total, alpha_X[3]/total, alpha_F[3]/total, alpha_I[3]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)
        else:
            total = alpha_X[4] + alpha_F[4] + alpha_I[4] + alpha_E[4]
            p_p = [alpha_E[4]/total, alpha_X[4]/total, alpha_F[4]/total, alpha_I[4]/total]
            perfil = rng.choice(['E', 'X', 'F', 'I'], p =  p_p)
        resultados += [[llegada, perfil]]
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
                eje_pierna = rgn.choice(['Prensa de piernas', 'Extension de piernas', 'Curl femoral'], p=[0.7, 0.2, 0.1])
                rutina += [[eje_pierna, 'pen']]
            elif rutina_escogida == 'Empuje':
                eje_empuje = rgn.choice(['Press de pecho', 'Press de hombros', 'Aperturas de pecho'], p=[0.6, 0.3, 0.1])
                rutina += [[eje_empuje, 'pen']]
            elif rutina_escogida == 'Jalon':
                eje_jalon = rgn.choice(['Jalon al pecho', 'Remo sentado', 'Curl de biceps'], p=[0.5, 0.4, 0.1])
                rutina += [[eje_jalon, 'pen']]
            elif rutina_escogida == 'Complemento':
                principal = rgn.choice(['Piernas', 'Empuje', 'Jalon'], p=[0.4, 0.3, 0.3])
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
