# Technical Notes and Design Decisions

## Question 1: Race Conditions and Data Inconsistency

### What potential race conditions or data inconsistency issues could arise between the API and the Celery worker updating the same database record? How did your design mitigate them?

#### Potential Issues

**Lost Updates**: If multiple workers process the same task or the API reads while a worker writes, updates could be lost.

**Dirty Reads**: The API might read a widget status while the worker is in the middle of updating it, seeing an inconsistent state.

**Double Processing**: If task acknowledgment fails, the same widget might be processed multiple times.

#### Mitigation Strategies

**Database Transaction Isolation**: Using SQLAlchemy's session management with proper commit/rollback handling. Each database operation is wrapped in a transaction with `pool_pre_ping=True` to ensure connection validity.

**Celery Configuration**:
- `task_acks_late=True`: Task acknowledged only after completion
- `task_reject_on_worker_lost=True`: Tasks re-queued if worker crashes
- `worker_prefetch_multiplier=1`: Workers fetch one task at a time
- `max_retries=3`: Limited retries prevent infinite loops

**Idempotent Operations**: The widget status update is idempotent—running it multiple times produces the same result. Status transitions from "pending" to "success/failed" can safely be repeated.

**Status-Based Processing**: Workers only process widgets in "pending" status. Once updated, the same widget won't be processed again even if the task is retried.

#### Further Improvements

**Optimistic Locking**: Add a version column to detect concurrent modifications and use `with_for_update()` for row-level locking.

**Distributed Locking**: Use Redis distributed locks to ensure only one worker processes a widget at a time.

**Event Sourcing**: Store all state changes as events rather than updating in place, providing a complete audit trail.

---

## Question 2: Real-Time Status Updates Without Polling

### The current API design returns a 202 and forces the client to poll for status. How would you redesign the system to provide real-time status updates to the user without polling? Describe the technologies you would use and the new architecture.

#### Current Limitations

The 202 Accepted response requires clients to poll the GET endpoint repeatedly, which:
- Wastes bandwidth and server resources
- Introduces latency in status updates
- Creates unnecessary database load

#### Solution: WebSockets with Redis Pub/Sub

**Architecture**: Client connects via WebSocket to FastAPI. Celery worker publishes status updates to Redis Pub/Sub. FastAPI subscribes to Redis and broadcasts updates to connected WebSocket clients.

**Implementation**:

1. **WebSocket Connection Manager in FastAPI**: Manages active WebSocket connections per widget_id and broadcasts status updates to all connected clients.

2. **Redis Pub/Sub**: Worker publishes status updates to Redis channel `widget_status:{widget_id}` after processing completes.

3. **FastAPI Subscriber**: Background task subscribes to Redis pattern `widget_status:*` and broadcasts updates to connected WebSocket clients.

**Client Usage**: Client creates widget via POST, receives widget_id, then opens WebSocket connection to receive real-time status updates.

---

## Question 3: Poison Pill Message Handling

### Explain your strategy for handling a "poison pill" message in the Celery queue—a task that repeatedly fails and gets re-queued, blocking other tasks.

#### Mitigation Strategies

**Maximum Retry Limit**: Configure `max_retries=3` on Celery tasks. After maximum retries, mark the widget as permanently failed instead of re-queuing.

**Dead Letter Queue**: Failed tasks after max retries are moved to a separate queue for manual inspection. Use Celery's `on_failure` callback to log failed tasks with full context (task_id, args, exception, traceback, timestamp).

**Task Timeouts**: Set both hard (`time_limit=300`) and soft (`soft_time_limit=270`) timeouts. Soft timeout allows graceful cleanup before hard kill.

**Circuit Breaker Pattern**: Track failure count per widget in Redis. If failures exceed threshold (e.g., 5), stop processing that widget and mark as permanently failed. Reset counter on success.

**Monitoring and Alerting**: Log all task executions with metrics (execution_time, status, retry_count). Track failures in Redis for real-time monitoring. Create admin endpoints to view DLQ and manually retry tasks.

#### Best Practices

- Set hard limits on retries, timeouts, and queue sizes
- Isolate failures using DLQ to prevent blocking
- Monitor actively and alert on suspicious patterns
- Fail fast rather than retry indefinitely
- Provide manual controls for operators
- Log comprehensively for debugging
- Ensure operations are idempotent

---
