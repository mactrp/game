# necesitas instalar:  pip install pygame
import socket
import threading
import pygame
import pickle


HOST = '0.0.0.0'  
PORT = 16497      
FPS = 30          


WIDTH, HEIGHT = 600, 400
PLAYER_SIZE = 20


COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]


class Server:
    def __init__(self):
        self.players = {} 
        self.connections = {} 
        self.lock = threading.Lock()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen()
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")

    def broadcast_positions(self):
        with self.lock:
            data = pickle.dumps(self.players)
            for conn in self.connections.values():
                try:
                    conn.sendall(data)
                except Exception as e:
                    print(f"[ERROR] Al enviar posiciones: {e}")

    def handle_client(self, conn, addr):
        with self.lock:
            self.players[addr] = [WIDTH // 2, HEIGHT // 2]
            self.connections[addr] = conn
        
        self.broadcast_positions() 

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                direction = pickle.loads(data)
                with self.lock:
                    if direction == 'UP': self.players[addr][1] = max(0, self.players[addr][1] - 5)
                    elif direction == 'DOWN': self.players[addr][1] = min(HEIGHT, self.players[addr][1] + 5)
                    elif direction == 'LEFT': self.players[addr][0] = max(0, self.players[addr][0] - 5)
                    elif direction == 'RIGHT': self.players[addr][0] = min(WIDTH, self.players[addr][0] + 5)
                
                self.broadcast_positions()

        except Exception as e:
            print(f"[ERROR] Cliente {addr} desconectado inesperadamente: {e}")
        finally:
            with self.lock:
                print(f"[DESCONECTADO] {addr} se ha desconectado.")
                del self.players[addr]
                del self.connections[addr]
            self.broadcast_positions()
            conn.close()

    def start(self):
        print("[SERVIDOR] Esperando conexiones...")
        while True:
            try:
                conn, addr = self.server.accept()
                print(f"[NUEVA CONEXIÓN] {addr} conectado.")
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Al aceptar conexión: {e}")

# ==================== PARTE CLIENTE ====================
class Client:
    def __init__(self, host):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            resolved_host = socket.gethostbyname(host)
            self.client.connect((resolved_host, PORT))
            print(f"[CLIENTE] Conectado al servidor {resolved_host}:{PORT}")
        except Exception as e:
            print(f"[ERROR] No se pudo conectar al servidor: {e}")
            exit()

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Juego Multijugador")
        self.clock = pygame.time.Clock()

    def send_direction(self, direction):
        try:
            self.client.sendall(pickle.dumps(direction))
        except Exception as e:
            print(f"[ERROR] No se pudo enviar la dirección: {e}")

    def receive_positions(self):
        try:
            self.client.settimeout(0.1)  
            data = self.client.recv(4096)
            return pickle.loads(data) if data else {}
        except socket.timeout:
            return {}
        except Exception as e:
            print(f"[ERROR] Al recibir posiciones: {e}")
            return {}

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]: self.send_direction('UP')
            elif keys[pygame.K_DOWN]: self.send_direction('DOWN')
            elif keys[pygame.K_LEFT]: self.send_direction('LEFT')
            elif keys[pygame.K_RIGHT]: self.send_direction('RIGHT')

            positions = self.receive_positions()
            self.screen.fill((0, 0, 0))

            for i, (addr, (x, y)) in enumerate(positions.items()):
                color = COLORS[i % len(COLORS)]
                pygame.draw.circle(self.screen, color, (x, y), PLAYER_SIZE)

            pygame.display.flip()

        pygame.quit()
        self.client.close()

# ==================== EJECUTAMOS ====================
if __name__ == "__main__":
    choice = input("¿Quieres iniciar como servidor (s) o cliente (c)? ").strip().lower()

    if choice == 's':
        server = Server()
        server.start()
    elif choice == 'c':
        host = input("Introduce la IP del servidor (ej: 192.168.1.10): ").strip()
        client = Client(host)
        client.run()
    else:
        print("S o c te he dicho...!. Ejecuta nuevamente e ingresa 's' para servidor o 'c' para cliente.")
