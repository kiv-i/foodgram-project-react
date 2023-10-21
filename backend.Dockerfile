FROM python:3.9
WORKDIR /app
RUN pip install gunicorn==20.1.0
COPY backend/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY backend .
COPY data ./data
COPY docs ./docs
CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi" ]