"""
WebSocket Router

Handles WebSocket connections, ping/pong messages, and real-time communication
with connected clients.
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.services.websocket_manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for client connections with ping/pong heartbeat.

    Expected client messages:
    - {"type": "pong"} - Response to server ping
    - {"type": "message", "data": {...}} - Regular message
    - Any other JSON message

    Server messages sent:
    - {"type": "ping", "timestamp": "...", "message": "..."} - Heartbeat ping
    - {"type": "timeout", "message": "..."} - Session timeout notification
    - {"type": "notification", "data": {...}} - General notification

    Args:
        websocket (WebSocket): The WebSocket connection
        user_id (str): The unique identifier of the user

    Example:
        Client connects: ws://localhost:8000/ws/connect/user123
        Server sends ping every 30 seconds
        Client responds with pong
        If no pong for 3 hours, server signs user out
    """
    try:
        # Accept the WebSocket connection
        await manager.connect(user_id, websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()

                # Parse JSON message
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    message = {"type": "text", "content": data}

                # Handle different message types
                message_type = message.get("type", "unknown")

                if message_type == "pong":
                    # Record pong response
                    await manager.receive_pong(user_id)

                elif message_type == "message":
                    # Handle regular messages
                    await _handle_user_message(user_id, message)

                elif message_type == "ping":
                    # If client sends ping, respond with pong
                    pong_response = {"type": "pong", "timestamp": message.get("timestamp")}
                    await manager.send_message(user_id, pong_response)

                else:
                    # Log unknown message type
                    print(f"ℹ️ Unknown message type '{message_type}' from user {user_id}")

            except WebSocketDisconnect:
                # Client disconnected
                await manager.disconnect(user_id)
                print(f"📴 User {user_id} disconnected")
                break

    except Exception as e:
        print(f"✗ WebSocket error for user {user_id}: {str(e)}")
        await manager.disconnect(user_id)


async def _handle_user_message(user_id: str, message: dict) -> None:
    """
    Handle regular user messages from WebSocket.

    Args:
        user_id (str): The user ID
        message (dict): The message content
    """
    try:
        # Log the message
        print(f"📨 Message from user {user_id}: {message}")

        # You can process the message here
        # For now, just log it

    except Exception as e:
        print(f"✗ Error handling message from user {user_id}: {str(e)}")


@router.get("/status/{user_id}")
async def get_connection_status(user_id: str):
    """
    Check if a user is currently connected via WebSocket.

    Args:
        user_id (str): The unique identifier of the user

    Returns:
        dict: Connection status information

    Raises:
        HTTPException: If there's an error checking status
    """
    try:
        is_connected = manager.is_user_connected(user_id)

        return {
            "user_id": user_id,
            "is_connected": is_connected,
            "status": "connected" if is_connected else "disconnected",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking connection status: {str(e)}")


@router.get("/stats")
async def get_connection_stats():
    """
    Get statistics about current WebSocket connections.

    Returns:
        dict: Connection statistics including:
            - total_connections: Number of connected users
            - connected_users: List of connected user IDs
            - ping_interval_seconds: Interval between pings
            - pong_timeout_seconds: Timeout threshold for pong

    Raises:
        HTTPException: If there's an error retrieving stats
    """
    try:
        stats = manager.get_connection_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@router.post("/send/{user_id}")
async def send_message_to_user(user_id: str, message: dict):
    """
    Send a message to a specific connected user via WebSocket.

    Args:
        user_id (str): The unique identifier of the user
        message (dict): The message to send

    Returns:
        dict: Operation result

    Raises:
        HTTPException: If user is not connected or message send fails
    """
    try:
        if not manager.is_user_connected(user_id):
            raise HTTPException(status_code=404, detail=f"User {user_id} is not connected")

        success = await manager.send_message(user_id, message)

        if success:
            return {"status": "success", "message": "Message sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.post("/broadcast")
async def broadcast_message(message: dict, exclude_user: str = Query(None)):
    """
    Broadcast a message to all connected users.

    Args:
        message (dict): The message to broadcast
        exclude_user (str): Optional user ID to exclude from broadcast

    Returns:
        dict: Broadcast operation result

    Raises:
        HTTPException: If there's an error broadcasting
    """
    try:
        await manager.broadcast(message, exclude_user=exclude_user)

        stats = manager.get_connection_stats()
        return {
            "status": "success",
            "message": "Message broadcasted successfully",
            "recipients": stats["total_connections"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error broadcasting message: {str(e)}")
