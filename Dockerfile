FROM python:3.9
COPY . /home/otm
WORKDIR /home/otm
RUN pip install -r requirements.txt
#CMD ["python","TELEGRAM_BOT.py"]
#comment