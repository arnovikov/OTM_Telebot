FROM python:latest
COPY . /home/otm
WORKDIR /home/otm
RUN pip install -r requirements.txt
CMD ["python","TELEGRAM_BOT.py"]
#comment