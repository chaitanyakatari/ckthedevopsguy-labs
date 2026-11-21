FROM python:3.13-alpine
WORKDIR /srv
COPY app.py .
USER 1000
EXPOSE 8080
CMD ["python", "-u", "app.py"]
