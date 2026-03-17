FROM apache/airflow:2.10.3

USER root

# Add common libs (keep minimal; this is a showcase image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

USER airflow

COPY dags/ /opt/airflow/dags/
COPY plugins/ /opt/airflow/plugins/

