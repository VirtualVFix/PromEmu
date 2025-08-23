FROM grafana/grafana:12.1.0

# Install additional plugins
USER root
RUN grafana cli plugins install grafana-piechart-panel && \
    grafana cli plugins install grafana-worldmap-panel

# Copy provisioning configuration and startup script
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /etc/grafana/dashboards/
COPY start.sh /usr/local/bin/start.sh

# Create grafana user directories and make startup script executable
RUN mkdir -p /var/lib/grafana/dashboards && \
    chown -R 472:472 /var/lib/grafana /etc/grafana/provisioning /etc/grafana/dashboards && \
    chmod +x /usr/local/bin/start.sh

# Switch back to grafana user (uid 472)
USER 472

# Set the entrypoint to our startup script
ENTRYPOINT ["/usr/local/bin/start.sh"]

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1
