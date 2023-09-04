FROM debian:bullseye-slim
RUN apt update -y && apt install -y python3 python3-pip ffmpeg
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
CMD ["python3","discordbot.py"]
