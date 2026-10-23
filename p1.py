import simpy
import numpy as np
import scipy.stats as st
from collections import deque
from clases_funciones import Maquina, Cliente, simular_ppnh_tramos, generar_lista_cliente, elegir_rutina
# Resume deque progra avanzada: deque() crea deque, con deque.append(elemento) agregamos al final de la cola, deque.popleft() saca la que esta al final de la cola


class Simulacion:
    def __init__(self):
        self.dict_datos_replica = {}
        self.cords_celda = {}
        for cord_x in range(7):
            for cord_y in range(7):
                self.cords_celda[(cord_x) * 7 + (cord_y + 1)] = (cord_x, cord_y)
        #Distribuciones de velocidad según tipo de persona
        # loc es el minimo, scale es el ancho (max-min) y c es (moda-minim)/scale
        self.velocidad = {
            'E' : lambda: st.triang.rvs(loc = 55, scale = (85 - 55), c = ((70 - 55) / (85 - 55)), random_state=self.rng),
            'X' : lambda: st.triang.rvs(loc = 70, scale = (100 - 70), c = ((85 - 70) / (100 - 70)), random_state=self.rng),
            'F' : lambda: st.triang.rvs(loc = 55, scale = (85 - 55), c = ((70 - 55) / (85 - 55)), random_state=self.rng),
            'I' : lambda: st.triang.rvs(loc = 48, scale = (76 - 48), c = ((62 - 48) / (76 - 48)), random_state=self.rng),
            'R' : lambda: st.triang.rvs(loc = 55, scale = (85 - 55), c = ((70 - 55) / (85 - 55)), random_state=self.rng),
            'PT' : lambda: st.triang.rvs(loc = 65, scale = (105 - 65), c = ((85 - 65) / (105 - 65)), random_state=self.rng),
            'M' : lambda: st.triang.rvs(loc = 45, scale = (75 - 45), c = ((60 - 45) / (75 - 45)), random_state=self.rng),}
        # REVISAR EL VALOR DE LOS PARAMETROS
        self.tiempo_registro = {
            'E' : lambda: self.generar_mezcla(0.85, 0.15, st.gamma.rvs(a=10, scale=0.16, random_state=self.rng), st.lognorm.rvs(s=0.22, scale=np.exp(1.05), random_state=self.rng)),
            'X' : lambda: min(2.2, st.lognorm.rvs(s=0.28, scale=np.exp(0.05), random_state=self.rng)),
            'F' : lambda: self.generar_mezcla(0.85, 0.15, st.gamma.rvs(a=10, scale=0.16, random_state=self.rng), st.lognorm.rvs(s=0.22, scale=np.exp(1.05), random_state=self.rng)),
            'I' : lambda: self.generar_mezcla(0.75, 0.25, st.gamma.rvs(a=9, scale=0.25, random_state=self.rng), st.lognorm.rvs(s=0.20, scale=np.exp(1.25), random_state=self.rng))}
        self.rutinas_opciones = {
            'E' : lambda: self.rng.choice(['Empuje', 'Jalon', 'Piernas', 'Tren superior', 'Cuerpo completo'], p = [0.2, 0.2, 0.2, 0.25, 0.15]),
            'X' : lambda: self.rng.choice(['Empuje', 'Jalon', 'Piernas', 'Tren superior', 'Cuerpo completo'], p = [0.2, 0.2, 0.2, 0.25, 0.15]),
            'F' : lambda: self.rng.choice(['Empuje', 'Jalon', 'Piernas', 'Tren superior', 'Cuerpo completo'], p = [0.15, 0.15, 0.15, 0.3, 0.25]),
            'I' : lambda: self.rng.choice(['Empuje', 'Jalon', 'Piernas', 'Tren superior', 'Cuerpo completo'], p = [0.25, 0.25, 0.25, 0.15, 0.10])}
        self.orden_ejecucion_rutina ={
            'E' : {
                'Empuje' : ['Press de pecho', 'Press de hombros', 'Aperturas de pecho'],
                'Jalon' : ['Jalon al pecho', 'Remo sentado', 'Curl de biceps'],
                'Piernas' : ['Prensa de piernas', 'Extension de piernas', 'Curl femoral'],
                'Tren superior' : ['Empuje principal', 'Jalon principal', 'Empuje secundario', 'Jalon secundario'],
                'Cuerpo completo' : ['Piernas', 'Empuje', 'Jalon', 'Complemento']},
            'X' : {
                'Empuje' : ['Press de pecho', 'Aperturas de pecho', 'Press de hombros'],
                'Jalon': ['Jalon al pecho', 'Curl de biceps', 'Remo sentado'],
                'Piernas': ['Prensa de piernas', 'Extension de piernas', 'Curl femoral'],
                'Tren superior': ['Empuje principal', 'Jalon principal', 'Jalon secundario', 'Empuje secundario'],
                'Cuerpo completo': ['Empuje', 'Jalon', 'Piernas', 'Complemento']},
            'I' : {
                'Empuje' : ['Press de pecho', 'Press de hombros', 'Aperturas de pecho'],
                'Jalon': ['Remo sentado', 'Jalon al pecho', 'Curl de biceps'],
                'Piernas': ['Prensa de piernas', 'Curl femoral', 'Extension de piernas'],
                'Tren superior': ['Empuje principal', 'Empuje secundario', 'Jalon principal', 'Jalon secundario'],
                'Cuerpo completo': ['Piernas', 'Empuje', 'Jalon', 'Complemento']},
            'F' : {
                'Empuje' : ['Seleccion dinamica'],
                'Jalon': ['Seleccion dinamica'],
                'Piernas':['Seleccion dinamica'],
                'Tren superior': ['Seleccion dinamica'],
                'Cuerpo completo':['Seleccion dinamica']}}
        self.agregar_polea = {
            'E': {'Empuje': 0.18, 'Jalon': 0.22, 'Piernas': 0.12, 'Tren superior': 0.2, 'Cuerpo completo': 0.15},
            'X': {'Empuje': 0.18, 'Jalon': 0.22, 'Piernas': 0.12, 'Tren superior': 0.2, 'Cuerpo completo': 0.15},
            'I': {'Empuje': 0.4, 'Jalon': 0.44, 'Piernas': 0.28, 'Tren superior': 0.38, 'Cuerpo completo': 0.32 },
            'F': {'Empuje': 0.4, 'Jalon': 0.44, 'Piernas': 0.28, 'Tren superior': 0.38, 'Cuerpo completo': 0.32}}
        # T_k^{max} [min], tau_k [min], Z_k^B [L], p_k^C
        self.info_perfil_t8 = {'E' : [72, 8, 1.25, 0.4], 'X' : [50, 5, 1, 0.15], 'I' : [70, np.inf, 1.5, 0.28], 'F' : [52, 7, 1.25, 0.35]}
        # REVISAR PARAMETROS
        self.dur_ejer_fuerza = {
            'E' : {
                'G1': lambda: st.gamma.rvs(a = 16, scale = 0.5, random_state=self.rng),
                'G2': lambda: st.gamma.rvs(a = 16, scale = 0.375, random_state=self.rng),
                'G3': lambda: st.gamma.rvs(a = 16, scale = 0.625, random_state=self.rng),
                'G4': lambda: st.gamma.rvs(a = 16, scale = 0.4375, random_state=self.rng)},
            'X' : {
                'G1': lambda: st.beta.rvs(a=3, b=3, loc=3, scale=(6-3), random_state=self.rng),
                'G2': lambda: st.beta.rvs(a=3, b=3, loc=2.5, scale=(5-2.5), random_state=self.rng),
                'G3': lambda: st.beta.rvs(a=3, b=3, loc=4, scale=(7-4), random_state=self.rng),
                'G4': lambda: st.beta.rvs(a=3, b=3, loc=3, scale=(5.5-3), random_state=self.rng)},
            'I' : {
                'G1': lambda: st.gamma.rvs(a = 16, scale = 0.725, random_state=self.rng),
                'G2': lambda: st.gamma.rvs(a = 16, scale = 0.54375, random_state=self.rng),
                'G3': lambda: st.gamma.rvs(a = 16, scale = 0.90625, random_state=self.rng),
                'G4': lambda: st.gamma.rvs(a = 16, scale = 0.634375, random_state=self.rng)},
            'F' : {
                'G1': lambda: st.gamma.rvs(a = 16, scale = 0.5, random_state=self.rng),
                'G2': lambda: st.gamma.rvs(a = 16, scale = 0.375, random_state=self.rng),
                'G3': lambda: st.gamma.rvs(a = 16, scale = 0.625, random_state=self.rng),
                'G4': lambda: st.gamma.rvs(a = 16, scale = 0.4375, random_state=self.rng)}}
        self.g_dur_ejer_fuerza = {
            'Press de pecho': 'G1', 'Press de hombros' : 'G1', 'Jalon al pecho': 'G1', 'Remo sentado': 'G1', 'Polea multifuncional': 'G1', 'Aperturas de pecho': 'G2', 'Curl de biceps': 'G2',
            'Prensa de piernas': 'G3', 'Curl femoral': 'G4', 'Extension de piernas': 'G4'}
        # REVISAR PARAMETROS
        self.dur_ejer_cardio = {
            'E': lambda: min(28, st.gamma.rvs(a = 9, scale = 2, random_state=self.rng)),
            'X': lambda: st.beta.rvs(a=3, b=3, loc=6, scale=(12-6), random_state=self.rng),
            'F': lambda: self.generar_mezcla(0.75, 0.25, st.gamma.rvs(a=12, scale=1.2, random_state=self.rng), st.lognorm.rvs(s=0.18, scale=np.exp(3), random_state=self.rng)),
            'I': lambda: self.generar_mezcla(0.7, 0.2, st.gamma.rvs(a=10, scale=2.3, random_state=self.rng), st.lognorm.rvs(s=0.2, scale=np.exp(3.55), random_state=self.rng))}
        self.tiempo_reparacion = {
            'G1': lambda: min(50, st.gamma.rvs(a = 7, scale = 5, random_state=self.rng)),
            'G2': lambda: self.generar_mezcla(0.75, 0.25, st.gamma.rvs(a=12, scale=1.35, random_state=self.rng), st.lognorm.rvs(s=0.18, scale=np.exp(3.55), random_state=self.rng)),
            'G3': lambda: min(48, st.fisk.rvs(c=4.2, scale=20.5, random_state=self.rng)),
            'G4': lambda: self.generar_mezcla(0.65, 0.35, st.gamma.rvs(a=12, scale=2.1, random_state=self.rng), st.lognorm.rvs(s=0.16, scale=np.exp(3.7), random_state=self.rng)),
            'G5': lambda: min(55, self.generar_mezcla(0.7, 0.3, st.weibull_min.rvs(c = 4, scale = 21, loc = 0, random_state=self.rng), st.lognorm.rvs(s=0.2, scale=np.exp(3.55), random_state=self.rng)))}
        self.g_reparacion = {'Trotadora': 'G1','Aperturas de pecho': 'G2','Press de pecho': 'G2', 'Press de hombros' : 'G2', 'Curl de biceps': 'G3', 'Jalon al pecho': 'G3','Remo sentado': 'G3',
        'Prensa de piernas': 'G4', 'Curl femoral': 'G4', 'Extension de piernas': 'G4', 'Polea multifuncional': 'G5'} 
        # REVISAR PARAMETROS
        self.entrenador_asistencia = {
            'E': {'Press de pecho': 0.10, 'Press de hombros': 0.12, 'Aperturas de pecho': 0.06, 'Jalon al pecho': 0.10, 'Remo sentado': 0.10, 'Curl de biceps': 0.05,
                'Prensa de piernas': 0.14, 'Curl femoral': 0.08, 'Extension de piernas': 0.06, 'Polea multifuncional': 0.15},
            'X': {'Press de pecho': 0.06, 'Press de hombros': 0.07, 'Aperturas de pecho': 0.04, 'Jalon al pecho': 0.06, 'Remo sentado': 0.06,
                'Curl de biceps': 0.03, 'Prensa de piernas': 0.09, 'Curl femoral': 0.05, 'Extension de piernas': 0.04,'Polea multifuncional': 0.09},
            'I': {'Press de pecho': 0.06, 'Press de hombros': 0.08, 'Aperturas de pecho': 0.05, 'Jalon al pecho': 0.06, 'Remo sentado': 0.06,
                'Curl de biceps': 0.03, 'Prensa de piernas': 0.09, 'Curl femoral': 0.05, 'Extension de piernas': 0.05, 'Polea multifuncional': 0.10},
            'F': {'Press de pecho': 0.12, 'Press de hombros': 0.14, 'Aperturas de pecho': 0.08, 'Jalon al pecho': 0.12, 'Remo sentado': 0.12,
                'Curl de biceps': 0.06, 'Prensa de piernas': 0.18, 'Curl femoral': 0.10, 'Extension de piernas': 0.08, 'Polea multifuncional': 0.18}}
        # REVISAR PARAMETROS
        self.consumo_agua = {
            'E': {
                'Empuje': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Jalon': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Piernas': lambda: st.gamma.rvs(a=9, scale=0.04, random_state=self.rng),
                'Multifuncional': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng)},
            'X': {
                'Empuje': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Jalon': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Piernas': lambda: st.gamma.rvs(a=9, scale=0.04, random_state=self.rng),
                'Multifuncional': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng)},
            'F': {
                'Empuje': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Jalon': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng),
                'Piernas': lambda: st.gamma.rvs(a=9, scale=0.04, random_state=self.rng),
                'Multifuncional': lambda: st.gamma.rvs(a=9, scale=0.03, random_state=self.rng)},
            'I': {
                'Empuje': lambda: st.gamma.rvs(a=9, scale=0.045, random_state=self.rng),
                'Jalon': lambda: st.gamma.rvs(a=9, scale=0.045, random_state=self.rng),
                'Piernas': lambda: st.gamma.rvs(a=9, scale=0.06, random_state=self.rng),
                'Multifuncional': lambda: st.gamma.rvs(a=9, scale=0.045, random_state=self.rng)}}
        self.probabilidad_falla = {
            'Trotadora': 0.005,
            'Press de pecho': 0.004,
            'Press de hombros': 0.004,
            'Aperturas de pecho': 0.004,
            'Jalon al pecho': 0.004,
            'Remo sentado': 0.004,
            'Curl de biceps': 0.004,
            'Prensa de piernas': 0.005,
            'Curl femoral': 0.005,
            'Extension de piernas': 0.005,
            'Polea multifuncional': 0.006}
        self.tiempo_reposicion = {
            'Agua': lambda: self.generar_mezcla(0.75, st.gamma.rvs(a=16, scale=0.35, random_state=self.rng), st.lognorm.rvs(s=0.30, scale=np.exp(2.45), random_state=self.rng)),
            'Toallas': lambda: st.gamma.rvs(a=16, scale=0.25, random_state=self.rng)}
    def generar_recursos(self):
        self.dict_maquinas = {}
        self.dict_maquinas_operativas = {}
        self.dict_maquinas_operativas['Press de pecho'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Press de hombros'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Aperturas de pecho'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Remo sentado'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Curl de biceps'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Prensa de piernas'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Curl femoral'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Extension de piernas'] = simpy.Event(self.env)
        self.dict_maquinas_operativas['Polea multifuncional'] = simpy.Event(self.env)

        self.dict_maquinas['Trotadora'] = [
            Maquina(self.env, 'Trotadora', 'Cardio', 14),
            Maquina(self.env, 'Trotadora', 'Cardio', 21),
            Maquina(self.env, 'Trotadora', 'Cardio', 28),
            Maquina(self.env, 'Trotadora', 'Cardio', 35)]
        self.dict_maquinas['Press de pecho'] = [
            Maquina(self.env, 'Press de pecho', 'Empuje', 42),
            Maquina(self.env, 'Press de pecho', 'Empuje', 47)]
        self.dict_maquinas['Press de hombros'] = [
            Maquina(self.env, 'Press de hombros', 'Empuje', 45),
            Maquina(self.env, 'Press de hombros', 'Empuje', 49)]
        self.dict_maquinas['Aperturas de pecho'] = [
            Maquina(self.env, 'Aperturas de pecho', 'Empuje', 46)]
        self.dict_maquinas['Jalon al pecho'] = [
            Maquina(self.env, 'Jalon al pecho', 'Jalon', 36),
            Maquina(self.env, 'Jalon al pecho', 'Jalon', 22)]
        self.dict_maquinas['Remo sentado'] = [
            Maquina(self.env, 'Remo sentado', 'Jalon', 15),
            Maquina(self.env, 'Remo sentado', 'Jalon', 39)]
        self.dict_maquinas['Curl de biceps'] = [
            Maquina(self.env, 'Curl de biceps', 'Jalon', 11),
            Maquina(self.env, 'Curl de biceps', 'Jalon', 33)]
        self.dict_maquinas['Prensa de piernas'] = [
            Maquina(self.env, 'Prensa de piernas', 'Piernas', 26),
            Maquina(self.env, 'Prensa de piernas', 'Piernas', 32)]
        self.dict_maquinas['Curl femoral'] = [
            Maquina(self.env, 'Curl femoral', 'Piernas', 31),
            Maquina(self.env, 'Curl femoral', 'Piernas', 24)]
        self.dict_maquinas['Extension de piernas'] = [
            Maquina(self.env, 'Extension de piernas', 'Piernas', 12),
            Maquina(self.env, 'Extension de piernas', 'Piernas', 10)]
        self.dict_maquinas['Polea multifuncional'] = [
            Maquina(self.env, 'Polea multifuncional', 'Multifuncional', 8),
            Maquina(self.env, 'Polea multifuncional', 'Multifuncional', 43)]

        #R costo ordinario [CLP/h] 4500 costo extra [CLP/h] 6750
        self.recepcionistas = simpy.PriorityResource(self.env, capacity=2)
        #t costo ordinario [CLP/h] 10000 costo extra [CLP/h] 15000
        self.tecnico = simpy.Resource(self.env, capacity=1)
        #e costo ordinario [CLP/h] 8000 costo extra [CLP/h] 12000
        self.entrenadores = simpy.Store(self.env, capacity=2)
        # El valor cera la celda en que se encuentre el entrenador
        for entrenador in range(1, 3):
            self.entrenadores.put([f'PT{entrenador}', 25])

        self.dispensador_acceso = simpy.Resource(self.env, capacity=1)
        self.dispensador_toallas = simpy.Store(self.env, capacity= 100)
        for toalla in (100):
            self.dispensador_toallas.put(1)
        self.bidon_acceso = simpy.Resource(self.env, capacity=1)
        self.bidon_agua = simpy.Container(self.env, capacity = 20, init = 20)

    def generar_mezcla(self, peso_a, distribucion_a, distribucion_b):
        u = st.uniform.rvs(loc = 1, scale = 1, random_state=self.rng)
        if u < peso_a:
            return distribucion_a
        else:
            return distribucion_b
        
    def distancia(self, coordenadas_a, coordenadas_b):
        return (0.7 * (abs(coordenadas_a[0] - coordenadas_b[0]) + abs(coordenadas_a[1] - coordenadas_b[1])) + 0.3 
                * (np.sqrt((coordenadas_a[0] - coordenadas_b[0])**2 + (coordenadas_a[1]- coordenadas_b[1])**2))) * 2.5
    
    def iniciar_simulacion(self, seed, n_replicas, misma_semilla = True):
        for replica in range(n_replicas):
            if misma_semilla:
                self.rng = np.random.default_rng(seed)
            else:
                self.rng = np.random.default_rng(seed + replica)
            self.simular_una_replica(replica)

    def simular_una_replica(self, id_replica):
        self.env = simpy.Environment()
        self.generar_recursos()
        self.dict_info_recolectada = {'int_llegada': 0, 'cliente_desviado': 0, 'n_fallas': 0}
        self.dict_datos_estado = {'n_clientes_sistema': 0, 'pedir_agua' : [False], 'pedir_toallas': [False], 'celda_tecnico': 7}
        # Poner procesos que van aquí
        self.env.process()
        # self.env.run()
        self.dict_datos_replica[id_replica] = [self.dict_info_recolectada, self.dict_datos_estado]

    def generar_cliente(self):
        lista_clientes = generar_lista_cliente(self.rgn, simular_ppnh_tramos(self.rgn, True))
        for cliente_llegada in lista_clientes:
            # Reiniciar id
            cliente = Cliente(cliente_llegada[1])
            yield self.env.timeout(cliente_llegada[0])
            self.env.process(self.llegada_clientes(cliente))

    def llegada_clientes(self, cliente):
        self.dict_info_recolectada['int_llegada'] += 1
        # Generar log
        if self.dict_datos_estado['n_clientes_sistema'] >= 30:
            self.dict_info_recolectada['cliente_desviado'] += 1
            # Generar log de entrada
        else:
            # Se actualiza la cantidad de clientes en el sistema
            self.dict_datos_estado['n_clientes_sistema'] +=1 
            # Se registra el tiempo de inicio de atencion
            cliente.hora_llegada = self.env.now()
            # Se calula y espera el tiempo de traslado de la celda 1 a la 7
            velocidad = self.velocidad[cliente.perfil]()
            distancia = self.distancia(self.cords_celda(1), self.cords_celda(7))
            yield self.env.timeout(distancia / velocidad)
            cliente.celda = 7
            # Se solicita recepcionista con prioridad 2
            with self.recepcionistas.request(priority= 2) as pedir_recepcionista:
                yield pedir_recepcionista
                # Ya teniendo a la recepcionista, se espera el tiempo de registro
                tiempo_registro = self.tiempo_registro[cliente.perfil]()
                yield self.env.timeout(tiempo_registro)
                # Se eliga la rutina
                seleccionar_rutina = self.rutinas_opciones[cliente.perfil]()
                if cliente.tipo == 'F':
                    # Da lo mismo cual, no sigue el orden
                    desglose_rutina = self.orden_ejecucion_rutina['I'][seleccionar_rutina]
                else:
                    desglose_rutina = self.orden_ejecucion_rutina[cliente.perfil][seleccionar_rutina]
                rutina = elegir_rutina(seleccionar_rutina, desglose_rutina, self.rng)
                p_p = self.agregar_polea[cliente.perfil][seleccionar_rutina]
                hacer_polea = st.bernoulli.rvs(p = p_p, random_state=self.rng)
                if hacer_polea == 1:
                    rutina += [['Polea multifuncional', 'pen']]
                else:
                    # No se hace polea, poner log tal vez
                    pass
                cliente.rutina = rutina
                # Se revisa si hace cardio
                p_c = self.info_perfil_t8[cliente.perfil][3]
                hacer_cardio = st.bernoulli.rvs(p = p_c, random_state=self.rng)
                if hacer_cardio == 1:
                    cliente.plan_cardio = True
                else:
                    cliente.plan_cardio = False
                # No se pide saca del dispensador, porque puede generar un deadlock (la recepcionista el la que repone toallas y si los se bloquean, el sistema no avanza)
                cliente.toallas = 2
            #Dice de la 6 a 13, pero según yo es de la 7 a 13
            velocidad = self.velocidad[cliente.perfil]()
            distancia = self.distancia(self.cords_celda(6), self.cords_celda(13))
            yield self.env.timeout(distancia / velocidad)
            cliente.celda = 13
            self.rutina_fuerza(cliente)
    # Considerar el 22:00, 900 minutos
    # T_i max
    # Consumo de toallas y agua
    # Carido no consume toallas

    def rutina_fuerza(self, cliente):
        if cliente.tipo == 'E':
            # Usar el se va para cortar reocrrido
            for recorrido in range(1, 3):
                for indice_ejercicio in len(cliente.rutina):
                    if cliente.toalla < 1:
                        self.buscar_toallas(cliente)
                    if cliente.rutina[indice_ejercicio][1] == 'pen' and cliente.se_va == False:
                        while True:
                            # El return es [hay maquina operativa?, hay maquina sin cola, [maquina con cola cercana, distancia], [maquina sin cola cercana, distancia]]
                            list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, self.dict_maquinas[cliente.rutina[indice_ejercicio][0]])
                            if list_respuesta[0] == True:
                                # Esto es para cuando hay maquina libre
                                list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                                velocidad = self.velocidad[cliente.perfil]()
                                recorrido = self.env.timeout(list_maquina_sel[1]/ velocidad)
                                tiempo_restante = self.info_perfil_t8[0]  - (self.now() - cliente.hora_llegada) if (self.info_perfil_t8[0]  - (self.now() - cliente.hora_llegada)) > 0 else 0
                                tiempo_restante = self.env.timeout(tiempo_restante)
                                # Hay que ver si en el reocrrido se puede ir o no. Porque si para en la mitad es raro
                                # Hay que poner la celda
                                tiempo_cierre = (900 - self.env.now()) if (900 - self.env.now()) else 0
                                tiempo_cierre = self.env.timeout(tiempo_cierre)
                                yield recorrido | tiempo_restante | tiempo_cierre
                                if tiempo_restante.triggered == True:
                                    cliente.se_va = True
                                    # Se va si llego a tiempo max durante reocorrido
                                    self.salida_cliente()
                                    break
                                elif tiempo_cierre.triggeered == True:
                                    cliente.se_va = True
                                    self.salida_cliente()
                                    break
                                else:
                                    cliente.celda = list_maquina_sel[0].celda
                                    if list_maquina_sel[0].operativa == True:
                                        self.ejecutar_ejercicio_fuerza(self, cliente, list_maquina_sel[0], indice_ejercicio)
                                    else:
                                        # Aqui llego a la maquina, pero al llegar esta la maquina esta con fallas
                                        pass
                            else:
                                # No hay maquina operativa
                                break
        elif cliente.tipo == 'X':
            for indice_ejercicio in len(cliente.rutina):
                if cliente.toalla < 1:
                    self.buscar_toallas(cliente)
                if cliente.rutina[indice_ejercicio][1] == 'pen' and cliente.se_va == False:
                    while True:
                        list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, self.dict_maquinas[cliente.rutina[indice_ejercicio][0]])
                        if list_respuesta[0] != False:
                            list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                            velocidad = self.velocidad[cliente.perfil]()
                            recorrido = self.env.timeout(list_maquina_sel[1]/ velocidad)
                            tiempo_restante = self.env.timeout(tiempo_restante)
                            yield recorrido | tiempo_restante
                            if tiempo_restante.triggered == True:
                                cliente.se_va = True
                                # Se va si llego a tiempo max durante reocorrido
                                self.salida_cliente()
                                break
                            else:
                                if list_maquina_sel[0].operativa == True:
                                    self.ejecutar_ejercicio_fuerza(self, cliente)
                                else:
                                    # Aqui llego a la maquina, pero al llegar esta la maquina esta con fallas
                                    pass            
                        else:
                            cliente.rutina[indice_ejercicio][1] == 'omit'
        elif cliente.tipo == 'F':



            toleracia_acumulada = {}
            for indice_ejercicio in len(cliente.rutina):
                # 0 porque no acumula toleracia todavia
                toleracia_acumulada[cliente.rutina[indice_ejercicio][0]] = 0


            
            for indice_ejercicio in len(cliente.rutina):
                if cliente.toalla < 1:
                    self.buscar_toallas(cliente)

        elif cliente.tipo == 'I':
            pass

    def ejecutar_ejercicio_fuerza(self, cliente, maquina, indice_ejercicio):
        try:
            tiempo_restante = self.info_perfil_t8[cliente.tipo][0] - (self.env.now() - cliente.hora_llegada)
            tiempo_restante = self.env.timeout(tiempo_restante)
            pedir_maquina = maquina.maquina_recurso.request()
            tiempo_max_espera = self.env.timeout(self.info_perfil_t8[cliente.tipo][1]) 
            tiempo_cierre = (900 - self.env.now()) if (900 - self.env.now()) else 0
            tiempo_cierre = self.env.timeout(tiempo_cierre)
            yield pedir_maquina | tiempo_max_espera | tiempo_restante | tiempo_cierre
            if tiempo_max_espera.triggered == True:
                  pass # Tiempo de espera maximamo
                  return
            elif tiempo_restante.triggered == True:
                  cliente.se_va = True
                  return
                  # Tiempo de estar en gimnacio
        except simpy.Interrupt as interrupcion:
              return
        # Aquí ya tiene la maquina
        maquina.libre = False
        p_entrenador = self.entrenador_asistencia[self.entrenador_asistencia[cliente.tipo][maquina.nombre]]
        nececita_entrenador = st.bernoulli.rvs(p=p_entrenador, random_state=self.rng)
        if nececita_entrenador == 1:
            entrenador = yield self.entrenadores.get()
            id_entrenador = entrenador[0]
            velocidad = self.velocidad['PT']()
            distancia = self.distancia(self.cords_celda(entrenador[1]), self.cords_celda(cliente.celda))
            yield self.env.timeout(distancia / velocidad)  
            # Cliente se va
        if cliente.se_va == False:
            g_maquina = self.g_dur_ejer_fuerza[maquina.nombre]
            tiempo_maquina = self.dur_ejer_fuerza[cliente.tipo][g_maquina]()
            yield self.env.timeout(tiempo_maquina)
            cliente.rutina[indice_ejercicio][1] = 'compl'
            p_falla = self.probabilidad_falla[maquina.nombre]
            falla_maquina = st.bernoulli.rvs(p=p_falla, random_state=self.rng)
            if falla_maquina == 1:
                maquina.operativa = False
                self.dict_info_recolectada['n_fallas'] += 1
                for cliente_en_cola in maquina.maquina_recurso.queue:
                    cliente_en_cola.proceso.interrupt(cause="La maquina ya no esta operativa")
                    maquina.maquina_recurso.release(pedir_maquina)
                    self.env.process(self.reparar_maquina(maquina))
            else:
                maquina.maquina_recurso.release(pedir_maquina)
            if nececita_entrenador == 1: 
                self.entrenadores.put([id_entrenador, cliente.celda])
            # Puede cambiar
            ejercicio = maquina.categoria if maquina.categoria in ['Empuje', 'Jalon', 'Piernas'] else 'Multifuncional'
            consumo_agua = min(cliente.agua, self.consumo_agua[cliente.tipo][ejercicio])
            cliente.agua -= consumo_agua
            if cliente.agua == 0:
                self.buscar_agua(cliente)
        
    def buscar_agua(self, cliente):
        # Creo que falta los casos en que cierre
        distancia = self.distancia(self.cords_celda(cliente.celda), self.cords_celda(48))
        velocidad = self.velocidad[cliente.tipo]()
        yield self.env.timeout(distancia/velocidad) 
        cliente.celda = 48
        if self.bidon_agua.level == 0:
            if self.dict_datos_estado['pedir_agua'][0] == False:
                self.dict_datos_estado['pedir_agua'][0] = True
                self.env.process(self.reposicion_agua(1))
        cliente.agua += self.bidon_agua.get(min(self.bidon_agua.level, self.info_perfil_t8[cliente.tipo][2]))
        yield self.env.timeout(0.75)
        

    def buscar_toallas(self, cliente):
        # Creo que falta los casos en que cierre
        distancia = self.distancia(self.cords_celda(cliente.celda), self.cords_celda(44))
        velocidad = self.velocidad[cliente.tipo]()
        tiempo_cierre = (900 - self.env.now()) if (900 - self.env.now()) else 0
        tiempo_cierre = self.env.timeout(tiempo_cierre)
        # Poner lo de 900
        yield self.env.timeout(distancia/velocidad) | tiempo_cierre
        if tiempo_cierre.triggered:
            cliente.se_va = True
            return 

        cliente.celda = 44
        if len(self.dispensador_toallas.items) == 0:
            if self.dict_datos_estado['pedir_toallas'][0] == False:
                self.dict_datos_estado['pedir_toallas'][0] = True
                self.env.process(self.reposicion_toallas(1))
        # Puede generar error, revisar
        # Puede generar error, revisar
        # Puede generar error, revisar
        # Puede generar error, revisar
        # Puede generar error, revisar
        with self.dispensador_acceso.request() as pedir_toallas:
            yield pedir_toallas
            for toalla in range(min(2, len(self.dispensador_toallas.items))):
                cliente.toallas += self.dispensador_toallas.get()
            yield self.env.timeout(0.75)

    def inpeccion_agua(self):
        # Se debe definir un criterio de parada
        tiempo_agua = 35
        while tiempo_agua < 900:
            # Son 35 minutos
            yield self.env.timeout(tiempo_agua)
            tiempo_agua += 35
            if self.recepcionista.count < 2:
                if self.bidon_agua.level < 5:
                    if self.dict_datos_estado['pedir_agua'][0] == False:
                        self.dict_datos_estado['pedir_agua'][0] = True
                        self.env.process(self.reposicion_agua(3))
    

    def reposicion_agua(self, prioridad):
        pedir_recepsionista = self.recepcionistas.request(priority=prioridad)
        yield pedir_recepsionista
        distancia = self.distancia(self.cords_celda(7), self.cords_celda(48))
        velocidad = self.velocidad['R']()
        yield self.env.timeout(distancia/velocidad)
        tiempo_reponer_agua = self.tiempo_reposicion['Agua']()
        yield self.env.timeout(tiempo_reponer_agua)
        # Da lo mismo la cantidad, siempre pone el maximo
        self.bidon_agua.put(20)
        distancia = self.distancia(self.cords_celda(48), self.cords_celda(7))
        velocidad = self.velocidad['R']()
        yield self.env.timeout(distancia/velocidad)
        self.recepcionistas.release(pedir_recepsionista)

    def inpeccion_toallas(self):
            tiempo_toallas = 45
            # Verificar 900
            while tiempo_toallas < 900:
                # Son 45 minutos
                yield self.env.timeout(tiempo_toallas)
                tiempo_toallas += 45
                if self.recepcionista.count < 2:
                    if len(self.dispensador_toallas.items) < 30:
                        if self.dict_datos_estado['pedir_toallas'][0] == False:
                            self.dict_datos_estado['pedir_toallas'][0] = True
                            self.env.process(self.reposicion_toallas(3))
    def reposicion_toallas(self, prioridad):

        pedir_recepsionista = self.recepcionistas.request(priority=prioridad)
        yield pedir_recepsionista
        distancia = self.distancia(self.cords_celda(7), self.cords_celda(44))
        velocidad = self.velocidad['R']()
        yield self.env.timeout(distancia/velocidad)
        tiempo_reponer_toallas = self.tiempo_reposicion['Toallas']()
        yield self.env.timeout(tiempo_reponer_toallas)
        toallas_reponer = 100 - len(self.dispensador_toallas.items)
        for toalla in range(toallas_reponer):
            self.dispensador_toallas.put(1)
        distancia = self.distancia(self.cords_celda(44), self.cords_celda(7))
        velocidad = self.velocidad['R']()
        self.recepcionistas.release(pedir_recepsionista)




    def reparar_maquina(self, maquina):
        
        with self.tecnico.request() as pedir_tecnico:
            yield pedir_tecnico
            distancia = self.distancia(self.cords_celda(self.dict_datos_estado['celda_tecnico']), self.cords_celda(maquina.celda))
            velocidad = self.velocidad['M']
            yield self.env.timeout(distancia/velocidad)
            g_reparacio = self.g_reparacion[maquina.nombre]
            tiempo_reparacion = self.tiempo_reparacion[g_reparacio]()
            yield self.env.timeout(tiempo_reparacion)
            maquina.operativa = True


    def salida_cliente(self, cliente):
        pass
   


    def elegir_maquina_cercana_menor_cola(self, cliente, lista_maquinas):
        maquina_cercana_con_cola = lista_maquinas[0]
        maquina_cercana_sin_cola = lista_maquinas[0]
        distancia_maquina_cercana_con_cola = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[maquina_cercana_con_cola.celda])
        distancia_maquina_cercana_sin_cola  = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[maquina_cercana_sin_cola .celda])
        for maquina in lista_maquinas:
            if maquina.operativa == True:
                distancia = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[maquina.celda])
                if maquina.libre == False:
                    if distancia_maquina_cercana_con_cola > distancia:
                        maquina_cercana_con_cola = maquina
                        distancia_maquina_cercana_con_cola = distancia
                    elif distancia_maquina_cercana_con_cola == distancia:
                        if len(maquina_cercana_con_cola.maquina_recurso.queue) > len(maquina.maquina_recurso.queue):
                            maquina_cercana_con_cola = maquina
                            distancia_maquina_cercana_con_cola = distancia
                        elif len(maquina_cercana_con_cola.maquina_recurso.queue) == len(maquina.maquina_recurso.queue):
                            if maquina_cercana_con_cola.celda > maquina.celda:
                                maquina_cercana_con_cola = maquina
                                distancia_maquina_cercana_con_cola = distancia
                else:
                    if distancia_maquina_cercana_sin_cola > distancia:
                        maquina_cercana_sin_cola = maquina
                        distancia_maquina_cercana_sin_cola = distancia
                    elif distancia_maquina_cercana_sin_cola == distancia:
                        if maquina_cercana_sin_cola.celda > maquina.celda:
                            maquina_cercana_sin_cola = maquina
                            distancia_maquina_cercana_sin_cola = distancia
        hay_maquina_operativa = False
        hay_maquina_sin_cola = False
        if maquina_cercana_con_cola.operativa == True or maquina_cercana_sin_cola.operativa == True:
            hay_maquina_operativa = True
            if maquina_cercana_sin_cola.libre == True and maquina_cercana_sin_cola.operativa == True:
                hay_maquina_sin_cola = True
        # El return es [hay maquina operativa?, hay maquina sin cola, [maquina con cola cercana, distancia], [maquina sin cola cercana, distancia]]
        return [hay_maquina_operativa, hay_maquina_sin_cola, [maquina_cercana_sin_cola, distancia_maquina_cercana_sin_cola], 
                [maquina_cercana_con_cola, distancia_maquina_cercana_con_cola]]
    def seleccionar_ejercicio_flexible(self, cliente, ejercicio_ban):
        list_maquinas = []
        maquina_elegida = ''
        distancia_maquina = ''
        for ejercicio in cliente.rutina:
            if ejercicio[0] !=  ejercicio_ban:
                list_maquinas.append([ejercicio, self.elegir_maquina_cercana_menor_cola(cliente, ejercicio)])
        for maquina in list_maquinas:
            if maquina['a']:
                pass
        
