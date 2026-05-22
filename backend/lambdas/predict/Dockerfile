FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY app/ /opt/app/
COPY TimeXer.pth /opt/model/TimeXer.pth

COPY handler.py .
CMD ["handler.handler"]
