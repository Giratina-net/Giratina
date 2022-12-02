FROM debian:bullseye-slim

RUN apt update -y && apt install -y python3 python3-pip ffmpeg
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
CMD ["python3","discordbot.py"]