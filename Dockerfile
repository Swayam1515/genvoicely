FROM python:3.11-slim

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.headless=true"]
