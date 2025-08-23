#!/bin/sh
# Grafana startup script with environment variable substitution

set -e

# Process datasource template using sed
sed -e "s/\${GRAFANA_REFRESH_INTERVAL}/${GRAFANA_REFRESH_INTERVAL}/g" \
    /etc/grafana/provisioning/datasources/prometheus.yml.template > /etc/grafana/provisioning/datasources/prometheus.yml

# Process dashboards template (no variables to substitute currently, just copy)
cp /etc/grafana/provisioning/dashboards/dashboards.yml.template /etc/grafana/provisioning/dashboards/dashboards.yml

echo "Generated Grafana datasource configuration:"
cat /etc/grafana/provisioning/datasources/prometheus.yml

# Start Grafana
exec /run.sh
