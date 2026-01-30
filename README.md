# Widget Processing Service

Asynchronous widget processing service with FastAPI, Celery, PostgreSQL, and Redis.

## Overview

This service provides an API for submitting widgets for processing. The processing is handled asynchronously in the background using Celery workers. The service implements complex business logic including palindrome detection, prime number checking, and quantum simulation.

## Features

- **Asynchronous Processing**: Background task processing with Celery
- **Rate Limiting**: Sophisticated rate limiting with priority request support
- **Quantum Simulation**: Business logic that simulates quantum processing with probabilistic outcomes
- **RESTful API**: FastAPI-based REST API with automatic documentation
- **Containerized**: Fully containerized with Docker and Docker Compose

## Architecture

- **FastAPI**: Web framework for the REST API
- **Celery**: Distributed task queue for asynchronous processing
- **PostgreSQL**: Relational database for persistent storage
- **Redis**: Message broker for Celery and cache for rate limiting
- **SQLAlchemy**: ORM for database interactions

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd widget-processing-service
```

### 2. Build and start the services
```bash
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- FastAPI application (port 8000)
- Celery worker

### 3. Access the API

The API will be available at: `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## API Endpoints

### POST /widgets

**Required endpoint as per assignment specification.**

Create a new widget for processing.

**Request Headers:**
- `X-User-ID` (required): User identifier for rate limiting
- `X-Priority-Request` (optional): Set to "true" for priority processing

**Request Body:**
```json
{
  "name": "retro-encabulator",
  "complexity_score": 83
}
```

**Response (202 Accepted):**
```json
{
  "widget_id": 1,
  "status": "pending"
}
```

**Rate Limits:**
- Normal requests: 5 per minute per user
- Priority requests: 2 per hour per user (bypasses normal limit)

### GET /widgets/{widget_id}

**Status polling endpoint** - necessary for clients to check widget processing status after receiving 202 Accepted response.

**Response:**
```json
{
  "id": 1,
  "name": "retro-encabulator",
  "complexity_score": 83,
  "status": "success",
  "created_at": "2024-01-29T10:30:00",
  "updated_at": "2024-01-29T10:30:15"
}
```

## Development

### Viewing logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Stopping the services
```bash
docker-compose down
```

### Stopping and removing all data
```bash
docker-compose down -v
```

## Example Usage

### Creating a widget with curl
```bash
# Normal request
curl -X POST "http://localhost:8000/widgets" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{"name": "level-sensor", "complexity_score": 42}'

# Priority request
curl -X POST "http://localhost:8000/widgets" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -H "X-Priority-Request: true" \
  -d '{"name": "quantum-widget", "complexity_score": 73}'
```

### Checking widget status
```bash
curl "http://localhost:8000/widgets/1"
```
