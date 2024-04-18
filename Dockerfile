FROM python:3.10.8
RUN mkdir -p /app
WORKDIR /app
ENV FLASK_APP app.app
ENV FLASK_RUN_HOST 0.0.0.0
EXPOSE 5001
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask","run","-p","5001"]
