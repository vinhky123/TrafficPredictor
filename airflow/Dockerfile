FROM apache/airflow:2.10.3-python3.11

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-jdk \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY dags/    /opt/airflow/dags/
COPY plugins/ /opt/airflow/plugins/
