import socket
import threading
import pygame
import pickle
import random

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 16497
FPS = 60
WIDTH, HEIGHT = 800, 400
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10

class PongServer:
    def __init__(self):
        self.players = {}  # Almacena las posiciones de los jugadores
        self.scores = {0: 0, 1: 0}  # Contador de goles (jugador 0 y jugador 1)
        self.ball = [WIDTH // 2, HEIGHT // 2, 3, 3]  # x, y, vel_x, vel_y
        self.connections = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(2)
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")

    def broadcast(self):
        """Envía los datos del juego a todos los clientes."""
        data = pickle.dumps({'players': self.players, 'ball': self.ball, 'scores': self.scores})
        for conn in self.connections:
            try:
                conn.sendall(data)
            except:
                pass

    def reset_ball(self, scorer):
        """Reinicia la pelota en el centro con una dirección aleatoria y actualiza el marcador."""
        self.scores[scorer] += 1  # Incrementa el puntaje del jugador que anotó
        self.ball = [WIDTH // 2, HEIGHT // 2, random.choice([-3, 3]), random.choice([-3, 3])]
        pygame.time.delay(1000)  # Pausa de 1 segundo antes de reanudar
        self.broadcast()  # Envía el marcador actualizado

    def handle_client(self, conn, player_id):
        """Maneja los movimientos de los jugadores."""
        self.players[player_id] = HEIGHT // 2 - PADDLE_HEIGHT // 2
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                move = pickle.loads(data)
                if move == 'UP':
                    self.players[player_id] = max(0, self.players[player_id] - 5)
                elif move == 'DOWN':
                    self.players[player_id] = min(HEIGHT - PADDLE_HEIGHT, self.players[player_id] + 5)
                self.broadcast()
            except:
                break
        self.connections.remove(conn)
        conn.close()

    def update_ball(self):
        """Actualiza la posición de la pelota y detecta colisiones."""
        self.ball[0] += self.ball[2]
        self.ball[1] += self.ball[3]

        # Rebote en la parte superior e inferior
        if self.ball[1] <= 0 or self.ball[1] >= HEIGHT - BALL_SIZE:
            self.ball[3] *= -1

        # Colisión con las paletas
        if self.ball[0] <= PADDLE_WIDTH and self.players.get(0, HEIGHT // 2) <= self.ball[1] <= self.players.get(0, HEIGHT // 2) + PADDLE_HEIGHT:
            self.ball[2] *= -1
        elif self.ball[0] >= WIDTH - PADDLE_WIDTH - BALL_SIZE and self.players.get(1, HEIGHT // 2) <= self.ball[1] <= self.players.get(1, HEIGHT // 2) + PADDLE_HEIGHT:
            self.ball[2] *= -1

        # Gol: Si la pelota sale por la izquierda, punto para el jugador 1
        if self.ball[0] <= 0:
            self.reset_ball(1)  # Jugador 1 anota

        # Gol: Si la pelota sale por la derecha, punto para el jugador 0
        elif self.ball[0] >= WIDTH:
            self.reset_ball(0)  # Jugador 0 anota

        self.broadcast()

    def start(self):
        """Inicia el servidor y maneja las conexiones de los jugadores."""
        while len(self.connections) < 2:
            conn, _ = self.server.accept()
            player_id = len(self.connections)
            self.connections.append(conn)
            threading.Thread(target=self.handle_client, args=(conn, player_id), daemon=True).start()

        while True:
            self.update_ball()
            pygame.time.delay(16)


if __name__ == "__main__":
    server = PongServer()
    server.start()
