import socket
import threading
import pygame
import pickle

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 16497
FPS = 60
WIDTH, HEIGHT = 800, 400
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)


class PongClient:
    def __init__(self, host):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
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
        """Envía el movimiento del jugador al servidor."""
        try:
            self.client.sendall(pickle.dumps(move))
        except Exception as e:
            print(f"[ERROR] No se pudo enviar movimiento: {e}")

    def receive_game_state(self):
        """Recibe el estado del juego desde el servidor."""
        try:
            data = self.client.recv(4096)
            return pickle.loads(data)
        except Exception as e:
            print(f"[ERROR] Al recibir estado del juego: {e}")
            return None

    def run(self):
        """Ejecuta el bucle del cliente, maneja entradas y actualiza la pantalla."""
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
                self.draw_waiting()
        pygame.quit()

    def draw(self, game_state):
        """Dibuja los elementos del juego en la pantalla."""
        self.screen.fill(BACKGROUND_COLOR)

        # Dibujar las palas
        pygame.draw.rect(self.screen, BLUE, (10, game_state['players'][0], PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(self.screen, RED, (WIDTH - 20, game_state['players'][1], PADDLE_WIDTH, PADDLE_HEIGHT))

        # Dibujar la pelota
        pygame.draw.ellipse(self.screen, WHITE, (game_state['ball'][0], game_state['ball'][1], BALL_SIZE, BALL_SIZE))

        # Mostrar el marcador
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"{game_state['scores'][0]} - {game_state['scores'][1]}", True, TEXT_COLOR)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))  # Centramos el marcador

        # Línea central
        pygame.draw.line(self.screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 1)

        pygame.display.flip()

    def draw_waiting(self):
        """Dibuja la pantalla de espera para los jugadores."""
        self.screen.fill(BACKGROUND_COLOR)
        font = pygame.font.Font(None, 48)
        text = font.render("Esperando jugadores...", True, TEXT_COLOR)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        pygame.display.flip()


if __name__ == "__main__":
    # Solicitamos al usuario la IP del servidor
    server_ip = input("Introduce la IP del servidor: ")
    client = PongClient(server_ip)
    client.run()