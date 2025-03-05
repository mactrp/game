import socket
import threading
import pickle
import struct  # Para manejar el tamaño de los datos enviados
import time  # Para pausas en el bucle del servidor

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 16497
FPS = 60
WIDTH, HEIGHT = 800, 400
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
BALL_SPEED = 3  # Velocidad de la pelota

class PongServer:
    def __init__(self):
        self.players = {}  # Almacena las posiciones de los jugadores
        self.ball = [WIDTH // 2, HEIGHT // 2, BALL_SPEED, BALL_SPEED]  # x, y, vel_x, vel_y
        self.connections = []
        self.lock = threading.Lock()  # Para evitar problemas de concurrencia
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(2)
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")

    def send_data(self, conn, data):
        """Envía datos precedidos por su tamaño para evitar fragmentación."""
        try:
            packed_data = pickle.dumps(data)
            size = struct.pack("I", len(packed_data))
            conn.sendall(size + packed_data)
        except Exception as e:
            print(f"[ERROR] No se pudo enviar datos: {e}")

    def broadcast(self):
        """Envía el estado del juego a todos los clientes conectados."""
        data = {'players': self.players, 'ball': self.ball}
        for conn in self.connections:
            self.send_data(conn, data)

    def handle_client(self, conn, player_id):
        """Maneja las conexiones de los jugadores y recibe sus movimientos."""
        self.players[player_id] = HEIGHT // 2 - PADDLE_HEIGHT // 2
        while True:
            try:
                data_size = conn.recv(4)
                if not data_size:
                    print(f"[SERVIDOR] Jugador {player_id} desconectado.")
                    break
                
                size = struct.unpack("I", data_size)[0]
                data = b""
                while len(data) < size:
                    packet = conn.recv(size - len(data))
                    if not packet:
                        print(f"[SERVIDOR] Desconexión inesperada del jugador {player_id}")
                        break
                    data += packet

                move = pickle.loads(data)
                with self.lock:
                    if move == 'UP':
                        self.players[player_id] = max(0, self.players[player_id] - 5)
                    elif move == 'DOWN':
                        self.players[player_id] = min(HEIGHT - PADDLE_HEIGHT, self.players[player_id] + 5)
                
                self.broadcast()
            except Exception as e:
                print(f"[ERROR] Problema con el jugador {player_id}: {e}")
                break

        with self.lock:
            self.connections.remove(conn)
        conn.close()
    
    def update_ball(self):
        """Mueve la pelota y detecta colisiones."""
        with self.lock:
            self.ball[0] += self.ball[2]
            self.ball[1] += self.ball[3]

            # Rebote en la parte superior e inferior
            if self.ball[1] <= 0 or self.ball[1] >= HEIGHT - BALL_SIZE:
                self.ball[3] *= -1  # Invertir dirección Y

            # Colisión con los jugadores
            if self.ball[0] <= PADDLE_WIDTH:
                if self.players.get(0, HEIGHT // 2) <= self.ball[1] <= self.players.get(0, HEIGHT // 2) + PADDLE_HEIGHT:
                    self.ball[2] *= -1  # Rebote en la paleta izquierda
                else:
                    print("[SERVIDOR] Punto para el jugador 2")
                    self.reset_ball()
            elif self.ball[0] >= WIDTH - PADDLE_WIDTH - BALL_SIZE:
                if self.players.get(1, HEIGHT // 2) <= self.ball[1] <= self.players.get(1, HEIGHT // 2) + PADDLE_HEIGHT:
                    self.ball[2] *= -1  # Rebote en la paleta derecha
                else:
                    print("[SERVIDOR] Punto para el jugador 1")
                    self.reset_ball()
        
        self.broadcast()

    def reset_ball(self):
        """Reinicia la pelota en el centro del campo."""
        self.ball = [WIDTH // 2, HEIGHT // 2, BALL_SPEED, BALL_SPEED]

    def start(self):
        """Inicia el servidor y gestiona las conexiones."""
        while len(self.connections) < 2:
            conn, addr = self.server.accept()
            player_id = len(self.connections)
            self.connections.append(conn)
            print(f"[SERVIDOR] Jugador {player_id} conectado desde {addr}")
            threading.Thread(target=self.handle_client, args=(conn, player_id), daemon=True).start()

        print("[SERVIDOR] ¡Juego iniciado!")
        while True:
            self.update_ball()
            time.sleep(1 / FPS)  # Control del tiempo de actualización


if __name__ == "__main__":
    server = PongServer()
    server.start()
