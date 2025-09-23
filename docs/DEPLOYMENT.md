# Inventory Service - Deployment Guide

**Container configuration, environment variables, and health checks for production deployment**

This guide covers everything needed to deploy the BookVerse Inventory Service in production environments, from local containers to Kubernetes clusters.

---

## 🐳 Container Deployment

### 📦 **Docker Configuration**

**Dockerfile Analysis:**
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run:**
```bash
# Build production image
docker build -t bookverse-inventory:latest .

# Run container
docker run -d \
  --name inventory-service \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/inventory.db \
  -e JWT_SECRET_KEY=your-production-secret \
  -v inventory-data:/app/data \
  bookverse-inventory:latest

# Verify deployment
docker logs inventory-service
curl http://localhost:8000/health
```

### 🔧 **Docker Compose**

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  inventory:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/inventory.db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - inventory-data:/app/data
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  inventory-data:
  redis-data:
```

**Deployment Commands:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f inventory

# Scale service
docker-compose up -d --scale inventory=3

# Update service
docker-compose pull && docker-compose up -d

# Cleanup
docker-compose down && docker volume prune
```

---

## ☸️ Kubernetes Deployment

### 🚀 **Basic Deployment**

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-service
  labels:
    app: inventory-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory-service
        version: v1.0.0
    spec:
      containers:
      - name: inventory
        image: bookverse/inventory:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: inventory-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: inventory-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: inventory-pvc
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: inventory-service
  labels:
    app: inventory-service
spec:
  selector:
    app: inventory-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: inventory-service-lb
  labels:
    app: inventory-service
spec:
  selector:
    app: inventory-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 🔐 **Secrets Management**

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: inventory-secrets
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  jwt-secret: <base64-encoded-jwt-secret>
  auth-token: <base64-encoded-auth-token>
```

**Create Secrets:**
```bash
# Create secrets from command line
kubectl create secret generic inventory-secrets \
  --from-literal=database-url='sqlite:///./data/inventory.db' \
  --from-literal=jwt-secret='your-super-secret-key' \
  --from-literal=auth-token='your-auth-token'

# Verify secrets
kubectl get secrets
kubectl describe secret inventory-secrets
```

### 💾 **Persistent Storage**

**pvc.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: inventory-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

**StatefulSet for Database:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: inventory-stateful
spec:
  serviceName: inventory-headless
  replicas: 1
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory-service
    spec:
      containers:
      - name: inventory
        image: bookverse/inventory:1.0.0
        volumeMounts:
        - name: data
          mountPath: /app/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
```

---

## ⚙️ Environment Configuration

### 🔧 **Environment Variables**

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `DATABASE_URL` | Yes | - | Database connection string | `sqlite:///./data/inventory.db` |
| `JWT_SECRET_KEY` | Yes | - | JWT signing secret | `your-super-secret-key-256-bits` |
| `JWT_ALGORITHM` | No | HS256 | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | 30 | Token expiration | `30` |
| `LOG_LEVEL` | No | INFO | Logging level | `INFO`, `DEBUG`, `WARNING` |
| `SERVICE_NAME` | No | bookverse-inventory | Service identifier | `bookverse-inventory` |
| `SERVICE_VERSION` | No | 1.0.0 | Service version | `1.0.0` |
| `PORT` | No | 8000 | Service port | `8000` |
| `HOST` | No | 0.0.0.0 | Bind address | `0.0.0.0` |
| `CORS_ORIGINS` | No | * | CORS allowed origins | `https://bookverse.com` |
| `MAX_CONNECTIONS` | No | 100 | Database connection pool size | `100` |
| `CACHE_TTL` | No | 300 | Cache TTL in seconds | `300` |

### 📁 **Configuration Files**

**Production Config (config/production.env):**
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@postgres:5432/inventory
DATABASE_ECHO=false
MAX_CONNECTIONS=20
POOL_SIZE=10

# Authentication
JWT_SECRET_KEY=your-production-secret-key-256-bits-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Configuration
SERVICE_NAME=bookverse-inventory
SERVICE_VERSION=1.0.0
LOG_LEVEL=INFO
PORT=8000
HOST=0.0.0.0

# Security
CORS_ORIGINS=https://bookverse.com,https://api.bookverse.com
ALLOWED_HOSTS=bookverse.com,api.bookverse.com

# Performance
CACHE_TTL=300
MAX_REQUEST_SIZE=10485760
RATE_LIMIT_PER_MINUTE=1000

# External Services
RECOMMENDATIONS_SERVICE_URL=http://recommendations:8001
CHECKOUT_SERVICE_URL=http://checkout:8002
AUTH_SERVICE_URL=http://auth:8003

# Monitoring
ENABLE_METRICS=true
METRICS_PATH=/metrics
HEALTH_CHECK_PATH=/health
```

**Staging Config (config/staging.env):**
```bash
# Inherit from production with overrides
DATABASE_URL=sqlite:///./data/staging_inventory.db
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ENABLE_DEBUG_ENDPOINTS=true
```

---

## 🏥 Health Checks & Monitoring

### 💚 **Health Check Implementation**

**Health Check Endpoint:**
```python
# app/health.py
from fastapi import APIRouter
from sqlalchemy import text
from app.database import get_db
import time
import psutil

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "response_time_ms": 5
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # Memory check
    memory = psutil.virtual_memory()
    checks["memory"] = {
        "status": "healthy" if memory.percent < 90 else "warning",
        "usage_percent": memory.percent,
        "available_mb": memory.available // 1024 // 1024
    }
    
    # Disk check
    disk = psutil.disk_usage('/')
    checks["disk"] = {
        "status": "healthy" if disk.percent < 85 else "warning",
        "usage_percent": disk.percent,
        "free_gb": disk.free // 1024 // 1024 // 1024
    }
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "checks": checks,
        "version": "1.0.0"
    }
```

### 📊 **Monitoring Metrics**

**Prometheus Metrics:**
```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Metrics definitions
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')
INVENTORY_ITEMS = Gauge('inventory_total_items', 'Total inventory items')

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")

# Middleware for automatic metrics collection
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

### 🚨 **Alerting Configuration**

**Prometheus Rules:**
```yaml
# prometheus-rules.yml
groups:
- name: inventory-service
  rules:
  - alert: InventoryServiceDown
    expr: up{job="inventory-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Inventory service is down"
      description: "Inventory service has been down for more than 1 minute"

  - alert: HighResponseTime
    expr: http_request_duration_seconds{job="inventory-service"} > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "Response time is above 1 second for 5 minutes"

  - alert: HighErrorRate
    expr: rate(http_requests_total{job="inventory-service",status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 10% for 2 minutes"
```

---

## 🔄 Deployment Strategies

### 🚀 **Rolling Deployment**

**Zero-Downtime Deployment:**
```bash
# Update deployment image
kubectl set image deployment/inventory-service \
  inventory=bookverse/inventory:1.1.0

# Monitor rollout
kubectl rollout status deployment/inventory-service

# Rollback if needed
kubectl rollout undo deployment/inventory-service
```

**Deployment Strategy:**
```yaml
# deployment-strategy.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  minReadySeconds: 30
  progressDeadlineSeconds: 600
```

### 🔵 **Blue-Green Deployment**

**Blue-Green Script:**
```bash
#!/bin/bash
# blue-green-deploy.sh

NEW_VERSION=$1
CURRENT_COLOR=$(kubectl get service inventory-service -o jsonpath='{.spec.selector.color}')
NEW_COLOR=$([ "$CURRENT_COLOR" = "blue" ] && echo "green" || echo "blue")

echo "Deploying version $NEW_VERSION as $NEW_COLOR..."

# Deploy new version
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-$NEW_COLOR
spec:
  replicas: 3
  selector:
    matchLabels:
      app: inventory-service
      color: $NEW_COLOR
  template:
    metadata:
      labels:
        app: inventory-service
        color: $NEW_COLOR
    spec:
      containers:
      - name: inventory
        image: bookverse/inventory:$NEW_VERSION
EOF

# Wait for deployment
kubectl wait --for=condition=available deployment/inventory-$NEW_COLOR --timeout=600s

# Health check
if curl -f http://inventory-$NEW_COLOR/health; then
  echo "Health check passed, switching traffic..."
  kubectl patch service inventory-service -p '{"spec":{"selector":{"color":"'$NEW_COLOR'"}}}'
  echo "Traffic switched to $NEW_COLOR"
else
  echo "Health check failed, rolling back..."
  kubectl delete deployment inventory-$NEW_COLOR
  exit 1
fi
```

### 🐥 **Canary Deployment**

**Canary Configuration:**
```yaml
# canary-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: inventory-rollout
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 2m}
      - setWeight: 40
      - pause: {duration: 2m}
      - setWeight: 60
      - pause: {duration: 2m}
      - setWeight: 80
      - pause: {duration: 2m}
      analysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: inventory-service
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory-service
    spec:
      containers:
      - name: inventory
        image: bookverse/inventory:1.1.0
```

---

## 🔐 Security Configuration

### 🛡️ **Security Best Practices**

**Security Context:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

**Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: inventory-netpol
spec:
  podSelector:
    matchLabels:
      app: inventory-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

### 🔒 **TLS Configuration**

**TLS Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: inventory-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - inventory.bookverse.com
    secretName: inventory-tls
  rules:
  - host: inventory.bookverse.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: inventory-service
            port:
              number: 80
```

---

## 📊 Performance Optimization

### ⚡ **Resource Configuration**

**Production Resources:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inventory-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inventory-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 🗄️ **Database Optimization**

**Connection Pooling:**
```python
# Database configuration for production
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

---

## 📞 Deployment Support

### 🤝 **Getting Help**
- **📖 [Service Overview](SERVICE_OVERVIEW.md)** - Business context and architecture
- **📚 [API Reference](API_REFERENCE.md)** - API documentation
- **🛠️ [Development Guide](DEVELOPMENT_GUIDE.md)** - Local development setup
- **🐛 [Issue Tracker](../../issues)** - Deployment issues and questions

### 🔧 **Operations Resources**
- **📊 [Monitoring Guide](../operations/MONITORING.md)** - Observability setup
- **⚡ [Performance Guide](../operations/PERFORMANCE.md)** - Optimization strategies
- **🔐 [Security Guide](../operations/SECURITY.md)** - Security configuration
- **💬 [Operations Discussions](../../discussions)** - Community support

---

*This deployment guide covers production-ready deployment patterns. For specific environment questions or advanced configurations, please engage with our [operations community](../../discussions).*
