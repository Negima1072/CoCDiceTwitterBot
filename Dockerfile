FROM python:3.10.4

RUN yum update -y

RUN mkdir /bot
ADD . /bot
WORKDIR /bot

RUN pip install -r requirements.txt

CMD ["python", "main.py"]