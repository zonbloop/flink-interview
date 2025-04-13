FROM flink:1.18.1

# Install Python
RUN apt-get update -y && \
apt-get install -y python3 python3-pip python3-dev && \
pip3 install apache-flink==1.18.1 && \
rm -rf /var/lib/apt/lists/*

# Ensure python command points to python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# install Java & updates
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk && \
    apt-get install -y ant && \
    apt-get clean;

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

WORKDIR /opt/flink


RUN mkdir -p ./lib

RUN curl -o ./lib/flink-connector-jdbc-3.1.2-1.18.jar https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.2-1.18/flink-connector-jdbc-3.1.2-1.18.jar
RUN curl -o ./lib/postgresql-42.7.3.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
RUN curl -o ./lib/flink-sql-connector-kafka-3.1.0-1.18.jar https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.1.0-1.18/flink-sql-connector-kafka-3.1.0-1.18.jar

RUN chown flink:flink /opt/flink/lib/flink-sql-connector-kafka-3.1.0-1.18.jar && \
    chown flink:flink /opt/flink/lib/flink-connector-jdbc-3.1.2-1.18.jar && \
    chown flink:flink /opt/flink/lib/postgresql-42.7.3.jar

# Copy job script
COPY ad_metrics_job.py /opt/flink/ad_metrics_job.py

USER flink

#CMD ["jobmanager"]