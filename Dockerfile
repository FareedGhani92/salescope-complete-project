FROM python:3.13-slim
WORKDIR /app
COPY requirements-streamlit.txt requirements.txt .
RUN pip install --no-cache-dir -r requirements-streamlit.txt
COPY . .
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
