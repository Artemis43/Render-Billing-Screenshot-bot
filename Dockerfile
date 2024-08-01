FROM python:3.11
WORKDIR /ssbot
COPY . /ssbot/
RUN pip install -r requirements.txt
RUN playwright install
RUN playwright install-deps
EXPOSE 8080
CMD python main.py