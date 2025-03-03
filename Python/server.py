import socket
import threading

clients = []
clients_lock = threading.Lock()

def broadcast_message(message, sender_socket):
    with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.sendall(message.encode())
                except:
                    client.close()
                    clients.remove(client)

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(4096).decode()
            if not message:
                break
            print(f"Received: {message}")
            broadcast_message(message, client_socket)
        except:
            break
    
    with clients_lock:
        clients.remove(client_socket)
    client_socket.close()
    print("Client disconnected")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 12345))
    server_socket.listen()
    print("Server is listening on port 12345...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Client connected: {addr}")
        
        with clients_lock:
            clients.append(client_socket)
        
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    main()
