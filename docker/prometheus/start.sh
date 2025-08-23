#!/bin/sh
# Prometheus startup script with environment variable substitution

set -e

# Simple environment variable substitution using sed
sed -e "s/\${PROMETHEUS_SCRAPE_INTERVAL}/${PROMETHEUS_SCRAPE_INTERVAL}/g" \
    -e "s/\${PROMETHEUS_EVALUATION_INTERVAL}/${PROMETHEUS_EVALUATION_INTERVAL}/g" \
    /etc/prometheus/prometheus.yml.template > /etc/prometheus/prometheus.yml

echo "Generated Prometheus configuration:"
head -10 /etc/prometheus/prometheus.yml

# Start Prometheus with the processed configuration
exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=${PROMETHEUS_RETENTION_TIME} \
  --storage.tsdb.retention.size=${PROMETHEUS_RETENTION_SIZE} \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --web.enable-lifecycle \
  --web.enable-admin-api \
  --log.level=${PROMETHEUS_LOG_LEVEL}
