import signal
import sys
import logging
import os
import grpc
# Agregar la ruta al directorio proto al Python PATH
from grpc.experimental import aio as grpc_aio  # Corregir la importación

proto_dir = os.path.join(os.path.dirname(__file__), 'proto')
sys.path.append(proto_dir)
import store_pb2
import store_pb2_grpc
import yaml
import logging
import asyncio
import json
import random
from datetime import datetime

# Rutas para los archivos de registro de errores y advertencias
log_dir = os.path.dirname(__file__)
error_log_path = os.path.join(log_dir, 'error.log')
warning_log_path = os.path.join(log_dir, 'warning.log')

# Configurar el formato del registro
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurar el registrador de errores
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(error_log_path, mode='w')  # Modo de escritura 'w'
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)

# Configurar el registrador de advertencias
warning_logger = logging.getLogger('warning_logger')
warning_logger.setLevel(logging.WARNING)
warning_handler = logging.FileHandler(warning_log_path, mode='w')  # Modo de escritura 'w'
warning_handler.setFormatter(formatter)
warning_logger.addHandler(warning_handler)

# Configurar el registro para capturar todas las excepciones y errores
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[error_handler, warning_handler])

# Redirigir la salida estándar y la salida de error a un archivo
stdout_log_path = os.path.join(log_dir, 'stdout.log')
stderr_log_path = os.path.join(log_dir, 'stderr.log')

sys.stdout = open(stdout_log_path, 'w')
sys.stderr = open(stderr_log_path, 'w')

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.lock = asyncio.Lock()  # Bloqueo para operaciones de lectura y escritura

    async def put(self, request, context):
        async with self.lock:
            self.data[request.key] = request.value  # Modificar datos de forma segura
            await self.persist_data()  # Guardar datos en disco
            await self.propagar_put(request)
        return store_pb2.PutResponse(success=True)

    async def get(self, request, context):
        async with self.lock:
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value, found=bool(value))

    async def persist_data(self):
        try:
            with open('data.json', 'w') as file:
                json.dump(self.data, file)
        except Exception as e:
            error_logger.error("Error al persistir los datos: %s", e)

    async def recover_data(self):
        try:
            with open('data.json', 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            warning_logger.warning("Archivo de datos no encontrado. Iniciando con datos vacíos.")
        except Exception as e:
            error_logger.error("Error al recuperar los datos: %s", e)

    async def replicate(self, request):
        quorum_size = 3 if request.value else 2
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                await self.propagar_put(request)

    async def propagar_put(self, request):
        try:
            # Determinar el tamaño del quórum basado en la cantidad de nodos disponibles
            quorum_size = max(2, len(self.nodes) // 2 + 1)
            
            # Seleccionar nodos aleatorios para solicitar votos
            nodes = random.sample(self.nodes, quorum_size)
            
            # Enviar solicitudes de voto a los nodos seleccionados
            votes = await asyncio.gather(*[self.solicitar_voto(node, request) for node in nodes])
            
            # Contar los votos recibidos (incluido el propio)
            num_votes = sum(1 for vote in votes if vote.vote == self.node_id) + 1
            
            # Verificar si se ha alcanzado el quórum necesario
            if num_votes >= quorum_size:
                await self.confirmar_a_nodo(self.node_id, request)
        except Exception as e:
            if not isinstance(e, TypeError):
                error_logger.error("Error al propagar la modificación: %s", e)

    async def solicitar_voto(self, node, request):
        return await self.pedir_voto(request, None)

    async def confirmar_a_nodo(self, node, request):
        async with grpc_aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            await stub.do_commit(store_pb2.CommitRequest(key=request.key, value=request.value))

    async def propagate_get(self, request):
        try:
            values = await asyncio.gather(*[self.request_value(node, request) for node in self.nodes if node != self.node_id])
            values = [value.value for value in values if value.value]
            if values:
                return values[0]
            else:
                return None
        except Exception as e:
            error_logger.error("Error al propagar la consulta: %s", e)
            return None

    async def request_value(self, node, request):
        async with grpc_aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            return await stub.get(store_pb2.GetRequest(key=request.key))

    async def pedir_voto(self, request, context):
        return store_pb2.VoteResponse(vote=self.node_id)
    
    async def slowDown(self, request, context):
        try:
            # Agregar un retraso a las operaciones
            delay = request.delay
            await asyncio.sleep(delay)
            return store_pb2.SlowDownResponse(success=True)
        except asyncio.CancelledError:
            warning_logger.info("Operación de retardo cancelada")
            return store_pb2.SlowDownResponse(success=False)
        except Exception as e:
            error_logger.error("Error en slowDown: %s", e)
            return store_pb2.SlowDownResponse(success=False)
        
    async def restore(self, request, context):
        try:
            await self.recover_data()
            return store_pb2.RestoreResponse(success=True)
        except Exception as e:
            error_logger.error("Error al restaurar el nodo: %s", e)
            return store_pb2.RestoreResponse(success=False)
        
async def cargar_configuracion(config_path):
    try:
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        error_logger.error("Archivo de configuración no encontrado en la ruta especificada: %s", config_path)
        return {}
    except Exception as e:
        error_logger.error("Error al cargar la configuración: %s", e)
        return {}

async def start_servers():
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')
    config = await cargar_configuracion(config_path)
    servers = []
    try:
        for node in config['nodes']:
            node_id = node['id']
            ip = node['ip']
            port = node['port']
            nodes = [f"{n['ip']}:{n['port']}" for n in config['nodes'] if n != node and 'ip' in n and 'port' in n]
            service = KeyValueStore(node_id, nodes)
            await service.recover_data()  # Recuperar datos del disco al iniciar
            server = Server(service, ip, port)
            server_address = f"{ip}:{port}"
            try:
                server.server.add_insecure_port(server_address)
            except Exception as e:
                error_logger.error("Error al agregar el puerto al servidor: %s", e)
                continue  # Continuar con la siguiente iteración si ocurre un error
            try:
                await server.server.start()
            except Exception as e:
                error_logger.error("Error al iniciar el servidor: %s", e)
                continue  # Continuar con la siguiente iteración si ocurre un error
            else:
                servers.append(server)
                logging.info(f"Servidor para el nodo {node_id} escuchando en {server_address}")
        # Manejar la señal de interrupción (Ctrl+C)
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown(servers)))

        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])
    finally:
        logging.info("Cerrando todos los servidores...")

async def shutdown(servers):
    for server in servers:
        await server.stop()

class Server:
    def __init__(self, service, ip, port):
        self.service = service
        self.ip = ip
        self.port = port
        self.server = grpc_aio.server(options=[('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(self.service, self.server)

    async def stop(self):
        await self.server.stop(None)

if __name__ == '__main__':
    # Configurar el nivel de registro global para evitar la impresión de mensajes de error específicos
    logging.getLogger().setLevel(logging.ERROR)
    asyncio.run(start_servers())