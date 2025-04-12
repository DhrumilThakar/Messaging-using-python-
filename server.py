import asyncio
import websockets
import socket
import threading
import json  # JSON format for WebSocket messages

websocket_clients = set() #Store Websocket client which are active
socket_clients = [] # Store TCP client which are active
client_names = {}  # Map TCp client to their username
clients_lock = threading.Lock() # To ensure thread saafety when modifying socket client

async def broadcast_message(message, sender=None, sender_name="Unknown"):
    """
    Broadcasts messages to both WebSocket and TCP clients.
    Ensures WebSocket messages are JSON and TCP messages include the sender's name.
    """
    # Format message as JSON for WebSocket clients
    formatted_message = json.dumps({"username": sender_name, "text": message})

    # Broadcast to WebSocket clients
    websockets_to_remove = set()
    for client in websocket_clients:
        if client != sender:
            try:
                await client.send(formatted_message)
            except Exception as e:
                print(f"Error sending to WebSocket client: {e}")
                websockets_to_remove.add(client)

    for client in websockets_to_remove:
        websocket_clients.remove(client)

    # Broadcast to TCP socket clients
    with clients_lock:
        disconnected_clients = []
        for client in socket_clients:
            if client != sender:
                try:
                    if client in client_names:
                        formatted_message_tcp = f": {message}"
                        client.sendall(formatted_message_tcp.encode())
                    else:
                        client.sendall(message.encode())
                except Exception as e:
                    print(f"Error sending to TCP client: {e}")
                    disconnected_clients.append(client)

        for client in disconnected_clients:
            socket_clients.remove(client)
            client.close()

async def handle_websocket(websocket):
    """
    Handles incoming WebSocket connections.
    Clients should send their username first.
    """
    websocket_clients.add(websocket)
    try:
        # Receive first message as the username
        name_message = await websocket.recv()
        try:
            name_data = json.loads(name_message)
            username = name_data.get("username", "Guest")
        except json.JSONDecodeError:
            username = "Guest"

        print(f"WebSocket Client connected: {username}")

        async for message in websocket:
            print(f"WebSocket Received from {username}: {message}")
            await broadcast_message(message, sender=websocket, sender_name=username)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_clients.remove(websocket)
        await websocket.close()
        print(f"WebSocket Client {username} disconnected")

def handle_socket_client(client_socket, loop):
    """
    Handles TCP socket clients.
    First, it receives the username, then listens for messages.
    """
    with clients_lock:
        socket_clients.append(client_socket)

    try:
        # Read client name first
        name = client_socket.recv(4096).decode().strip()
        if not name:
            print("Client disconnected (empty name received)")
            return
        client_names[client_socket] = name
        print(f"Socket Client connected: {name}")
    except Exception as e:
        print(f"Error receiving name: {e}")
        return

    while True:
        try:
            message = client_socket.recv(4096).decode().strip()
            if not message:
                print(f"Client {client_names[client_socket]} disconnected (empty message received)")
                break

            print(f"Socket Received from {client_names[client_socket]}: {message}")

            # Properly run async broadcast
            asyncio.run_coroutine_threadsafe(
                broadcast_message(message, sender=client_socket, sender_name=client_names[client_socket]), 
                loop
            )

        except Exception as e:
            print(f"Error: {e}")
            break

    with clients_lock:
        if client_socket in client_names:
            print(f"Socket Client {client_names[client_socket]} disconnected")
            del client_names[client_socket]
        socket_clients.remove(client_socket)
    client_socket.close()

def start_socket_server(loop):
    """
    Starts a TCP socket server on port 12346.
    Handles incoming connections in separate threads.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 12346))  # Use the correct TCP port
    server_socket.listen()
    print("TCP Server is listening on port 12346...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Socket Client connected: {addr}")
        thread = threading.Thread(target=handle_socket_client, args=(client_socket, loop))
        thread.start()

async def start_websocket_server():
    """
    Starts the WebSocket server on port 12347.
    """
    async with websockets.serve(handle_websocket, "0.0.0.0", 12347):
        print("WebSocket server is listening on port 12347...")
        await asyncio.Future()  # Keeps the server running

async def main():
    """
    Starts both the WebSocket server and TCP server.
    The TCP server runs in a separate thread.
    """
    loop = asyncio.get_running_loop()

    # Start TCP socket server in a separate thread
    socket_thread = threading.Thread(target=start_socket_server, args=(loop,), daemon=True)
    socket_thread.start()

    # Start WebSocket server
    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(main())