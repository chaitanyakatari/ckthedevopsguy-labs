FROM python:3.13-slim
COPY server.py /app/server.py
USER 65534
EXPOSE 8080
CMD ["python3", "-u", "/app/server.py"]
