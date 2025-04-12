import socket
import threading
import time

def send_message(client_socket, name):
    while True:
        message = input()
        if message.lower() == "quit":
            print("Disconnecting...")
            client_socket.close()
            break
        msg = f"{name}: {message}"
        try:
            client_socket.sendall(msg.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def receive_message(client_socket):
    try:
        while True:
            message = client_socket.recv(4096).decode()
            if not message:
                print("Disconnected from server")
                break
            print(message)
    except Exception as e:
        print(f"Error receiving message: {e}")
    finally:
        client_socket.close()

def main():
    server_address = "127.0.0.1"
    port = 12346  # Use the correct TCP port

    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((server_address, port))
            print("Successfully connected to server")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Connection failed after {max_retries} attempts: {e}")
                return

    while True:
        name = input("Enter your chat name: ").strip()
        if not name:
            print("Name cannot be empty. Please try again.")
        else:
            break

    try:
        client_socket.sendall(name.encode())
        print(f"Welcome, {name}! Type your messages below.")
    except Exception as e:
        print(f"Failed to send name: {e}")
        client_socket.close()
        return

    sender_thread = threading.Thread(target=send_message, args=(client_socket, name))
    receiver_thread = threading.Thread(target=receive_message, args=(client_socket,))

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join()
    receiver_thread.join()

    client_socket.close()

if __name__ == "__main__":
    main()