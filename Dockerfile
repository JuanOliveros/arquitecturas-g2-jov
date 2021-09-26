FROM ubuntu:20.04
RUN apt update \
  && apt -y install software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt update \
  && apt -y install python3 \
  && apt -y install pip \
  && apt -y install mosquitto
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x start.sh
CMD ["bash", "start.sh"]