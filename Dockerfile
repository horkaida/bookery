FROM python:3.11.9-alpine3.20
COPY . .
WORKDIR .

EXPOSE 8000
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]