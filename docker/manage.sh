#!/bin/bash
# Docker management script for MAX emulation infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.docker-env"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment variables if .docker-env exists
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
else
    print_warning "$ENV_FILE file not found"
fi

# Set default values if not provided in .docker-env
PUSHGATEWAY_PORT=${PUSHGATEWAY_PORT:-9091}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}
GRAFANA_PORT=${GRAFANA_PORT:-3000}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}
PROMETHEUS_SCRAPE_INTERVAL=${PROMETHEUS_SCRAPE_INTERVAL:-15s}
PROMETHEUS_EVALUATION_INTERVAL=${PROMETHEUS_EVALUATION_INTERVAL:-15s}
GRAFANA_REFRESH_INTERVAL=${GRAFANA_REFRESH_INTERVAL:-5s}
GRAFANA_DEFAULT_REFRESH=${GRAFANA_DEFAULT_REFRESH:-30s}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check .docker-env file
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error "$ENV_FILE file not found."
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting MAX emulation infrastructure..."
    check_docker
    check_env_file
    
    cd "$SCRIPT_DIR"
    docker-compose --env-file .docker-env up -d --build
    
    print_success "Services started successfully!"
    print_status "Access URLs:"
    echo "  • Pushgateway: http://localhost:${PUSHGATEWAY_PORT}"
    echo "  • Prometheus:  http://localhost:${PROMETHEUS_PORT}"
    echo "  • Grafana:     http://localhost:${GRAFANA_PORT} (admin/${GRAFANA_ADMIN_PASSWORD})"
}

# Function to stop services
stop_services() {
    print_status "Stopping MAX emulation infrastructure..."
    
    cd "$SCRIPT_DIR"
    docker-compose --env-file .docker-env down
    
    print_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting MAX emulation infrastructure..."
    stop_services
    sleep 2
    start_services
}

# Function to view logs
view_logs() {
    cd "$SCRIPT_DIR"
    if [ -n "$1" ]; then
        docker-compose --env-file .docker-env logs -f "$1"
    else
        docker-compose --env-file .docker-env logs -f
    fi
}

# Function to show status
show_status() {
    cd "$SCRIPT_DIR"
    docker-compose --env-file .docker-env ps
    
    print_status "Service health checks:"
    
    # Check Pushgateway
    if curl -s http://localhost:${PUSHGATEWAY_PORT}/metrics > /dev/null 2>&1; then
        print_success "Pushgateway: Running (http://localhost:${PUSHGATEWAY_PORT})"
    else
        print_warning "Pushgateway: Not accessible"
    fi
    
    # Check Prometheus
    if curl -s http://localhost:${PROMETHEUS_PORT}/-/healthy > /dev/null 2>&1; then
        print_success "Prometheus: Running (http://localhost:${PROMETHEUS_PORT})"
    else
        print_warning "Prometheus: Not accessible"
    fi
    
    # Check Grafana
    if curl -s http://localhost:${GRAFANA_PORT}/api/health > /dev/null 2>&1; then
        print_success "Grafana: Running (http://localhost:${GRAFANA_PORT})"
    else
        print_warning "Grafana: Not accessible"
    fi
}

# Function to clean up everything
cleanup() {
    print_status "Cleaning up MAX emulation infrastructure..."
    
    # Load env vars to get volume names
    check_env_file
    
    cd "$SCRIPT_DIR"
    docker-compose --env-file .docker-env down -v --rmi all --remove-orphans
    
    # Remove named volumes using env vars
    docker volume rm ${PROMETHEUS_VOLUME:-max-prometheus-data} ${GRAFANA_VOLUME:-max-grafana-data} ${PUSHGATEWAY_VOLUME:-max-pushgateway-data} 2>/dev/null || true
    
    # Remove network using env var
    docker network rm ${MONITORING_NETWORK:-max-monitoring} 2>/dev/null || true
    
    print_success "Cleanup completed!"
}

# Function to show configuration
show_config() {
    print_status "Current Configuration:"
    echo "  • Pushgateway Port: $PUSHGATEWAY_PORT"
    echo "  • Prometheus Port: $PROMETHEUS_PORT"
    echo "  • Grafana Port: $GRAFANA_PORT"
    echo "  • Prometheus Scrape Interval: $PROMETHEUS_SCRAPE_INTERVAL"
    echo "  • Prometheus Evaluation Interval: $PROMETHEUS_EVALUATION_INTERVAL"
    echo "  • Grafana Refresh Interval: $GRAFANA_REFRESH_INTERVAL"
    echo "  • Grafana Default Refresh: $GRAFANA_DEFAULT_REFRESH"
}

# Function to backup data
backup_data() {
    print_status "Backing up monitoring data..."
    
    # Load env vars to get volume names
    check_env_file
    
    BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup Prometheus data using env var
    docker run --rm -v ${PROMETHEUS_VOLUME:-max-prometheus-data}:/source -v "$BACKUP_DIR":/backup alpine \
        tar czf /backup/prometheus-data.tar.gz -C /source .
    
    # Backup Grafana data using env var
    docker run --rm -v ${GRAFANA_VOLUME:-max-grafana-data}:/source -v "$BACKUP_DIR":/backup alpine \
        tar czf /backup/grafana-data.tar.gz -C /source .
    
    print_success "Data backed up to $BACKUP_DIR"
}

# Function to show help
show_help() {
    cat << EOF
MAX Emulation Infrastructure Management Script

Usage: $0 [COMMAND]

Commands:
    start       Start all services (Pushgateway, Prometheus, Grafana)
    stop        Stop all services
    restart     Restart all services
    status      Show service status and health
    config      Show current configuration
    logs [svc]  Show logs (optionally for specific service)
    cleanup     Stop services and remove all data/volumes
    backup      Backup monitoring data
    help        Show this help message

Examples:
    $0 start                # Start all services
    $0 logs prometheus      # Show Prometheus logs
    $0 status              # Check service health
    $0 cleanup             # Complete cleanup

Service URLs:
    • Pushgateway: http://localhost:9091 (or custom port from .env)
    • Prometheus:  http://localhost:9090 (or custom port from .env)
    • Grafana:     http://localhost:3000 (or custom port from .env)
EOF
}

# Main command handling
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs "$2"
        ;;
    status)
        show_status
        ;;
    config)
        show_config
        ;;
    cleanup)
        read -p "This will remove all data. Are you sure? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup
        else
            print_status "Cleanup cancelled."
        fi
        ;;
    backup)
        backup_data
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
