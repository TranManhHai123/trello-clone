from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: int):
        if project_id in self.active_connections:
            connections = self.active_connections[project_id]
            if websocket in connections:
                connections.remove(websocket)
            if not connections:
                del self.active_connections[project_id]

    async def broadcast(self, project_id: int, message: dict):
        if project_id not in self.active_connections:
            return
        dead_connections = []
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead, project_id)

manager = ConnectionManager()