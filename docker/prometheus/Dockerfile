FROM prom/prometheus:v3.5.0

# Copy configuration files and startup script
COPY prometheus.yml /etc/prometheus/prometheus.yml.template
COPY rules/ /etc/prometheus/rules/
COPY start.sh /usr/local/bin/start.sh

# Create prometheus user data directory and make startup script executable
USER root
RUN mkdir -p /prometheus && \
    chown -R 65534:65534 /prometheus && \
    chmod +x /usr/local/bin/start.sh

# Switch to prometheus user
USER 65534

# Set the entrypoint to our startup script
ENTRYPOINT ["/usr/local/bin/start.sh"]

# Expose port
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:9090/-/healthy || exit 1
