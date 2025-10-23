"""
WebSocket Manager Service

Manages WebSocket connections, ping/pong heartbeats, and connection timeouts.
Handles sending pings to clients and tracking their responses.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Set
from fastapi import WebSocket
from app.services.auth_service import sign_out_user


class ConnectionManager:
    """
    Manages WebSocket connections for all connected users.

    Handles:
    - Connection lifecycle (connect, disconnect)
    - Ping/pong heartbeat mechanism
    - Automatic timeout and sign-out after inactivity
    - Broadcasting messages to connected clients
    """

    def __init__(self):
        """Initialize the connection manager."""
        # Dictionary to store active connections: {user_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Dictionary to store last pong timestamp: {user_id: datetime}
        self.last_pong_time: Dict[str, datetime] = {}

        # Dictionary to store ping tasks: {user_id: task}
        self.ping_tasks: Dict[str, asyncio.Task] = {}

        # Dictionary to store timeout tasks: {user_id: task}
        self.timeout_tasks: Dict[str, asyncio.Task] = {}

        # Ping interval in seconds (send ping every 30 seconds)
        self.PING_INTERVAL = 30

        # Pong timeout in seconds (wait 3 hours for pong before auto sign-out)
        self.PONG_TIMEOUT = 3 * 60 * 60  # 3 hours = 10800 seconds

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection for a user.

        Args:
            user_id (str): The unique identifier of the user
            websocket (WebSocket): The WebSocket connection object

        Raises:
            Exception: If there's an error accepting the connection
        """
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
            self.last_pong_time[user_id] = datetime.now()

            print(f"✓ User {user_id} connected via WebSocket")

            # Start ping and timeout tasks for this connection
            await self._start_ping_task(user_id)
            await self._start_timeout_task(user_id)

        except Exception as e:
            print(f"✗ Error connecting user {user_id}: {str(e)}")
            raise

    async def disconnect(self, user_id: str) -> None:
        """
        Unregister a WebSocket connection for a user.

        Args:
            user_id (str): The unique identifier of the user
        """
        try:
            # Cancel ping and timeout tasks
            if user_id in self.ping_tasks:
                self.ping_tasks[user_id].cancel()
                del self.ping_tasks[user_id]

            if user_id in self.timeout_tasks:
                self.timeout_tasks[user_id].cancel()
                del self.timeout_tasks[user_id]

            # Remove connection
            if user_id in self.active_connections:
                del self.active_connections[user_id]

            if user_id in self.last_pong_time:
                del self.last_pong_time[user_id]

            print(f"✓ User {user_id} disconnected from WebSocket")

        except Exception as e:
            print(f"✗ Error disconnecting user {user_id}: {str(e)}")

    async def send_ping(self, user_id: str) -> bool:
        """
        Send a ping message to a connected client.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if ping was sent successfully, False otherwise
        """
        if user_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[user_id]
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "message": "Server heartbeat - please respond with pong",
            }

            await websocket.send_json(ping_message)
            print(f"📤 Ping sent to user {user_id}")
            return True

        except Exception as e:
            print(f"✗ Error sending ping to user {user_id}: {str(e)}")
            await self.disconnect(user_id)
            return False

    async def receive_pong(self, user_id: str) -> bool:
        """
        Record receipt of a pong message from a client.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if pong was recorded successfully
        """
        try:
            self.last_pong_time[user_id] = datetime.now()
            print(f"📥 Pong received from user {user_id}")
            return True
        except Exception as e:
            print(f"✗ Error recording pong for user {user_id}: {str(e)}")
            return False

    async def broadcast(self, message: dict, exclude_user: str = None) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message (dict): The message to broadcast
            exclude_user (str): Optional user ID to exclude from broadcast
        """
        disconnected_users: Set[str] = set()

        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"✗ Error broadcasting to user {user_id}: {str(e)}")
                disconnected_users.add(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)

    async def send_message(self, user_id: str, message: dict) -> bool:
        """
        Send a message to a specific user.

        Args:
            user_id (str): The unique identifier of the user
            message (dict): The message to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if user_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"✗ Error sending message to user {user_id}: {str(e)}")
            await self.disconnect(user_id)
            return False

    async def _start_ping_task(self, user_id: str) -> None:
        """
        Start a periodic ping task for a user.

        Sends a ping message every PING_INTERVAL seconds.

        Args:
            user_id (str): The unique identifier of the user
        """
        try:
            async def ping_loop():
                while user_id in self.active_connections:
                    try:
                        await asyncio.sleep(self.PING_INTERVAL)
                        await self.send_ping(user_id)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(f"✗ Error in ping loop for user {user_id}: {str(e)}")
                        break

            task = asyncio.create_task(ping_loop())
            self.ping_tasks[user_id] = task

        except Exception as e:
            print(f"✗ Error starting ping task for user {user_id}: {str(e)}")

    async def _start_timeout_task(self, user_id: str) -> None:
        """
        Start a timeout monitoring task for a user.

        Automatically signs out the user if no pong is received for PONG_TIMEOUT seconds.

        Args:
            user_id (str): The unique identifier of the user
        """
        try:
            async def timeout_monitor():
                while user_id in self.active_connections:
                    try:
                        await asyncio.sleep(60)  # Check every minute

                        if user_id not in self.last_pong_time:
                            continue

                        last_pong = self.last_pong_time[user_id]
                        time_since_pong = datetime.now() - last_pong

                        # Check if timeout threshold is exceeded (3 hours)
                        if time_since_pong.total_seconds() > self.PONG_TIMEOUT:
                            print(
                                f"⏱️ User {user_id} timeout detected - "
                                f"no pong for {time_since_pong.total_seconds()/3600:.1f} hours"
                            )

                            # Attempt automatic sign-out
                            await self._handle_timeout(user_id)
                            break

                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(f"✗ Error in timeout monitor for user {user_id}: {str(e)}")
                        break

            task = asyncio.create_task(timeout_monitor())
            self.timeout_tasks[user_id] = task

        except Exception as e:
            print(f"✗ Error starting timeout task for user {user_id}: {str(e)}")

    async def _handle_timeout(self, user_id: str) -> None:
        """
        Handle automatic sign-out when a user times out.

        Performs the following:
        1. Notifies the user via WebSocket
        2. Calls Firebase sign-out function
        3. Disconnects the WebSocket

        Args:
            user_id (str): The unique identifier of the user
        """
        try:
            # Send timeout notification to client
            timeout_message = {
                "type": "timeout",
                "message": "Your session has expired due to inactivity (3 hours). Please sign in again.",
                "timestamp": datetime.now().isoformat(),
            }

            try:
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_json(timeout_message)
            except Exception as e:
                print(f"✗ Error sending timeout message to user {user_id}: {str(e)}")

            # Call Firebase sign-out function
            try:
                await sign_out_user(user_id)
                print(f"✓ User {user_id} signed out automatically due to timeout")
            except Exception as e:
                print(f"✗ Error signing out user {user_id}: {str(e)}")

            # Disconnect WebSocket
            await self.disconnect(user_id)

        except Exception as e:
            print(f"✗ Error handling timeout for user {user_id}: {str(e)}")

    def get_connected_users(self) -> list:
        """
        Get a list of all connected user IDs.

        Returns:
            list: List of user IDs currently connected
        """
        return list(self.active_connections.keys())

    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if a user is currently connected.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            bool: True if user is connected, False otherwise
        """
        return user_id in self.active_connections

    def get_connection_stats(self) -> dict:
        """
        Get statistics about current WebSocket connections.

        Returns:
            dict: Dictionary containing connection statistics
        """
        return {
            "total_connections": len(self.active_connections),
            "connected_users": self.get_connected_users(),
            "ping_interval_seconds": self.PING_INTERVAL,
            "pong_timeout_seconds": self.PONG_TIMEOUT,
        }


# Global connection manager instance
manager = ConnectionManager()
