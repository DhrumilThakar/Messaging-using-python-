import socket
import threading
import asyncio
import websockets

clients = []
clients_lock = threading.Lock()

async def broadcast_message(message, sender_socket):
    async with clients_lock:
        for client in clients:
            if client != sender_socket:
                try:
                    await client.send(message)
                except:
                    await client.close()
                    clients.remove(client)

async def handle_client(websocket, path):
    async with clients_lock:
        clients.append(websocket)
    
    try:
        async for message in websocket:
            print(f"Received: {message}")
            await broadcast_message(message, websocket)
    except:
        pass
    finally:
        async with clients_lock:
            clients.remove(websocket)
        await websocket.close()
        print("Client disconnected")

async def start_server():
    server = await websockets.serve(handle_client, "0.0.0.0", 12346)
    print("WebSocket server is listening on port 12346...")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
