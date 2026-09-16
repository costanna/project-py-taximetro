FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY taximetro/ taximetro/
COPY web/ web/
COPY run_api.py config.json ./

EXPOSE 5000

CMD ["python", "run_api.py"]
