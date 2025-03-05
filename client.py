import socket
import threading
import pygame
import pickle
import struct  # Para manejar el tamaño de los datos enviados

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 11578
FPS = 60
WIDTH, HEIGHT = 800, 400
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10


class PongClient:
    def __init__(self, host):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("[CLIENTE] intentando conectar")
            self.client.connect((host, PORT))
            print(f"[CLIENTE] Conectado al servidor {host}:{PORT}")
        except Exception as e:
            print(f"[ERROR] No se pudo conectar al servidor: {e}")
            exit()

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong Multijugador")
        self.clock = pygame.time.Clock()
        self.waiting = True
    
    def send_move(self, move):
        """Envía el movimiento al servidor si el socket sigue abierto."""
        try:
            if self.client.fileno() == -1:
                print("[ERROR] No se puede enviar movimiento. El socket está cerrado.")
                return
            
            data = pickle.dumps(move)
            self.client.sendall(data)
            print(f"[DEBUG] Movimiento enviado: {move}")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar movimiento: {e}")
    
    def receive_game_state(self):
        """Recibe el estado del juego desde el servidor con control de errores."""
        try:
            if self.client.fileno() == -1:
                print("[ERROR] El socket ya está cerrado. No se puede recibir datos.")
                return None

            # Recibir el tamaño del mensaje primero (4 bytes)
            data_size = self.client.recv(4)
            if not data_size:
                print("[ERROR] Conexión cerrada por el servidor.")
                self.client.close()
                return None

            data_size = struct.unpack("I", data_size)[0]
            print(f"[DEBUG] Recibiendo {data_size} bytes de datos del servidor...")

            # Recibir datos hasta completar el mensaje
            data = b""
            while len(data) < data_size:
                packet = self.client.recv(data_size - len(data))
                if not packet:
                    print("[ERROR] Conexión interrumpida.")
                    self.client.close()
                    return None
                data += packet

            game_state = pickle.loads(data)
            print(f"[DEBUG] Estado del juego recibido: {game_state}")
            return game_state

        except OSError as e:
            print(f"[ERROR] Problema con el socket: {e}")
            return None
    
    def run(self):
        """Bucle principal del juego."""
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            game_state = self.receive_game_state()
            if game_state and 'players' in game_state and len(game_state['players']) == 2:
                self.waiting = False
                self.draw(game_state)

                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]:
                    self.send_move('UP')
                elif keys[pygame.K_DOWN]:
                    self.send_move('DOWN')
            else:
                print("[DEBUG] Esperando jugadores...")
                self.draw_waiting()

        print("[CLIENTE] Cerrando conexión...")
        self.client.close()
        pygame.quit()
    
    def draw(self, game_state):
        """Dibuja el estado del juego en la pantalla."""
        self.screen.fill((0, 0, 0))
        pygame.draw.rect(self.screen, (255, 255, 255), (10, game_state['players'][0], PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(self.screen, (255, 255, 255), (WIDTH - 20, game_state['players'][1], PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(self.screen, (255, 255, 255), (game_state['ball'][0], game_state['ball'][1], BALL_SIZE, BALL_SIZE))
        pygame.display.flip()
    
    def draw_waiting(self):
        """Dibuja la pantalla de espera mientras se conectan jugadores."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)
        text = font.render("Esperando jugadores...", True, (255, 255, 255))
        self.screen.blit(text, (WIDTH // 2 - 100, HEIGHT // 2 - 20))
        pygame.display.flip()


if __name__ == "__main__":
    client = PongClient("4.tcp.eu.ngrok.io")
    client.run()
