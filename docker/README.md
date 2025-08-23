# Prometheus Metrics Emulator (PromEmu) Docker Infrastructure

This directory contains Docker configurations for a complete Prometheus monitoring stack to support the Prometheus Metrics Emulator (PromEmu).

## Table of Contents

- [Architecture](#architecture)
- [Services](#services)
  - [Pushgateway (Port 9091)](#pushgateway-port-9091)
  - [Prometheus (Port 9090)](#prometheus-port-9090)
  - [Grafana (Port 3000)](#grafana-port-3000)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Start Everything](#start-everything)
  - [Access Services](#access-services)
  - [Check Status](#check-status)
- [Management Script](#management-script)
- [Configuration Files](#configuration-files)
  - [Docker Compose](#docker-compose)
  - [Pushgateway](#pushgateway)
  - [Prometheus](#prometheus)
  - [Grafana](#grafana)
- [Data Persistence](#data-persistence)
  - [Backup Data](#backup-data)
- [Networking](#networking)
- [Health Checks](#health-checks)
- [Monitoring Emulated Metrics](#monitoring-emulated-metrics)
  - [Prometheus Queries](#prometheus-queries)
  - [Grafana Dashboards](#grafana-dashboards)
- [Alerting Rules](#alerting-rules)
- [Troubleshooting](#troubleshooting)
  - [Services Won't Start](#services-wont-start)
  - [Missing Data](#missing-data)
  - [Performance Issues](#performance-issues)
  - [Reset Everything](#reset-everything)
- [Integration with Emulation](#integration-with-emulation)
- [Production Considerations](#production-considerations)

## Architecture

```
┌─────────────────┐    ┌────────────────────┐    ┌─────────────────┐
│   Pushgateway   │◄───│  Emulation Script  │    │     Grafana     │
│   Port: 9091    │    │  (Python)          │    │   Port: 3000    │
└─────────┬───────┘    └────────────────────┘    └─────────┬───────┘
          │                                                │
          │                                                │
          ▼                                                ▼
┌─────────────────┐                              ┌─────────────────┐
│   Prometheus    │◄─────────────────────────────│  Data Storage   │
│   Port: 9090    │                              │   (Volumes)     │
└─────────────────┘                              └─────────────────┘
```

## Services

### Pushgateway (Port 9091)
- **Image**: `prom/pushgateway:v1.11.1`
- **Purpose**: Receives metrics from emulation script
- **Features**:
  - Persistent storage with 5-minute intervals
  - Health checks
  - Data persistence in Docker volume

### Prometheus (Port 9090)  
- **Image**: `prom/prometheus:v3.5.0`
- **Purpose**: Scrapes metrics from Pushgateway, stores time-series data
- **Features**:
  - 7-day retention policy
  - 10GB storage limit
  - Custom alerting rules for emulation metrics
  - API access for external tools

### Grafana (Port 3000)
- **Image**: `grafana/grafana:12.1.0`
- **Purpose**: Visualization and dashboards
- **Credentials**: `admin` / `admin`
- **Features**:
  - Pre-configured Prometheus datasource
  - Automatic dashboard provisioning
  - Additional plugins (piechart, worldmap)
  - Anonymous viewer access

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports 3000, 9090, 9091 available

### Start Everything
```bash
# Start all services
./manage.sh start

# Or using docker-compose directly
docker-compose up -d --build
```

### Access Services
- **Pushgateway**: http://localhost:9091
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Check Status
```bash
./manage.sh status
```

## Management Script

The `manage.sh` script provides convenient management commands:

```bash
./manage.sh start     # Start all services
./manage.sh stop      # Stop all services  
./manage.sh restart   # Restart all services
./manage.sh status    # Show service status
./manage.sh config    # Show current configuration
./manage.sh logs      # Show all logs
./manage.sh logs grafana  # Show specific service logs
./manage.sh backup    # Backup data volumes
./manage.sh cleanup   # Complete cleanup (removes all data)
```

## Configuration Files

### Docker Compose
- `docker-compose.yml` - Main orchestration file
- Defines services, networks, volumes, and dependencies

### Pushgateway
- `pushgateway/Dockerfile` - Custom build with health checks
- Persistent storage in `/data` volume
- Runs as non-root user for security

### Prometheus
- `prometheus/Dockerfile` - Custom build with config files
- `prometheus/prometheus.yml` - Main configuration
- `prometheus/rules/emulation_alerts.yml` - Alerting rules
- Scrapes Pushgateway every 15 seconds (configurable)

### Grafana
- `grafana/Dockerfile` - Custom build with plugins
- `grafana/provisioning/datasources/` - Auto-configured datasources
- `grafana/provisioning/dashboards/` - Auto-provisioned dashboards
- `grafana/dashboards/emulation_overview.json` - Main dashboard

## Data Persistence

All data is stored in Docker named volumes:
- `max-prometheus-data` - Prometheus time-series data
- `max-grafana-data` - Grafana dashboards and settings  
- `max-pushgateway-data` - Pushgateway metric buffer

### Backup Data
```bash
./manage.sh backup
```

Creates timestamped backup in `backups/` directory.

## Networking

Services communicate via dedicated Docker network:
- Network: `max-monitoring`
- Internal DNS resolution between services
- Only necessary ports exposed to host

## Health Checks

All services include health checks:
- **Pushgateway**: HTTP GET `/metrics`
- **Prometheus**: HTTP GET `/-/healthy`  
- **Grafana**: HTTP GET `/api/health`

Health check parameters:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 10-30 seconds

## Monitoring Emulated Metrics

### Prometheus Queries
```promql
# CPU usage across all hosts
cpu_usage_percent

# Memory usage for specific host
memory_usage_percent{host="worker-01"}

# Heavy task status
heavy_task_active

# Database connections
db_connections
```

### Grafana Dashboards
The included dashboard shows:
- CPU usage by host (time series)
- Memory usage by host (time series)  
- Heavy task status (stat panel)
- Host distribution by role (pie chart)
- Database connections (time series)
- Network throughput (time series)

## Alerting Rules

Pre-configured alerts:
- **HighCPUUsage**: CPU > 80% for 2 minutes
- **CriticalCPUUsage**: CPU > 95% for 1 minute
- **HighMemoryUsage**: Memory > 85% for 3 minutes
- **HeavyTaskActive**: Heavy task started
- **PushgatewayDown**: Service unavailable
- **PrometheusDown**: Service unavailable

## Troubleshooting

### Services Won't Start
```bash
# Check Docker is running
docker info

# Check port availability
netstat -tulpn | grep -E ':(3000|9090|9091)'

# View service logs
./manage.sh logs [service]
```

### Missing Data
```bash
# Verify Pushgateway has metrics
curl http://localhost:9091/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Grafana datasource
curl -u admin:admin123 http://localhost:3000/api/datasources
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check volume sizes
docker system df -v

# Reduce Prometheus retention (current default: 7d)
# Edit .docker-env: PROMETHEUS_RETENTION_TIME=3d
```

### Reset Everything
```bash
./manage.sh cleanup
./manage.sh start
```

## Integration with Emulation

The emulation script pushes metrics to Pushgateway:

```python
from core.emulator import MetricsEmulator
from core.config_example import get_example_config

# Configure to use local Pushgateway
config = get_example_config()
config.pushgateway_url = 'http://localhost:9091'

# Run emulation
emulator = MetricsEmulator(config)
await emulator.run_for_duration(1800)  # 30 minutes
```

## Production Considerations

For production use, consider:

1. **Security**:
   - Change default Grafana password
   - Enable HTTPS with reverse proxy
   - Configure authentication

2. **Persistence**:
   - Use external storage for volumes
   - Set up backup automation
   - Configure retention policies

3. **Monitoring**:
   - Add Alertmanager for notifications
   - Configure external receivers (email, Slack)
   - Monitor the monitoring stack itself

4. **Performance**:
   - Tune Prometheus storage settings
   - Configure appropriate resource limits
   - Use SSD storage for better performance
