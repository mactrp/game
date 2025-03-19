import socket
import threading
import pickle
import os
import subprocess

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 8080

class GameServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")

    def handle_client(self, conn):
        try:
            # Enviar el menú de selección al cliente
            menu = "Elige un juego:\n1. Tetris\n2. Space Invaders\nOpción: "
            conn.send(menu.encode())

            # Recibir la elección del usuario
            choice = conn.recv(1024).decode().strip()
            print(choice)

            # Ejecutar el juego correspondiente
            if choice == '1':
                print("[JUEGO] Iniciando Tetris...")
                subprocess.Popen(["python", "tetris/main.py"])
            elif choice == '2':
                print("[JUEGO] Iniciando Space Invaders...")
                subprocess.Popen(["python", "space-invaders/main.py"])
            else:
                conn.send("Opción inválida. Conexión cerrada.".encode())
                conn.close()
                return

            conn.send(f"Juego {choice} iniciado.".encode())
        except Exception as e:
            print(f"[ERROR] {e}")
            conn.send("Se ha producido un error en el servidor.".encode())
        finally:
            try:
                conn.close()
            except:
                pass


    def start(self):
        while True:
            conn, addr = self.server.accept()
            print(f"[CONEXIÓN] Nueva conexión de {addr}")
            threading.Thread(target=self.handle_client, args=(conn,)).start()

if __name__ == "__main__":
    server = GameServer()
    server.start()
