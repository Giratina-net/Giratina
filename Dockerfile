FROM python:3.13.1-bullseye
RUN apt update -y && apt install -y ffmpeg build-essential
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
CMD ["python3","discordbot.py"]
