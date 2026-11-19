# DegsellOS-systemavbildning för amd64 och arm64, byggd på Bluefin LTS.
ARG BASE_IMAGE=ghcr.io/ublue-os/bluefin:lts

# Byggkontext som bara monteras under bygget och inte hamnar i avbildningen.
FROM scratch AS ctx
COPY build_files /build_files
COPY system_files /system_files
COPY vault /vault
COPY VERSION /VERSION

FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="DegsellOS" \
      org.opencontainers.image.description="Ett forskningsorienterat OS byggt på Bluefin LTS" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/Jtensetti/DegsellOS"

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build_files/build.sh

RUN bootc container lint
