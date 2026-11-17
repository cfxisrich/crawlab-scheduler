ARG CRAWLAB_IMAGE=crawlabteam/crawlab:0.6.3@sha256:9dbe97240ba2670ce49fd1be5d557b59653e602d8fa29a71c9e05b26c557193b
FROM ${CRAWLAB_IMAGE}
COPY examples/requirements.txt /tmp/flowharbor-requirements.txt
COPY licenses/Crawlab-BSD-3-Clause.txt licenses/Crawlab-SDK-BSD-3-Clause.txt /opt/flowharbor/licenses/
RUN python -m pip install --no-cache-dir -r /tmp/flowharbor-requirements.txt
