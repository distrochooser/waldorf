FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /backend
COPY ./ ./
RUN pip install -r requirements.txt
RUN adduser waldorf --no-create-home --shell /bin/false --disabled-password --gecos ""
USER waldorf
CMD ["python", "./main.py", "--langs", "de,en,zh-cn"]