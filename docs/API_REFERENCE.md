# Inventory Service - API Reference

**Complete REST API documentation for the BookVerse Inventory Service**

This reference provides comprehensive documentation for all API endpoints, request/response schemas, authentication requirements, and error handling patterns.

---

## 🔗 Base URL & Authentication

### 🌐 **Service Endpoints**

| Environment | Base URL | Purpose |
|-------------|----------|---------|
| **Local** | `http://localhost:8000` | Development and testing |
| **Development** | `https://inventory-dev.bookverse.com` | Development environment |
| **Staging** | `https://inventory-staging.bookverse.com` | Pre-production testing |
| **Production** | `https://inventory.bookverse.com` | Production environment |

### 🔑 **Authentication**

All API endpoints require authentication using JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

**Authentication Flow:**
```bash
# Obtain JWT token
curl -X POST https://auth.bookverse.com/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books
```

---

## 📚 Product Catalog Endpoints

### 📋 **List Books**

Retrieve a paginated list of books with optional filtering and sorting.

```http
GET /books
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Number of results per page (1-100) |
| `offset` | integer | 0 | Number of results to skip |
| `genre` | string | - | Filter by genre (e.g., "fiction", "technology") |
| `author` | string | - | Filter by author name (partial match) |
| `min_price` | decimal | - | Minimum price filter |
| `max_price` | decimal | - | Maximum price filter |
| `sort` | string | "title" | Sort field: "title", "author", "price", "rating", "date" |
| `order` | string | "asc" | Sort order: "asc" or "desc" |
| `available_only` | boolean | false | Show only books with available stock |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "https://inventory.bookverse.com/books?genre=technology&min_price=10&limit=10&sort=rating&order=desc"
```

**Response:**
```json
{
  "books": [
    {
      "id": 123,
      "title": "Python Programming Mastery",
      "author": "Jane Smith",
      "isbn": "978-0123456789",
      "description": "Comprehensive guide to Python programming with real-world examples.",
      "price": 29.99,
      "genre": "technology",
      "publication_date": "2023-06-15",
      "rating": 4.8,
      "image_url": "https://images.bookverse.com/books/123.jpg",
      "stock": {
        "available": 25,
        "total": 30,
        "reserved": 5
      },
      "created_at": "2023-06-01T10:00:00Z",
      "updated_at": "2023-12-01T15:30:00Z"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 150,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "genre": "technology",
    "min_price": 10,
    "sort": "rating",
    "order": "desc"
  }
}
```

### 📖 **Get Book Details**

Retrieve detailed information for a specific book.

```http
GET /books/{book_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `book_id` | integer | Yes | Unique book identifier |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books/123
```

**Response:**
```json
{
  "id": 123,
  "title": "Python Programming Mastery",
  "author": "Jane Smith",
  "isbn": "978-0123456789",
  "description": "Comprehensive guide to Python programming with real-world examples and advanced techniques.",
  "price": 29.99,
  "genre": "technology",
  "publication_date": "2023-06-15",
  "rating": 4.8,
  "review_count": 247,
  "image_url": "https://images.bookverse.com/books/123.jpg",
  "publisher": "Tech Books Publishing",
  "pages": 450,
  "language": "English",
  "stock": {
    "available": 25,
    "total": 30,
    "reserved": 5,
    "reorder_point": 10,
    "last_restocked": "2023-11-15T09:00:00Z"
  },
  "metadata": {
    "weight": "1.2kg",
    "dimensions": "23.5 x 15.5 x 3.2 cm",
    "tags": ["python", "programming", "software-development", "beginners"]
  },
  "created_at": "2023-06-01T10:00:00Z",
  "updated_at": "2023-12-01T15:30:00Z"
}
```

---

## 🔍 Search & Discovery Endpoints

### 🔎 **Search Books**

Perform full-text search across the book catalog with advanced filtering.

```http
GET /books/search
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (title, author, description, keywords) |
| `limit` | integer | No | Results per page (1-100, default: 20) |
| `offset` | integer | No | Results to skip (default: 0) |
| `genre` | string | No | Filter by genre |
| `author` | string | No | Filter by author |
| `min_price` | decimal | No | Minimum price |
| `max_price` | decimal | No | Maximum price |
| `min_rating` | decimal | No | Minimum rating (0-5) |
| `sort` | string | No | Sort by: "relevance", "price", "rating", "date" |
| `order` | string | No | Sort order: "asc", "desc" |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "https://inventory.bookverse.com/books/search?q=python%20programming&genre=technology&min_rating=4.0&sort=rating&order=desc"
```

**Response:**
```json
{
  "query": "python programming",
  "results": [
    {
      "id": 123,
      "title": "Python Programming Mastery",
      "author": "Jane Smith",
      "isbn": "978-0123456789",
      "price": 29.99,
      "rating": 4.8,
      "genre": "technology",
      "image_url": "https://images.bookverse.com/books/123.jpg",
      "stock": {
        "available": 25,
        "total": 30
      },
      "relevance_score": 0.95,
      "match_highlights": {
        "title": ["<em>Python</em> <em>Programming</em> Mastery"],
        "description": ["Comprehensive guide to <em>Python</em> <em>programming</em>"]
      }
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 42,
    "has_next": true
  },
  "search_metadata": {
    "query_time_ms": 15,
    "total_indexed": 10000,
    "filters_applied": {
      "genre": "technology",
      "min_rating": 4.0
    }
  },
  "suggestions": [
    "python web development",
    "python data science",
    "python machine learning"
  ]
}
```

### 📊 **Get Search Suggestions**

Get auto-complete suggestions for search queries.

```http
GET /books/suggestions
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Partial search query |
| `limit` | integer | No | Number of suggestions (1-10, default: 5) |
| `type` | string | No | Suggestion type: "all", "title", "author", "genre" |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "https://inventory.bookverse.com/books/suggestions?q=pyth&limit=5"
```

**Response:**
```json
{
  "query": "pyth",
  "suggestions": [
    {
      "text": "python programming",
      "type": "title",
      "count": 25
    },
    {
      "text": "python data science",
      "type": "title", 
      "count": 18
    },
    {
      "text": "python web development",
      "type": "title",
      "count": 12
    }
  ]
}
```

---

## 📦 Inventory Management Endpoints

### 📊 **Check Book Availability**

Get real-time stock information for a specific book.

```http
GET /books/{book_id}/availability
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `book_id` | integer | Yes | Unique book identifier |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books/123/availability
```

**Response:**
```json
{
  "book_id": 123,
  "stock": {
    "available": 25,
    "total": 30,
    "reserved": 5,
    "in_transit": 10,
    "reorder_point": 10,
    "max_stock": 50
  },
  "availability_status": "available",
  "estimated_restock": "2024-01-15T00:00:00Z",
  "last_updated": "2023-12-01T15:30:00Z",
  "reservations": [
    {
      "reservation_id": "order_456",
      "quantity": 2,
      "expires_at": "2023-12-02T15:30:00Z"
    }
  ]
}
```

### 🔒 **Reserve Inventory**

Reserve stock for a pending order.

```http
POST /books/{book_id}/reserve
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `book_id` | integer | Yes | Unique book identifier |

**Request Body:**
```json
{
  "quantity": 2,
  "reservation_id": "order_456",
  "expires_at": "2023-12-02T15:30:00Z",
  "customer_id": "user_789"
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quantity` | integer | Yes | Number of items to reserve (1-10) |
| `reservation_id` | string | Yes | Unique reservation identifier |
| `expires_at` | datetime | No | Reservation expiration (default: 30 minutes) |
| `customer_id` | string | No | Customer identifier for tracking |

**Example Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 2, "reservation_id": "order_456"}' \
  https://inventory.bookverse.com/books/123/reserve
```

**Response:**
```json
{
  "reservation": {
    "id": "res_123456",
    "book_id": 123,
    "quantity": 2,
    "reservation_id": "order_456",
    "customer_id": "user_789",
    "status": "confirmed",
    "created_at": "2023-12-01T15:30:00Z",
    "expires_at": "2023-12-01T16:00:00Z"
  },
  "remaining_stock": {
    "available": 23,
    "total": 30,
    "reserved": 7
  }
}
```

### 🔓 **Release Reservation**

Release a previously made reservation.

```http
DELETE /books/{book_id}/reserve/{reservation_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `book_id` | integer | Yes | Unique book identifier |
| `reservation_id` | string | Yes | Reservation identifier to release |

**Example Request:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books/123/reserve/order_456
```

**Response:**
```json
{
  "message": "Reservation released successfully",
  "released_quantity": 2,
  "updated_stock": {
    "available": 25,
    "total": 30,
    "reserved": 5
  }
}
```

---

## 📊 Analytics & Reporting Endpoints

### 📈 **Get Inventory Metrics**

Retrieve inventory analytics and metrics.

```http
GET /analytics/inventory
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period: "day", "week", "month" (default: "day") |
| `start_date` | date | No | Start date for metrics (ISO 8601) |
| `end_date` | date | No | End date for metrics (ISO 8601) |
| `genre` | string | No | Filter by genre |

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "https://inventory.bookverse.com/analytics/inventory?period=week&genre=technology"
```

**Response:**
```json
{
  "metrics": {
    "total_books": 1500,
    "total_stock": 15000,
    "available_stock": 12500,
    "reserved_stock": 2500,
    "low_stock_items": 45,
    "out_of_stock_items": 12
  },
  "trends": {
    "stock_turnover_rate": 2.5,
    "days_of_inventory": 146,
    "reservation_rate": 0.85,
    "stockout_frequency": 0.008
  },
  "top_genres": [
    {
      "genre": "technology",
      "book_count": 350,
      "stock_value": 8750.50
    }
  ],
  "period": {
    "start": "2023-11-25T00:00:00Z",
    "end": "2023-12-01T23:59:59Z",
    "days": 7
  }
}
```

---

## 🏥 Health & Status Endpoints

### 💚 **Health Check**

Check service health and dependencies.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "timestamp": "2023-12-01T15:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "connection_pool": {
        "active": 5,
        "idle": 15,
        "max": 20
      }
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 2,
      "hit_rate": 0.85
    },
    "external_services": {
      "auth_service": {
        "status": "healthy",
        "response_time_ms": 25
      }
    }
  },
  "uptime_seconds": 86400
}
```

### 📊 **Service Metrics**

Get detailed service performance metrics.

```http
GET /metrics
```

**Response:**
```json
{
  "performance": {
    "requests_per_second": 150.5,
    "average_response_time_ms": 45,
    "p95_response_time_ms": 120,
    "p99_response_time_ms": 250,
    "error_rate": 0.002
  },
  "resources": {
    "cpu_usage_percent": 35.5,
    "memory_usage_mb": 512,
    "memory_usage_percent": 25.6,
    "disk_usage_percent": 15.2
  },
  "database": {
    "active_connections": 8,
    "query_time_avg_ms": 12,
    "slow_queries_count": 2
  }
}
```

---

## ❌ Error Responses

### 🚨 **Error Format**

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "Book with ID 999 not found",
    "details": {
      "book_id": 999,
      "available_books": 1500
    },
    "timestamp": "2023-12-01T15:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### 📋 **Error Codes**

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `INVALID_REQUEST` | Malformed request or invalid parameters |
| `400` | `VALIDATION_ERROR` | Request validation failed |
| `401` | `UNAUTHORIZED` | Missing or invalid authentication |
| `403` | `FORBIDDEN` | Insufficient permissions |
| `404` | `BOOK_NOT_FOUND` | Requested book does not exist |
| `404` | `RESERVATION_NOT_FOUND` | Reservation does not exist |
| `409` | `INSUFFICIENT_STOCK` | Not enough inventory available |
| `409` | `RESERVATION_CONFLICT` | Reservation already exists |
| `422` | `STOCK_UNAVAILABLE` | Book is out of stock |
| `429` | `RATE_LIMIT_EXCEEDED` | Too many requests |
| `500` | `INTERNAL_ERROR` | Server error |
| `503` | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### 🔧 **Error Examples**

**Validation Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "fields": {
        "quantity": "Must be between 1 and 10",
        "reservation_id": "Required field missing"
      }
    },
    "timestamp": "2023-12-01T15:30:00Z",
    "request_id": "req_123456789"
  }
}
```

**Insufficient Stock:**
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Not enough inventory available for reservation",
    "details": {
      "requested": 5,
      "available": 2,
      "book_id": 123
    },
    "timestamp": "2023-12-01T15:30:00Z",
    "request_id": "req_123456789"
  }
}
```

---

## 🔄 Rate Limiting

### 📊 **Rate Limits**

| Endpoint Category | Requests per Minute | Burst Limit |
|-------------------|-------------------|-------------|
| **Read Operations** | 1000 | 100 |
| **Search Operations** | 500 | 50 |
| **Write Operations** | 200 | 20 |
| **Analytics** | 100 | 10 |

### 📈 **Rate Limit Headers**

All responses include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1638360000
```

---

## 🧪 Testing & Examples

### 🔧 **cURL Examples**

**Complete Search Workflow:**
```bash
# 1. Search for books
curl -H "Authorization: Bearer <token>" \
  "https://inventory.bookverse.com/books/search?q=python&limit=5"

# 2. Get detailed book information
curl -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books/123

# 3. Check availability
curl -H "Authorization: Bearer <token>" \
  https://inventory.bookverse.com/books/123/availability

# 4. Reserve inventory
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 2, "reservation_id": "order_456"}' \
  https://inventory.bookverse.com/books/123/reserve
```

### 🐍 **Python Client Example**

```python
import requests
from datetime import datetime, timedelta

class InventoryClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def search_books(self, query, **filters):
        params = {"q": query, **filters}
        response = requests.get(
            f"{self.base_url}/books/search",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def reserve_book(self, book_id, quantity, reservation_id):
        data = {
            "quantity": quantity,
            "reservation_id": reservation_id,
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
        response = requests.post(
            f"{self.base_url}/books/{book_id}/reserve",
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
client = InventoryClient("https://inventory.bookverse.com", "your_token")
results = client.search_books("python programming", genre="technology")
reservation = client.reserve_book(123, 2, "order_456")
```

---

## 📞 API Support

### 🤝 **Getting Help**
- **📖 [Service Overview](SERVICE_OVERVIEW.md)** - Business context and capabilities
- **🛠️ [Development Guide](DEVELOPMENT_GUIDE.md)** - Local development setup
- **🚀 [Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **🐛 [Issue Tracker](../../issues)** - API bugs and enhancement requests

### 🔧 **Integration Support**
- **📝 [Integration Examples](../examples/)** - Client implementations
- **⚡ [Performance Guide](../performance/)** - Optimization strategies
- **💬 [API Discussions](../../discussions)** - Community support

---

*This API reference is automatically generated from OpenAPI specifications. For the most up-to-date documentation, visit our [interactive API docs](https://inventory.bookverse.com/docs).*
