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

class PongGame:
    """Clase que representa una instancia de un juego de Pong."""
    def __init__(self, connections, server):
        self.players = {0: HEIGHT // 2 - PADDLE_HEIGHT // 2, 1: HEIGHT // 2 - PADDLE_HEIGHT // 2}
        self.scores = {0: 0, 1: 0}
        self.ball = [WIDTH // 2, HEIGHT // 2, 3, 3]
        self.connections = connections
        self.server = server

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
        self.scores[scorer] += 1
        self.ball = [WIDTH // 2, HEIGHT // 2, random.choice([-3, 3]), random.choice([-3, 3])]
        pygame.time.delay(1000)
        self.broadcast()

    def handle_client(self, conn, player_id):
        """Maneja los movimientos de los jugadores."""
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

        # Verificar si ambos jugadores están desconectados
        if len(self.connections) == 0:
            print("[JUEGO] Ambos jugadores desconectados. Eliminando la partida.")
            self.server.remove_game(self)

    def update_ball(self):
        """Actualiza la posición de la pelota y detecta colisiones."""
        self.ball[0] += self.ball[2]
        self.ball[1] += self.ball[3]

        # Rebote en la parte superior e inferior
        if self.ball[1] <= 0 or self.ball[1] >= HEIGHT - BALL_SIZE:
            self.ball[3] *= -1

        # Colisión con las paletas
        if self.ball[0] <= PADDLE_WIDTH and self.players.get(0) <= self.ball[1] <= self.players.get(0) + PADDLE_HEIGHT:
            self.ball[2] *= -1
        elif self.ball[0] >= WIDTH - PADDLE_WIDTH - BALL_SIZE and self.players.get(1) <= self.ball[1] <= self.players.get(1) + PADDLE_HEIGHT:
            self.ball[2] *= -1

        # Gol: Si la pelota sale por la izquierda o la derecha
        if self.ball[0] <= 0:
            self.reset_ball(1)
        elif self.ball[0] >= WIDTH:
            self.reset_ball(0)

        self.broadcast()

    def start(self):
        """Ejecuta el bucle del juego."""
        while len(self.connections) > 0:
            self.update_ball()
            pygame.time.delay(16)

class PongServer:
    """Servidor principal que gestiona múltiples juegos."""
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen()
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")
        self.pending_connections = []
        self.active_games = []

    def handle_game(self, connections):
        """Crea y ejecuta un juego con las conexiones proporcionadas."""
        game = PongGame(connections, self)
        self.active_games.append(game)
        for i, conn in enumerate(connections):
            threading.Thread(target=game.handle_client, args=(conn, i), daemon=True).start()
        game.start()

    def remove_game(self, game):
        """Elimina un juego de la lista de juegos activos."""
        if game in self.active_games:
            self.active_games.remove(game)
            print("[SERVIDOR] Juego eliminado.")

    def start(self):
        """Inicia el servidor y maneja las conexiones entrantes."""
        while True:
            conn, _ = self.server.accept()
            self.pending_connections.append(conn)
            print("[CONEXIÓN] Nueva conexión recibida")

            # Cada vez que se tienen 2 conexiones, se inicia un nuevo juego
            if len(self.pending_connections) >= 2:
                print("[JUEGO] Iniciando un nuevo juego con 2 jugadores")
                connections = [self.pending_connections.pop(0), self.pending_connections.pop(0)]
                threading.Thread(target=self.handle_game, args=(connections,), daemon=True).start()

if __name__ == "__main__":
    server = PongServer()
    server.start()
