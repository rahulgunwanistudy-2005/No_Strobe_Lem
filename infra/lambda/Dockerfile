FROM public.ecr.aws/lambda/python:3.12@sha256:517bcc7dc1a3ba62e324961c1563cc54a2bd6dc1060188f9d376211ecb7b2926 AS ffmpeg
ARG FFMPEG_URL=https://github.com/rahul-software-dev/hazardtrack/releases/download/v0.1.0/ffmpeg-7.1.1-hazardtrack-linux-x86_64.tar.xz
ARG FFMPEG_SHA256=cdae69e1c416c10a340be3c998bcd1a7a1d591a930c44d96c2441b5c09fd5595
RUN curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 --max-time 180 \
       "$FFMPEG_URL" -o /tmp/ffmpeg.tar.xz \
    && echo "$FFMPEG_SHA256  /tmp/ffmpeg.tar.xz" | sha256sum --check - \
    && python -c 'import tarfile; tarfile.open("/tmp/ffmpeg.tar.xz").extractall("/opt/ffmpeg", filter="data")'

FROM public.ecr.aws/lambda/python:3.12@sha256:517bcc7dc1a3ba62e324961c1563cc54a2bd6dc1060188f9d376211ecb7b2926
COPY --from=ffmpeg /opt/ffmpeg/bin/ffmpeg /opt/ffmpeg/bin/ffprobe /usr/local/bin/
COPY --from=ffmpeg /opt/ffmpeg/LICENSE.txt /opt/ffmpeg/source.tar.xz /opt/ffmpeg/
COPY infra/runtime-requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-compile --require-hashes -r /tmp/requirements.txt --target /var/task \
    && rm /tmp/requirements.txt
ARG NOSTROBE_WHEEL_URL=https://github.com/rahul-software-dev/hazardtrack/releases/download/v0.1.1/nostrobe-0.1.1-py3-none-any.whl
ARG NOSTROBE_WHEEL_SHA256=857d20cb8d25e5aa0c54e77bf328d07b1c5555c96d36936d2814577236404bb9
RUN curl --fail --silent --show-error --location --retry 3 "$NOSTROBE_WHEEL_URL" \
       -o /tmp/nostrobe-0.1.1-py3-none-any.whl \
    && echo "$NOSTROBE_WHEEL_SHA256  /tmp/nostrobe-0.1.1-py3-none-any.whl" | sha256sum --check - \
    && pip install --no-cache-dir --no-compile --no-deps /tmp/nostrobe-*.whl --target /var/task \
    && rm /tmp/*.whl
COPY infra/lambda/*.py /var/task/
ENV NUMBA_CACHE_DIR=/tmp/numba MPLCONFIGDIR=/tmp/matplotlib
CMD ["handler.handler"]
