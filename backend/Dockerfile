FROM python:3.11-slim

WORKDIR /srv/app

COPY requirements.txt /srv/app/
RUN pip install --no-cache-dir -r requirements.txt

# CPU torch (portfolio-friendly; no GPU requirements)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY . /srv/app

EXPOSE 5000

CMD ["python", "-m", "app.app"]

