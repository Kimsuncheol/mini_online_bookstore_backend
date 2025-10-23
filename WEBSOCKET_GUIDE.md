# WebSocket Implementation Guide

## Overview

This document describes the WebSocket implementation for real-time communication with connected clients, including automatic session timeout after 3 hours of inactivity.

## Architecture

### Components

1. **WebSocket Manager** (`app/services/websocket_manager.py`)
   - Manages all active WebSocket connections
   - Handles ping/pong heartbeat mechanism
   - Monitors connection timeouts
   - Broadcasts messages to clients

2. **WebSocket Router** (`app/routers/websocket.py`)
   - FastAPI WebSocket endpoints
   - Message routing and handling
   - Connection status endpoints

3. **Auth Service** (`app/services/auth_service.py`)
   - User sign-out functionality
   - Session management
   - Token invalidation

## Features

### ✅ Mission 1: Send Pings to Client

The server sends periodic ping messages to all connected clients every 30 seconds.

**How it works:**
```
Server sends ping → Client receives ping → Client responds with pong → Server records pong time
```

**Ping Message Format:**
```json
{
  "type": "ping",
  "timestamp": "2025-10-23T10:30:00.000000",
  "message": "Server heartbeat - please respond with pong"
}
```

**Expected Pong Response:**
```json
{
  "type": "pong"
}
```

### ✅ Mission 2: Automatic Sign-Out After 3 Hours

If a client doesn't respond with a pong message for **3 hours (10,800 seconds)**, the server automatically:

1. **Notifies the client** with a timeout message
2. **Signs out the user** via Firebase sign-out function
3. **Disconnects the WebSocket**

**Timeout Message:**
```json
{
  "type": "timeout",
  "message": "Your session has expired due to inactivity (3 hours). Please sign in again.",
  "timestamp": "2025-10-23T13:30:00.000000"
}
```

## WebSocket Endpoints

### Connection Endpoint

**URL:** `ws://localhost:8000/ws/connect/{user_id}`

**Description:** Establishes a WebSocket connection for a user

**Example:**
```
ws://localhost:8000/ws/connect/user123
```

**Client Message Types:**

| Type | Description | Example |
|------|-------------|---------|
| `pong` | Response to server ping | `{"type": "pong"}` |
| `message` | Regular user message | `{"type": "message", "data": {...}}` |
| `ping` | Client ping (optional) | `{"type": "ping", "timestamp": "..."}` |

### Status Endpoint

**URL:** `GET /ws/status/{user_id}`

**Description:** Check if a user is currently connected

**Response:**
```json
{
  "user_id": "user123",
  "is_connected": true,
  "status": "connected"
}
```

### Statistics Endpoint

**URL:** `GET /ws/stats`

**Description:** Get current WebSocket connection statistics

**Response:**
```json
{
  "total_connections": 5,
  "connected_users": ["user1", "user2", "user3", "user4", "user5"],
  "ping_interval_seconds": 30,
  "pong_timeout_seconds": 10800
}
```

### Send Message Endpoint

**URL:** `POST /ws/send/{user_id}`

**Description:** Send a message to a specific connected user

**Request Body:**
```json
{
  "type": "notification",
  "data": {
    "message": "Order shipped!",
    "order_id": "12345"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message sent successfully"
}
```

### Broadcast Endpoint

**URL:** `POST /ws/broadcast?exclude_user=user1`

**Description:** Broadcast a message to all connected users

**Request Body:**
```json
{
  "type": "announcement",
  "data": {
    "title": "System Maintenance",
    "message": "Server maintenance scheduled for tonight"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message broadcasted successfully",
  "recipients": 4
}
```

## Configuration

### Ping Interval

Currently set to **30 seconds** in `ConnectionManager.__init__()`:
```python
self.PING_INTERVAL = 30  # seconds
```

To change, modify:
```python
self.PING_INTERVAL = 60  # Change to 60 seconds
```

### Pong Timeout

Currently set to **3 hours (10,800 seconds)** in `ConnectionManager.__init__()`:
```python
self.PONG_TIMEOUT = 3 * 60 * 60  # 3 hours = 10800 seconds
```

To change, modify:
```python
self.PONG_TIMEOUT = 1 * 60 * 60  # Change to 1 hour
```

### Timeout Check Interval

The server checks for timeouts every **60 seconds**:
```python
await asyncio.sleep(60)  # Check every minute
```

## Client Implementation Example

### JavaScript/TypeScript Client

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private userId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(userId: string) {
    this.userId = userId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `ws://localhost:8000/ws/connect/${this.userId}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("✓ Connected to server");
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
          console.error("✗ WebSocket error:", error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("📴 Disconnected from server");
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: any): void {
    switch (message.type) {
      case "ping":
        console.log("📥 Ping received, sending pong...");
        this.sendPong();
        break;

      case "timeout":
        console.warn("⏱️ Session timeout:", message.message);
        // Redirect to login
        this.disconnect();
        window.location.href = "/login";
        break;

      case "notification":
        console.log("📨 Notification:", message.data);
        // Handle notification
        break;

      default:
        console.log("ℹ️ Message:", message);
    }
  }

  private sendPong(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "pong" }));
      console.log("📤 Pong sent to server");
    }
  }

  sendMessage(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "message", data }));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      console.log(`Attempting to reconnect in ${delay}ms...`);

      setTimeout(() => {
        this.connect().catch((error) => {
          console.error("Reconnect failed:", error);
        });
      }, delay);
    }
  }
}

// Usage
const client = new WebSocketClient("user123");
await client.connect();
```

## Database Changes Required

When a user signs out due to timeout, the following fields are updated in the `members` collection:

```firestore
members/{user_id}
  - is_signed_in: false
  - last_sign_out_at: <current_timestamp>
  - updated_at: <current_timestamp>
```

Additionally, in the `sessions` collection (if used):

```firestore
sessions/{session_id}
  - is_active: false
  - signed_out_at: <current_timestamp>
```

## Error Handling

The system handles the following error scenarios:

1. **Connection Loss:** Client can reconnect with exponential backoff
2. **Network Timeout:** Server detects missing pong and signs out user
3. **Invalid Messages:** Unknown message types are logged and ignored
4. **WebSocket Errors:** Errors are logged and connection is cleaned up

## Monitoring

### Check Connected Users

```bash
curl http://localhost:8000/ws/stats
```

### Check Specific User Status

```bash
curl http://localhost:8000/ws/status/user123
```

### Send Test Message

```bash
curl -X POST http://localhost:8000/ws/send/user123 \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "message": "Hello User"}'
```

### Broadcast Message

```bash
curl -X POST http://localhost:8000/ws/broadcast \
  -H "Content-Type: application/json" \
  -d '{"type": "announcement", "message": "Test broadcast"}'
```

## Security Considerations

1. **User ID Validation:** In production, validate user_id from authentication tokens
2. **Message Validation:** Sanitize all incoming messages
3. **Rate Limiting:** Implement rate limiting for message sending
4. **HTTPS/WSS:** Use secure WebSocket (WSS) in production
5. **CORS:** Configure CORS appropriately for your frontend domain

## Troubleshooting

### Client not receiving pings
- Check if WebSocket connection is open
- Verify client is properly listening for messages
- Check server logs for errors

### User not being signed out after timeout
- Verify Firebase credentials are configured
- Check if `auth_service.sign_out_user()` is being called
- Check Firestore rules allow write access to `members` collection

### High memory usage with many connections
- Check if old connections are being properly cleaned up
- Monitor the `active_connections` dictionary size
- Consider using connection pooling

## Future Enhancements

- [ ] Implement message queuing for offline clients
- [ ] Add message encryption
- [ ] Implement client-side acknowledgment for critical messages
- [ ] Add analytics/logging for connection events
- [ ] Implement connection rate limiting
- [ ] Add support for room-based broadcasting
