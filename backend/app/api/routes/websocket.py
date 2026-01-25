"""WebSocket endpoints for real-time updates."""
import asyncio
import json
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.routes.arbitrage import get_scanner

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/opportunities")
async def websocket_opportunities(websocket: WebSocket):
    """
    WebSocket endpoint for real-time opportunity updates.

    Sends updates whenever new opportunities are detected.
    Message format:
    {
        "type": "opportunities",
        "data": {
            "opportunities": [...],
            "count": N,
            "timestamp": "..."
        }
    }
    """
    await manager.connect(websocket)

    try:
        # Send initial data
        scanner = get_scanner()
        if scanner:
            opps = scanner.get_opportunities()
            await websocket.send_json(
                {
                    "type": "opportunities",
                    "data": {
                        "opportunities": [
                            {
                                "id": o.id,
                                "type": o.type.value,
                                "market_id": o.market_id,
                                "market_question": o.market_question,
                                "yes_price": o.yes_price,
                                "no_price": o.no_price,
                                "combined_cost": o.combined_cost,
                                "net_profit": o.net_profit,
                                "edge_percent": o.edge_percent,
                                "detected_at": o.detected_at.isoformat(),
                            }
                            for o in opps
                        ],
                        "count": len(opps),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )

        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client message or timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=5.0
                )

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send heartbeat and updated opportunities
                scanner = get_scanner()
                if scanner and scanner.is_running:
                    opps = scanner.get_opportunities()
                    await websocket.send_json(
                        {
                            "type": "opportunities",
                            "data": {
                                "opportunities": [
                                    {
                                        "id": o.id,
                                        "type": o.type.value,
                                        "market_id": o.market_id,
                                        "market_question": o.market_question,
                                        "yes_price": o.yes_price,
                                        "no_price": o.no_price,
                                        "combined_cost": o.combined_cost,
                                        "net_profit": o.net_profit,
                                        "edge_percent": o.edge_percent,
                                        "detected_at": o.detected_at.isoformat(),
                                    }
                                    for o in opps
                                ],
                                "count": len(opps),
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "heartbeat",
                            "data": {"timestamp": datetime.utcnow().isoformat()},
                        }
                    )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """WebSocket endpoint for scanner statistics."""
    await manager.connect(websocket)

    try:
        while True:
            scanner = get_scanner()
            stats = scanner.stats if scanner else {"running": False}

            await websocket.send_json(
                {
                    "type": "stats",
                    "data": {
                        **stats,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )

            await asyncio.sleep(2)  # Update every 2 seconds

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
