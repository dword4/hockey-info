FROM alpine:3.9

# update
RUN apk update

# setup and clone
RUN mkdir -p /hockey-info
WORKDIR /hockey-info
RUN apk add git
RUN apk add py-pip
RUN git clone https://gitlab.com/dword4/hockey-info.git .
RUN pip install -r requirements.txt

# set timezone
RUN apk add tzdata
ENV TZ=America/New_York

# make it happen captain!
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
