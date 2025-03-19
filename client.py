import socket

def iniciar_cliente(ip: str, puerto: int):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            print("Conectando...")
            cliente.connect((ip, puerto))
            print(f"Conectado al servidor en {ip}:{puerto}")

            while True:
                respuesta = cliente.recv(1024).decode()
                print(f"Servidor: {respuesta}")
                mensaje = input("Cliente: ")
                cliente.sendall(mensaje.encode())
                if mensaje.lower() == "salir":
                    print("Desconectando...")
                    break
    except Exception as e:
        print(f"Error al conectar: {e}")




def main():
    ip = input("Ingrese la IP del servidor: ")
    puerto = int(input("Ingrese el puerto: "))
    iniciar_cliente(ip, puerto)


if __name__ == "__main__":
    main()
