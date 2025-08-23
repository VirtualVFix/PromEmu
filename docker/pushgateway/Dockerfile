FROM prom/pushgateway:v1.11.1

# Create data directory with proper permissions
USER root
RUN mkdir -p /data && \
    chown -R 65534:65534 /data

# Switch to non-root user (uid 65534 is 'nobody' in many alpine images)
USER 65534

# Expose port
EXPOSE 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:9091/metrics || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["--web.listen-address=0.0.0.0:9091"]
