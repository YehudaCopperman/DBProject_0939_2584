FROM python:3.10-slim

WORKDIR /app

#  התקנת ספריות גרפיות עבור Tkinter
RUN apt-get update && apt-get install -y tcl-dev tk-dev

COPY . .

RUN pip install psycopg2-binary tk

CMD ["python", "main.py"]