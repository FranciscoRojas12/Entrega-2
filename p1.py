import simpy
import numpy as np
import scipy.stats as st
from clases_funciones import Maquina, Cliente, simular_ppnh_tramos, generar_lista_cliente, elegir_rutina
import os

class Simulacion:
    def __init__(self, archivo):
        self.archivo = archivo
        self.dict_datos_replica = {}
        self.cords_celda = {}
        for celda in range(1, 50):
            fila = (celda - 1) // 7
            col = 6 - ((celda - 1) % 7)
            self.cords_celda[celda] = (col, fila)
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
            'E' : lambda: self.generar_mezcla(0.85, st.gamma.rvs(a=10, scale=0.16, random_state=self.rng), st.lognorm.rvs(s=0.22, scale=np.exp(1.05), random_state=self.rng)),
            'X' : lambda: min(2.2, st.lognorm.rvs(s=0.28, scale=np.exp(0.05), random_state=self.rng)),
            'F' : lambda: self.generar_mezcla(0.85, st.gamma.rvs(a=10, scale=0.16, random_state=self.rng), st.lognorm.rvs(s=0.22, scale=np.exp(1.05), random_state=self.rng)),
            'I' : lambda: self.generar_mezcla(0.75, st.gamma.rvs(a=9, scale=0.25, random_state=self.rng), st.lognorm.rvs(s=0.20, scale=np.exp(1.25), random_state=self.rng))}
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
        self.insatisfaccion = {
            'E': {'R': 0.45, 'W': 0.35, 'C': 0.10, 'S': 0.10},
            'X': {'R': 0.30, 'W': 0.55, 'C': 0.05, 'S': 0.10},
            'F': {'R': 0.35, 'W': 0.40, 'C': 0.10, 'S': 0.15},
            'I': {'R': 0.60, 'W': 0.20, 'C': 0.05, 'S': 0.15}}
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
            'F': lambda: self.generar_mezcla(0.75, st.gamma.rvs(a=12, scale=1.2, random_state=self.rng), st.lognorm.rvs(s=0.18, scale=np.exp(3), random_state=self.rng)),
            'I': lambda: self.generar_mezcla(0.7, st.gamma.rvs(a=10, scale=2.3, random_state=self.rng), st.lognorm.rvs(s=0.2, scale=np.exp(3.55), random_state=self.rng))}
        self.tiempo_reparacion = {
            'G1': lambda: min(50, st.gamma.rvs(a = 7, scale = 5, random_state=self.rng)),
            'G2': lambda: self.generar_mezcla(0.75, st.gamma.rvs(a=12, scale=1.35, random_state=self.rng), st.lognorm.rvs(s=0.18, scale=np.exp(3.55), random_state=self.rng)),
            'G3': lambda: min(48, st.fisk.rvs(c=4.2, scale=20.5, random_state=self.rng)),
            'G4': lambda: self.generar_mezcla(0.65, st.gamma.rvs(a=12, scale=2.1, random_state=self.rng), st.lognorm.rvs(s=0.16, scale=np.exp(3.7), random_state=self.rng)),
            'G5': lambda: min(55, self.generar_mezcla(0.7, st.weibull_min.rvs(c = 4, scale = 21, loc = 0, random_state=self.rng), st.lognorm.rvs(s=0.2, scale=np.exp(3.55), random_state=self.rng)))}
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
            Maquina(self.env, 'Remo sentado', 'Jalon', 29)]
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

            self.entrenadores.put([f'PT{entrenador}', 25, self.velocidad['PT']()])
        self.dispensador_acceso = simpy.Resource(self.env, capacity=1)
        self.dispensador_toallas = simpy.Store(self.env, capacity= 100)
        for toalla in range(100):
            self.dispensador_toallas.put(1)
        self.bidon_acceso = simpy.Resource(self.env, capacity=1)
        self.bidon_agua = simpy.Container(self.env, capacity = 20, init = 20)
        self.bido_reposicion = simpy.Event(self.env)
        self.bido_reposicion.succeed()
        self.dispensador_reposicion = simpy.Event(self.env)
        self.dispensador_reposicion.succeed()

    def generar_mezcla(self, peso_a, distribucion_a, distribucion_b):
        u = self.rng.random()
        if u < peso_a:
            return distribucion_a
        else:
            return distribucion_b
        
    def distancia(self, coordenadas_a, coordenadas_b):
        return (0.7 * (abs(coordenadas_a[0] - coordenadas_b[0]) + abs(coordenadas_a[1] - coordenadas_b[1])) + 0.3 
                * (np.sqrt((coordenadas_a[0] - coordenadas_b[0])**2 + (coordenadas_a[1]- coordenadas_b[1])**2))) * 2.5
    
    def iniciar_simulacion(self, seed, n_replicas, misma_semilla = False):
        for replica in range(n_replicas):
            if misma_semilla:
                self.rng = np.random.default_rng(seed)
            else:
                self.rng = np.random.default_rng(seed + replica)
            self.simular_una_replica(replica)

    def simular_una_replica(self, id_replica):
        Cliente.id = 0 
        self.dict_pedir_maquina = {}
        self.env = simpy.Environment()
        self.generar_recursos()
        # Permanencia: Obtener promedio y el percentil 90
        # Espera total calcular propmedio y el percentil 90
        # Finalizacion de rutinas completaron_rutina/clientes_admitidos
        # cumplimiento de ejercicio = n_ejercicio_completo/n_ejercicio_planificados
        # Finalizacion de cardio n_completaron_cardio/n_planificaron_cardio
        # insatisfaccion de admitidos: sum('insatisfaccion_admintidos')/'clientes_admitidos'


        self.dict_info_recolectada = {'int_llegada': 0, 'cliente_desviado': 0, 'n_fallas': 0, 'permanencia': [], 'espera_total': [],
                                      'n_ejercicio_completo': 0, 'n_ejercicio_planificados': 0, 'clientes_admitidos': 0, 'completaron_rutina': 0,
                                      'n_planificaron_cardio': 0, 'n_completaron_cardio': 0, 'n_ejercicios_omitidos': 0, 'n_ejercicios_pendientes': 0,
                                      'insatisfaccion_admintidos': []}

        self.dict_datos_estado = {'n_clientes_sistema': 0, 'pedir_agua' : False, 'pedir_toallas': False, 'celda_tecnico': 7,
                                  'velocidad_mecanico': self.velocidad['M'](), 'velocidad_recepcionista': [self.velocidad['R'](), self.velocidad['R']()]}
        self.env.process(self.inpeccion_agua())
        self.env.process(self.inpeccion_toallas())
        self.env.process(self.generar_cliente())
        self.env.run()
        self.dict_datos_replica[id_replica] = [self.dict_info_recolectada, self.dict_datos_estado]

    def generar_cliente(self):
        lista_clientes = generar_lista_cliente(self.rng, simular_ppnh_tramos(self.rng, True))
        for cliente_llegada in lista_clientes:
            tipo = cliente_llegada[1]
            cliente = Cliente(tipo, self.info_perfil_t8[tipo][2], 2, self.info_perfil_t8[tipo][0])
            yield self.env.timeout(cliente_llegada[0] - self.env.now)
            self.env.process(self.llegada_clientes(cliente))

    def llegada_clientes(self, cliente):
        self.dict_info_recolectada['int_llegada'] += 1
        
        if self.dict_datos_estado['n_clientes_sistema'] >= 30:
            self.dict_info_recolectada['cliente_desviado'] += 1
            cliente.se_va = True
        else:
            cliente.admitido = True
   
            self.dict_datos_estado['n_clientes_sistema'] +=1 
            self.dict_info_recolectada['clientes_admitidos'] += 1

            cliente.hora_llegada = self.env.now

            cliente.velocidad = self.velocidad[cliente.tipo]()

            distancia = self.distancia(self.cords_celda[1], self.cords_celda[7])
            yield self.env.timeout(distancia / cliente.velocidad)
            cliente.celda = 7

            inicio_espera = self.env.now

            pedir_recepcionista = self.recepcionistas.request(priority= 2)

            tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
            tiempo_restante = self.env.timeout(tiempo_restante)

            tiempo_cierre = max(900 - self.env.now, 0)
            tiempo_cierre = self.env.timeout(tiempo_cierre)

            yield pedir_recepcionista | tiempo_restante | tiempo_cierre
            cliente.espera_recepcion += self.env.now - inicio_espera

            if tiempo_restante.processed or tiempo_cierre.processed:
                cliente.se_va = True
                pedir_recepcionista.cancel()

            else:

                tiempo_registro = self.tiempo_registro[cliente.tipo]()
                yield self.env.timeout(tiempo_registro)

                seleccionar_rutina = self.rutinas_opciones[cliente.tipo]()
                if cliente.tipo == 'F':
                    desglose_rutina = self.orden_ejecucion_rutina['I'][seleccionar_rutina]
                else:
                    desglose_rutina = self.orden_ejecucion_rutina[cliente.tipo][seleccionar_rutina]

                rutina = elegir_rutina(seleccionar_rutina, desglose_rutina, self.rng)

                p_p = self.agregar_polea[cliente.tipo][seleccionar_rutina]
                hacer_polea = st.bernoulli.rvs(p = p_p, random_state=self.rng)
                if hacer_polea == 1:
                    rutina += [['Polea multifuncional', 'pen']]
                
                cliente.rutina = rutina
                cliente.tiempo_acumulado = [self.info_perfil_t8[cliente.tipo][1] for i in range(len(cliente.rutina))]
                cliente.tiempo_acumulado_cardio = self.info_perfil_t8[cliente.tipo][1]

                p_c = self.info_perfil_t8[cliente.tipo][3]
                hacer_cardio = st.bernoulli.rvs(p = p_c, random_state=self.rng)
                if hacer_cardio == 1:
                    cliente.plan_cardio = True
                else:
                    cliente.plan_cardio = False

                self.recepcionistas.release(pedir_recepcionista)

                distancia = self.distancia(self.cords_celda[6], self.cords_celda[13])
                desplazamiento = self.env.timeout(distancia / cliente.velocidad)

                tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(900 - self.env.now, 0)
                tiempo_cierre = self.env.timeout(tiempo_cierre)

                yield desplazamiento | tiempo_restante | tiempo_cierre

                if tiempo_restante.processed or tiempo_cierre.processed:
                    cliente.se_va = True
                else:
                    cliente.celda = 13
                
            if cliente.se_va == True:
                self.env.process(self.salida_cliente(cliente))
            else:
                self.env.process(self.rutina_fuerza(cliente))

    def rutina_fuerza(self, cliente):
        if cliente.tipo == 'E':

            for recorrido in range(1, 3):
                if cliente.se_va == True:
                    break
                if recorrido == 2:
                    cliente.tiempo_acumulado = [self.info_perfil_t8[cliente.tipo][1] for i in range(len(cliente.rutina))]
                for indice_ejercicio in range(len(cliente.rutina)):

                    if cliente.se_va == True:
                        break

                    if cliente.toallas < 1:
                        yield self.env.process(self.buscar_toallas(cliente))

                    if cliente.rutina[indice_ejercicio][1] == 'pen':
                        while True:
                            if cliente.se_va == True:
                                break

                            list_maquinas = self.dict_maquinas[cliente.rutina[indice_ejercicio][0]]
                            list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, list_maquinas)

                            if list_respuesta[0] == True:
                                
                                list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                                
                                desplazamiento = self.env.timeout(list_maquina_sel[1]/ cliente.velocidad)

                                tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                                tiempo_restante = self.env.timeout(tiempo_restante)

                                tiempo_cierre = max(900 - self.env.now, 0)
                                tiempo_cierre = self.env.timeout(tiempo_cierre)

                                yield desplazamiento | tiempo_restante | tiempo_cierre

                                if tiempo_restante.processed == True or tiempo_cierre.processed == True:
                                    cliente.se_va = True
                                    break
                                else:
                                    cliente.celda = list_maquina_sel[0].celda
                                    if list_maquina_sel[0].operativa == True:
                                        yield self.env.process(self.ejecutar_ejercicio_fuerza(cliente, list_maquina_sel[0], indice_ejercicio))
                                        if cliente.rutina[indice_ejercicio][1] == 'pen':
                                            if cliente.fallo_maquina == False:
                                                if recorrido == 2:
                                                    cliente.rutina[indice_ejercicio][1] = 'omit'
                                                break
                                        elif cliente.rutina[indice_ejercicio][1] == 'compl':
                                            break
                            else:
                                # Aqui pasa cuando no hay maquinas operativas
                                # No esta muy claro el enunciado, pero propongo dos camninos
                                # Camino 1, solo pasa el ejercicio y lo deja como pendiente

                                #break

                                # Camino 2, espera hasta que encuentre una maquina opertativa (espera reparacion)
                                # Igual es un poco raro el tiempo_max_espera, porque el enunciado no dice que espera tau por la reparacion

                                eventos_reparacion = [maq.evento for maq in list_maquinas]
                                eventos_reparacion = simpy.AnyOf(self.env, eventos_reparacion)

                                tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                                tiempo_restante = self.env.timeout(tiempo_restante)

                                tiempo_cierre = max(900 - self.env.now, 0)
                                tiempo_cierre = self.env.timeout(tiempo_cierre)


                                tiempo_max_espera = self.env.timeout(cliente.tiempo_acumulado[indice_ejercicio])

                                yield eventos_reparacion | tiempo_restante | tiempo_cierre | tiempo_max_espera

                                if tiempo_restante.processed or tiempo_cierre.processed:
                                    cliente.se_va = True
                                    break

                                elif tiempo_max_espera.processed:
                                    if recorrido == 2:
                                        cliente.rutina[indice_ejercicio][1] = 'omit'
                                        break
                              
        elif cliente.tipo == 'X':
            for indice_ejercicio in range(len(cliente.rutina)):
                if cliente.se_va == True:
                    break
                if cliente.toallas < 1:
                    yield self.env.process(self.buscar_toallas(cliente))
                if cliente.rutina[indice_ejercicio][1] == 'pen':
                    while True:
                        if cliente.se_va == True:
                            break
                        list_maquinas = self.dict_maquinas[cliente.rutina[indice_ejercicio][0]]
                        list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, list_maquinas)
                        if list_respuesta[0] == True:
                            list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]

                            desplazamiento = self.env.timeout(list_maquina_sel[1]/ cliente.velocidad)

                            tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                            tiempo_restante = self.env.timeout(tiempo_restante)

                            tiempo_cierre = max(900 - self.env.now, 0)
                            tiempo_cierre = self.env.timeout(tiempo_cierre)

                            yield desplazamiento | tiempo_restante | tiempo_cierre

                            if tiempo_restante.processed or tiempo_cierre.processed:
                                cliente.se_va = True
                                break
                            else:
                                cliente.celda = list_maquina_sel[0].celda
                                yield self.env.process(self.ejecutar_ejercicio_fuerza(cliente, list_maquina_sel[0], indice_ejercicio))
                                if cliente.rutina[indice_ejercicio][1] == 'compl' or cliente.rutina[indice_ejercicio][1] == 'omit':
                                    break
                        else:
                            cliente.rutina[indice_ejercicio][1] = 'omit'
                            break

        elif cliente.tipo == 'I':
            for indice_ejercicio in range(len(cliente.rutina)):
                if cliente.se_va == True:
                    break
                if cliente.toallas < 1:
                    yield self.env.process(self.buscar_toallas(cliente))
                list_maquinas = self.dict_maquinas[cliente.rutina[indice_ejercicio][0]]
                while True:
                    if cliente.se_va == True:
                        break
                    list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, list_maquinas)
                    if list_respuesta[0] == True:
                        list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]

                        desplazamiento = self.env.timeout(list_maquina_sel[1]/ cliente.velocidad)

                        tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                        tiempo_restante = self.env.timeout(tiempo_restante)

                        tiempo_cierre = max(900 - self.env.now, 0)
                        tiempo_cierre = self.env.timeout(tiempo_cierre)

                        yield desplazamiento | tiempo_restante | tiempo_cierre

                        if tiempo_restante.processed or tiempo_cierre.processed:
                            cliente.se_va = True
                            break
                        else:
                            cliente.celda = list_maquina_sel[0].celda
                            yield self.env.process(self.ejecutar_ejercicio_fuerza(cliente, list_maquina_sel[0], indice_ejercicio))
                            if cliente.rutina[indice_ejercicio][1] == 'compl':
                                break
                    else:

                        eventos_reparacion = [maq.evento for maq in list_maquinas]
                        eventos_reparacion = simpy.AnyOf(self.env, eventos_reparacion)

                        tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                        tiempo_restante = self.env.timeout(tiempo_restante)

                        tiempo_cierre = max(900 - self.env.now, 0)
                        tiempo_cierre = self.env.timeout(tiempo_cierre)

                        yield eventos_reparacion | tiempo_restante | tiempo_cierre
                        
                        if tiempo_restante.processed or tiempo_cierre.processed:
                            cliente.se_va = True
                            break

        elif cliente.tipo == 'F':
            while True:
                if cliente.se_va == True:
                    break
                seguir_rutina = False
                for ejercicio in cliente.rutina:
                    if ejercicio[1] == 'pen':
                        seguir_rutina = True
                if seguir_rutina == False:
                    break
                elif cliente.toallas < 1:
                    yield self.env.process(self.buscar_toallas(cliente))
                else:
                    maquina_selec, distacia_selec, no_tiene_cola, eventos_reparacion, indice_ejercicio = self.seleccion_maquina_flex(cliente, True)
                    if maquina_selec == None and len(eventos_reparacion) != 0:
                        eventos_reparacion = simpy.AnyOf(self.env, eventos_reparacion)

                        tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                        tiempo_restante = self.env.timeout(tiempo_restante)

                        tiempo_cierre = max(900 - self.env.now, 0)
                        tiempo_cierre = self.env.timeout(tiempo_cierre)
                        yield eventos_reparacion | tiempo_restante | tiempo_cierre

                        if tiempo_restante.processed or tiempo_cierre.processed:
                            cliente.se_va = True
                            break
                    elif maquina_selec == None:

                        maquina_selec, distacia_selec, no_tiene_cola, eventos_reparacion, indice_ejercicio = self.seleccion_maquina_flex(cliente, False)
                        if no_tiene_cola == False:
                            cliente.se_va = True
                            break
                        else:
                            if maquina_selec != None:
                                desplazamiento = self.env.timeout(distacia_selec/ cliente.velocidad)

                                tiempo_cierre = max(900 - self.env.now, 0)
                                tiempo_cierre = self.env.timeout(tiempo_cierre)

                                tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                                tiempo_restante = self.env.timeout(tiempo_restante)

                                yield desplazamiento | tiempo_restante | tiempo_cierre

                                if tiempo_restante.processed or tiempo_cierre.processed:
                                    cliente.se_va = True
                                    break
                                else:
                                    cliente.celda = maquina_selec.celda
                                    if maquina_selec.operativa == True:
                                        yield self.env.process(self.ejecutar_ejercicio_fuerza(cliente, maquina_selec, indice_ejercicio))

                    else:
                        desplazamiento = self.env.timeout(distacia_selec/ cliente.velocidad)

                        tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
                        tiempo_restante = self.env.timeout(tiempo_restante)

                        tiempo_cierre = max(900 - self.env.now, 0)
                        tiempo_cierre = self.env.timeout(tiempo_cierre)

                        yield desplazamiento | tiempo_restante | tiempo_cierre

                        if tiempo_restante.processed or tiempo_cierre.processed:
                            cliente.se_va = True
                            break
                        else:
                            cliente.celda = maquina_selec.celda
                            if maquina_selec.operativa == True:
                                yield self.env.process(self.ejecutar_ejercicio_fuerza(cliente, maquina_selec, indice_ejercicio))

        if cliente.se_va == False and cliente.plan_cardio == True:
            self.env.process(self.ejecutar_cardio(cliente))
        else:
            self.env.process(self.salida_cliente(cliente))

    def ejecutar_ejercicio_fuerza(self, cliente, maquina, indice_ejercicio):
        cliente.fallo_maquina = False
        cliente.seguir_ejercicio = True
        inicio_espera = self.env.now

        self.dict_pedir_maquina[cliente.id] = self.env.process(self.pedir_maquina(cliente, maquina, indice_ejercicio, inicio_espera))
        maquina.list_id_cliente.append(cliente.id)

        yield self.dict_pedir_maquina[cliente.id]

        del self.dict_pedir_maquina[cliente.id]
        maquina.list_id_cliente.remove(cliente.id)

        if cliente.seguir_ejercicio == True:
            maquina.libre = False

            p_entrenador = self.entrenador_asistencia[cliente.tipo][maquina.nombre]
            nececita_entrenador = st.bernoulli.rvs(p=p_entrenador, random_state=self.rng)

            if nececita_entrenador == 1:
                tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0) 
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(900 - self.env.now, 0)
                tiempo_cierre = self.env.timeout(tiempo_cierre)

                pedir_entrenador = self.entrenadores.get()

                inicio_espera = self.env.now
                respuesta = yield pedir_entrenador | tiempo_restante | tiempo_cierre
                cliente.espera_asistente += self.env.now - inicio_espera

                if tiempo_restante.processed or tiempo_cierre.processed:
                    if pedir_entrenador.triggered:
                        self.entrenadores.put(pedir_entrenador.value)
                    else:
                        pedir_entrenador.cancel()
                    cliente.seguir_ejercicio = False
                    maquina.maquina_recurso.release(cliente.pedir_maquina)
                    maquina.libre = True
                    cliente.se_va = True
                else:
                    pedir_entrenador = respuesta[pedir_entrenador]

                    tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0) 
                    tiempo_restante = self.env.timeout(tiempo_restante)

                    tiempo_cierre = max(900 - self.env.now, 0)
                    tiempo_cierre = self.env.timeout(tiempo_cierre)

                    id_entrenador = pedir_entrenador[0]
                    distancia = self.distancia(self.cords_celda[pedir_entrenador[1]], self.cords_celda[cliente.celda])
                    desplazamiento = self.env.timeout(distancia / pedir_entrenador[2])  

                    yield desplazamiento | tiempo_restante | tiempo_cierre
                    
                    if tiempo_restante.processed or tiempo_cierre.processed:
                        cliente.seguir_ejercicio = False
                        maquina.maquina_recurso.release(cliente.pedir_maquina)
                        self.entrenadores.put([id_entrenador, pedir_entrenador[1], pedir_entrenador[2]])
                        cliente.se_va = True

            if cliente.seguir_ejercicio == True:
                g_maquina = self.g_dur_ejer_fuerza[maquina.nombre]
                tiempo_maquina = self.dur_ejer_fuerza[cliente.tipo][g_maquina]()
                yield self.env.timeout(tiempo_maquina)

                cliente.rutina[indice_ejercicio][1] = 'compl'

                p_falla = self.probabilidad_falla[maquina.nombre]
                falla_maquina = st.bernoulli.rvs(p=p_falla, random_state=self.rng)

                if falla_maquina == 1:

                    maquina.operativa = False
                    self.dict_info_recolectada['n_fallas'] += 1

                    for id, proceso in list(self.dict_pedir_maquina.items()):
                        if id in maquina.list_id_cliente and proceso.is_alive:
                            proceso.interrupt('Fallo la maquina')
                            
                    maquina.maquina_recurso.release(cliente.pedir_maquina)
                    self.env.process(self.reparar_maquina(maquina))
                else:
                    maquina.libre = True
                    maquina.maquina_recurso.release(cliente.pedir_maquina)

                if nececita_entrenador == 1: 
                    self.entrenadores.put([id_entrenador, cliente.celda, pedir_entrenador[2]])
                consumo_agua = min(cliente.agua, self.consumo_agua[cliente.tipo][maquina.categoria]())
                cliente.agua -= consumo_agua
                cliente.toallas -= 1
                if cliente.agua == 0:
                    yield self.env.process(self.buscar_agua(cliente))

    def pedir_maquina(self, cliente, maquina, indice_ejercicio, inicio_espera, maquina_cardio = False):
        try:
            tiempo_restante = max(self.info_perfil_t8[cliente.tipo][0]  - (self.env.now - cliente.hora_llegada), 0)
            tiempo_restante = self.env.timeout(tiempo_restante)

            pedir_maquina = maquina.maquina_recurso.request()
            cliente.pedir_maquina = pedir_maquina

            tiempo_max = cliente.tiempo_acumulado[indice_ejercicio] if maquina_cardio == False else cliente.tiempo_acumulado_cardio
            tiempo_max_espera = self.env.timeout(tiempo_max) 

            tiempo_cierre = max(900 - self.env.now, 0)
            tiempo_cierre = self.env.timeout(tiempo_cierre)

            yield pedir_maquina | tiempo_max_espera | tiempo_restante | tiempo_cierre
            if maquina_cardio == True:
                cliente.espera_cardio += self.env.now - inicio_espera
                if (not pedir_maquina.triggered) and (tiempo_max_espera.processed or tiempo_restante.processed or tiempo_cierre.processed):
                    pedir_maquina.cancel()
                    cliente.seguir_ejercicio = False
                    cliente.se_va = True
            else:
                cliente.espera_fuerza += self.env.now - inicio_espera

                if pedir_maquina.triggered:
                    pass
                elif tiempo_max_espera.processed == True:
                    if cliente.tipo == 'F':
                        cliente.tiempo_acumulado[indice_ejercicio] = 0
                    elif cliente.tipo == 'X':
                        cliente.rutina[indice_ejercicio][1] = 'omit'
                    pedir_maquina.cancel()
                    cliente.seguir_ejercicio = False

                elif tiempo_restante.processed == True or tiempo_cierre.processed == True:
                    cliente.se_va = True
                    cliente.seguir_ejercicio= False
                    pedir_maquina.cancel()
                
        except simpy.Interrupt as interrupcion:
            cliente.fallo_maquina = True
            cliente.seguir_ejercicio = False
            if pedir_maquina.triggered:
                maquina.maquina_recurso.release(pedir_maquina)
            else:
                pedir_maquina.cancel()
            if maquina_cardio == True:
                cliente.espera_cardio += self.env.now - inicio_espera
                cliente.tiempo_acumulado_cardio = max(0,cliente.tiempo_acumulado_cardio - (self.env.now - inicio_espera))
            else:
                cliente.espera_fuerza += self.env.now - inicio_espera
                cliente.tiempo_acumulado[indice_ejercicio] = max(0, cliente.tiempo_acumulado[indice_ejercicio] - (self.env.now - inicio_espera))


    def ejecutar_cardio(self, cliente):
        while True:

            if cliente.se_va == True:
                break

            list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, self.dict_maquinas['Trotadora'])
            
            if list_respuesta[0] == True:
                cliente.seguir_ejercicio = True
                list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                desplazamiento = self.env.timeout(list_maquina_sel[1]/ cliente.velocidad)
                
                tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(0, 900 - self.env.now)
                tiempo_cierre = self.env.timeout(tiempo_cierre)

                yield desplazamiento | tiempo_restante | tiempo_cierre

                if tiempo_restante.processed or tiempo_cierre.processed:
                    cliente.se_va = True
                    break

                elif list_maquina_sel[0].operativa != False:

                    inicio_espera = self.env.now

                    self.dict_pedir_maquina[cliente.id] = self.env.process(self.pedir_maquina(cliente, list_maquina_sel[0], 0, inicio_espera, True))
                    list_maquina_sel[0].list_id_cliente.append(cliente.id)
                
                    yield self.dict_pedir_maquina[cliente.id]

                    del self.dict_pedir_maquina[cliente.id]
                    list_maquina_sel[0].list_id_cliente.remove(cliente.id)

                    if cliente.se_va == False and cliente.seguir_ejercicio == True:
                        tiempo_cardio = self.env.timeout(self.dur_ejer_cardio[cliente.tipo]())
                        yield tiempo_cardio

                        cliente.cardio_completado = True

                        p_falla = self.probabilidad_falla['Trotadora']
                        falla_maquina = st.bernoulli.rvs(p=p_falla, random_state=self.rng)

                        if falla_maquina == 1:
                            list_maquina_sel[0].operativa = False
                            self.dict_info_recolectada['n_fallas'] += 1

                            for id, proceso in list(self.dict_pedir_maquina.items()):
                                if id in list_maquina_sel[0].list_id_cliente and proceso.is_alive:
                                    proceso.interrupt('Fallo la maquina')

                            list_maquina_sel[0].maquina_recurso.release(cliente.pedir_maquina)
                            self.env.process(self.reparar_maquina(list_maquina_sel[0]))
                        else:
                            list_maquina_sel[0].maquina_recurso.release(cliente.pedir_maquina)
                        cliente.se_va = True
            else:
                eventos_reparacion = [maq.evento for maq in self.dict_maquinas['Trotadora']]
                eventos_reparacion = simpy.AnyOf(self.env, eventos_reparacion)

                tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(0, 900 - self.env.now)
                tiempo_cierre = self.env.timeout(tiempo_cierre)

                # Puede que sea un error pone el tiempo max espera, el enunciado no es muy claro
                tiempo_max_espera = self.env.timeout(self.info_perfil_t8[cliente.tipo][1]) 

                yield eventos_reparacion | tiempo_restante | tiempo_cierre | tiempo_max_espera

                if tiempo_restante.processed or tiempo_cierre.processed or tiempo_max_espera.processed:
                    cliente.se_va = True
                
        self.env.process(self.salida_cliente(cliente))

    def salida_cliente(self, cliente):
        if cliente.celda != 13:
            distancia = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[13])
            yield self.env.timeout(distancia / cliente.velocidad)
            cliente.celda = 13
        distancia = self.distancia(self.cords_celda[13], self.cords_celda[6])
        yield self.env.timeout(distancia / cliente.velocidad)
        cliente.celda = 6
        distancia = self.distancia(self.cords_celda[6], self.cords_celda[1])
        yield self.env.timeout(distancia/ cliente.velocidad)
        cliente.celda = 1

        n_pendientes, n_omitidos = cliente.n_ejercicios_pendientes_omitidos()
        self.dict_info_recolectada['n_ejercicios_omitidos'] += n_omitidos
        self.dict_info_recolectada['n_ejercicios_pendientes'] += n_pendientes

        if cliente.plan_cardio == True:
            self.dict_info_recolectada['n_planificaron_cardio'] += 1
            self.dict_info_recolectada['n_completaron_cardio'] += 1 if cliente.cardio_completado == True else 0

        n_ejercicio_completo, n_ejercicio_planificados = cliente.cumplimento_ejercicio()
        self.dict_info_recolectada['n_ejercicio_completo'] += n_ejercicio_completo
        self.dict_info_recolectada['n_ejercicio_planificados'] += n_ejercicio_planificados

        self.dict_info_recolectada['completaron_rutina'] += 1 if cliente.completo_rutina_fuerza() == True else 0

        self.dict_info_recolectada['espera_total'].append(cliente.espera_agua + cliente.espera_toallas + cliente.espera_asistente + cliente.espera_cardio + cliente.espera_fuerza + cliente.espera_recepcion)
        self.dict_info_recolectada['permanencia'].append(self.env.now - cliente.hora_llegada)

        self.dict_datos_estado['n_clientes_sistema'] -= 1

    
    def buscar_agua(self, cliente):
        distancia = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[48])
        desplazamiento = self.env.timeout(distancia/cliente.velocidad)

        tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
        tiempo_restante = self.env.timeout(tiempo_restante)

        tiempo_cierre = max(0, 900 - self.env.now)
        tiempo_cierre = self.env.timeout(tiempo_cierre)

        yield desplazamiento | tiempo_cierre | tiempo_restante

        if tiempo_cierre.processed or tiempo_restante.processed:
            cliente.se_va = True
        else:
            cliente.celda = 48
            if self.bidon_agua.level == 0:
                if self.dict_datos_estado['pedir_agua'] == False:
                    self.dict_datos_estado['pedir_agua'] = True
                    self.env.process(self.reposicion_agua(1))

            pedir_acceso = self.bidon_acceso.request()

            tiempo_cierre = max(0, 900 - self.env.now)
            tiempo_cierre = self.env.timeout(tiempo_cierre)

            tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
            tiempo_restante_acumulado = tiempo_restante
            tiempo_restante = self.env.timeout(tiempo_restante)

            inicio_espera = self.env.now

            yield pedir_acceso | tiempo_cierre | tiempo_restante
            cliente.espera_agua += self.env.now - inicio_espera
            

            if tiempo_cierre.processed or tiempo_restante.processed:
                cliente.se_va = True
                pedir_acceso.cancel()
            else:
                if self.bidon_agua.level == 0:
                    if self.dict_datos_estado['pedir_agua'] == False:
                        self.dict_datos_estado['pedir_agua'] = True
                        self.bido_reposicion = simpy.Event(self.env)
                        self.env.process(self.reposicion_agua(1))

                tiempo_restante = max(0, tiempo_restante_acumulado - self.env.now)
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(0, 900 - self.env.now)
                tiempo_cierre = self.env.timeout(tiempo_cierre)

                yield self.bido_reposicion | tiempo_cierre | tiempo_restante

                if tiempo_cierre.processed or tiempo_restante.processed:
                    cliente.se_va = True
                else:
                    agua = min(self.bidon_agua.level, self.info_perfil_t8[cliente.tipo][2])
                    yield self.bidon_agua.get(agua)
                    yield self.env.timeout(0.75)
                    cliente.agua += agua
                self.bidon_acceso.release(pedir_acceso)


    def buscar_toallas(self, cliente):
        distancia = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[44])
        desplazamiento = self.env.timeout(distancia/cliente.velocidad)

        tiempo_cierre = max(0, 900 - self.env.now)
        tiempo_cierre = self.env.timeout(tiempo_cierre)

        tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
        tiempo_restante = self.env.timeout(tiempo_restante)

        yield desplazamiento | tiempo_cierre | tiempo_restante
        if tiempo_cierre.processed or tiempo_restante.processed:
            cliente.se_va = True
        else:
            cliente.celda = 44
      
            pedir_acceso = self.dispensador_acceso.request()

            tiempo_cierre = max(0, 900 - self.env.now)
            tiempo_cierre = self.env.timeout(tiempo_cierre)

            tiempo_restante = max(0, self.info_perfil_t8[cliente.tipo][0] - (self.env.now - cliente.hora_llegada))
            tiempo_restante_acumulado = tiempo_restante
            tiempo_restante = self.env.timeout(tiempo_restante)

            inicio_espera = self.env.now

            yield pedir_acceso | tiempo_cierre | tiempo_restante
            cliente.espera_toallas += self.env.now - inicio_espera

            if tiempo_cierre.processed or tiempo_restante.processed:
                cliente.se_va = True
                pedir_acceso.cancel()
            else:
                if len(self.dispensador_toallas.items) == 0:
                    if self.dict_datos_estado['pedir_toallas'] == False:
                        self.dispensador_reposicion = simpy.Event(self.env)
                        self.dict_datos_estado['pedir_toallas'] = True
                        self.env.process(self.reposicion_toallas(1))

                tiempo_restante = max(0, tiempo_restante_acumulado - self.env.now)
                tiempo_restante = self.env.timeout(tiempo_restante)

                tiempo_cierre = max(0, 900 - self.env.now)
                tiempo_cierre = self.env.timeout(tiempo_cierre)
            
                yield self.dispensador_reposicion | tiempo_cierre | tiempo_restante

                if tiempo_cierre.processed or tiempo_restante.processed:
                    cliente.se_va = True
                else:
                    for toalla in range(min(2, len(self.dispensador_toallas.items))):
                        yield self.dispensador_toallas.get()
                        cliente.toallas += 1
                    yield self.env.timeout(0.75)
                self.dispensador_acceso.release(pedir_acceso)

    def inpeccion_agua(self):
        tiempo_agua = 35
        while tiempo_agua < 900:
            yield self.env.timeout(tiempo_agua)
            tiempo_agua += 35
            if self.recepcionistas.count < 2:
                if self.bidon_agua.level < 5:
                    if self.dict_datos_estado['pedir_agua'] == False:
                        self.bido_reposicion = simpy.Event(self.env)
                        self.dict_datos_estado['pedir_agua'] = True
                        self.env.process(self.reposicion_agua(3))

    def inpeccion_toallas(self):
        tiempo_toallas = 45
        while tiempo_toallas < 900:
            yield self.env.timeout(tiempo_toallas)
            tiempo_toallas += 45
            if self.recepcionistas.count < 2:
                if len(self.dispensador_toallas.items) < 30:
                    if self.dict_datos_estado['pedir_toallas'] == False:
                        self.dispensador_reposicion = simpy.Event(self.env)
                        self.dict_datos_estado['pedir_toallas'] = True
                        self.env.process(self.reposicion_toallas(3))

    def reposicion_agua(self, prioridad):
        pedir_recepsionista = self.recepcionistas.request(priority=prioridad)
        yield pedir_recepsionista

        velocidad_r = self.dict_datos_estado['velocidad_recepcionista'][0] if self.recepcionistas.count == 1 else self.dict_datos_estado['velocidad_recepcionista'][1]

        distancia = self.distancia(self.cords_celda[7], self.cords_celda[48])
        yield self.env.timeout(distancia/velocidad_r)

        tiempo_reponer_agua = self.tiempo_reposicion['Agua']()
        yield self.env.timeout(tiempo_reponer_agua)
        reponer = 20 - self.bidon_agua.level
        self.bidon_agua.put(reponer)
        self.bido_reposicion.succeed()
        self.dict_datos_estado['pedir_agua'] = False

        distancia = self.distancia(self.cords_celda[48], self.cords_celda[7])
        yield self.env.timeout(distancia/velocidad_r)

        self.recepcionistas.release(pedir_recepsionista)
        
        

    def reposicion_toallas(self, prioridad):
        pedir_recepsionista = self.recepcionistas.request(priority=prioridad)
        yield pedir_recepsionista

        velocidad_r = self.dict_datos_estado['velocidad_recepcionista'][0] if self.recepcionistas.count == 1 else self.dict_datos_estado['velocidad_recepcionista'][1]

        distancia = self.distancia(self.cords_celda[7], self.cords_celda[44])
        yield self.env.timeout(distancia/velocidad_r)

        tiempo_reponer_toallas = self.tiempo_reposicion['Toallas']()
        yield self.env.timeout(tiempo_reponer_toallas)

        toallas_reponer = 100 - len(self.dispensador_toallas.items)
        for toalla in range(toallas_reponer):
            self.dispensador_toallas.put(1)
        self.dict_datos_estado['pedir_toallas'] = False
        self.dispensador_reposicion.succeed()

        distancia = self.distancia(self.cords_celda[44], self.cords_celda[7])
        velocidad = self.velocidad['R']()
        yield self.env.timeout(distancia/velocidad_r)

        self.recepcionistas.release(pedir_recepsionista)


    def reparar_maquina(self, maquina):        
        with self.tecnico.request() as pedir_tecnico:
            yield pedir_tecnico

            distancia = self.distancia(self.cords_celda[self.dict_datos_estado['celda_tecnico']], self.cords_celda[maquina.celda])
            
            desplazamiento = self.env.timeout(distancia/self.dict_datos_estado['velocidad_mecanico'])

            yield desplazamiento

            self.dict_datos_estado['celda_tecnico'] = maquina.celda

            g_reparacio = self.g_reparacion[maquina.nombre]
            tiempo_reparacion = self.tiempo_reparacion[g_reparacio]()

            yield self.env.timeout(tiempo_reparacion)

            maquina.operativa = True
            maquina.libre = True
            maquina.evento.succeed()
            maquina.evento = simpy.Event(self.env)

            if len(self.tecnico.queue) == 0:
                distancia = self.distancia(self.cords_celda[self.dict_datos_estado['celda_tecnico']], self.cords_celda[7])
                desplazamiento = self.env.timeout(distancia/self.dict_datos_estado['velocidad_mecanico'])
                yield desplazamiento
                self.dict_datos_estado['celda_tecnico'] = 7
                
    def elegir_maquina_cercana_menor_cola(self, cliente, lista_maquinas):
        maquina_cercana_con_cola = lista_maquinas[0]
        maquina_cercana_sin_cola = lista_maquinas[0]
        distancia_maquina_cercana_con_cola = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[maquina_cercana_con_cola.celda])
        distancia_maquina_cercana_sin_cola  = self.distancia(self.cords_celda[cliente.celda], self.cords_celda[maquina_cercana_sin_cola.celda])
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
    def seleccion_maquina_flex(self, cliente, con_ejercicios_antiguos):
        maquina_selec = None
        distacia_selec = None
        no_tiene_cola = False
        eventos_reparacion = []
        indice_ejercicio_sel = 0
        for indice_ejercicio in range(len(cliente.rutina)):
            if cliente.rutina[indice_ejercicio][1] == 'pen' and (con_ejercicios_antiguos == False or cliente.tiempo_acumulado[indice_ejercicio] > 0):
                list_maquinas = self.dict_maquinas[cliente.rutina[indice_ejercicio][0]]
                eventos_reparacion += [maq.evento for maq in list_maquinas]
                list_respuesta = self.elegir_maquina_cercana_menor_cola(cliente, list_maquinas)
                if not list_respuesta[0]:
                    continue   # sin unidades operativas de este tipo: no compararlas
                # ESTE BLOQUE LO QUE HACE ES ESCOGER SEGUN MAQUINA LIBRE -> MAQUINA CERCANA -> MAQUINA CON MENOR NUMERO DE CELDA
                # SI NO HAY MAQUINA SIN COLA: MAQUINA CON MENOS COLA -> MAQUINA CERCANA -> MAQUINA CON MENOR NUMERO DE CELDA
                if maquina_selec == None:
                    if list_respuesta[0] == True:
                        no_tiene_cola = list_respuesta[1] 
                        list_maquina_sel = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                        maquina_selec = list_maquina_sel[0]
                        distacia_selec = list_maquina_sel[1]
                        indice_ejercicio_sel = indice_ejercicio
                else:
                    maquina_evaluada = list_respuesta[2] if list_respuesta[1] == True else list_respuesta[3]
                    if no_tiene_cola == False and list_respuesta[1] == True:
                        maquina_selec = maquina_evaluada[0]
                        distacia_selec = maquina_evaluada[1]
                        indice_ejercicio_sel = indice_ejercicio
                        no_tiene_cola = True 
                    elif no_tiene_cola == True and list_respuesta[1] == True:
                        if distacia_selec > maquina_evaluada[1]:
                            maquina_selec = maquina_evaluada[0]
                            distacia_selec = maquina_evaluada[1]
                            indice_ejercicio_sel = indice_ejercicio
                        elif distacia_selec == maquina_evaluada[1]:
                            if maquina_evaluada[0].celda < maquina_selec.celda:
                                maquina_selec = maquina_evaluada[0]
                                distacia_selec = maquina_evaluada[1]
                                indice_ejercicio_sel = indice_ejercicio
                    elif no_tiene_cola == False and list_respuesta[1] == False:
                        if len(maquina_evaluada[0].maquina_recurso.queue) < len(maquina_selec.maquina_recurso.queue):
                            maquina_selec = maquina_evaluada[0]
                            distacia_selec = maquina_evaluada[1]
                            indice_ejercicio_sel = indice_ejercicio
                        elif len(maquina_evaluada[0].maquina_recurso.queue) == len(maquina_selec.maquina_recurso.queue):
                            if distacia_selec > maquina_evaluada[1]:
                                maquina_selec = maquina_evaluada[0]
                                distacia_selec = maquina_evaluada[1]
                                indice_ejercicio_sel = indice_ejercicio
                            elif distacia_selec == maquina_evaluada[1]:
                                if maquina_evaluada[0].celda < maquina_selec.celda:
                                    maquina_selec = maquina_evaluada[0]
                                    distacia_selec = maquina_evaluada[1]
                                    indice_ejercicio_sel = indice_ejercicio
        return maquina_selec, distacia_selec, no_tiene_cola, eventos_reparacion, indice_ejercicio_sel

        
if __name__ == "__main__":
    sim = Simulacion('log.txt')
    sim.iniciar_simulacion(seed=2133, n_replicas=1)
    print(sim.dict_datos_replica[0][0]['int_llegada'])
    print(sim.dict_datos_replica[0][0]['cliente_desviado'])
    print(f'M1 {sim.dict_datos_replica[0][0]['cliente_desviado']/sim.dict_datos_replica[0][0]['int_llegada']}')
    print(f'M2 {np.average(sim.dict_datos_replica[0][0]['permanencia'])}')
    print(f'M3 {np.average(sim.dict_datos_replica[0][0]['espera_total'])}')
