import socket
import threading

def send_message(client_socket, name):
    while True:
        message = input()
        msg = f"{name} : {message}"
        try:
            client_socket.sendall(msg.encode())
        except:
            print("Error sending message")
            break
        
        if message.lower() == "quit":
            print("Stopping the application")
            client_socket.close()
            break

def receive_message(client_socket):
    while True:
        try:
            message = client_socket.recv(4096).decode()
            if not message:
                print("Disconnected from the server")
                break
            print(message)
        except:
            break

def main():
    server_address = "127.0.0.1"
    port = 12345
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_address, port))
        print("Successfully connected to server")
    except:
        print("Not able to connect")
        return
    
    name = input("Enter your chat name: ")
    
    sender_thread = threading.Thread(target=send_message, args=(client_socket, name))
    receiver_thread = threading.Thread(target=receive_message, args=(client_socket,))
    
    sender_thread.start()
    receiver_thread.start()
    
    sender_thread.join()
    receiver_thread.join()
    
    client_socket.close()

if __name__ == "__main__":
    main()