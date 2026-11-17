# ForskarOS – ett forskningslager ovanpå en färdig, fungerande distribution.
#
# Vi bygger inte ett eget OS från grunden. Vi tar Bluefin LTS (Universal Blue,
# GNOME, atomära uppdateringar, Flatpak, Homebrew) som finns för både
# amd64 (PC, Intel-Mac) och arm64 (t.ex. virtuell maskin på Apple Silicon)
# och lägger ForskarOS ovanpå.
ARG BASE_IMAGE=ghcr.io/ublue-os/bluefin:lts

# Byggkontext som bara monteras under bygget och inte hamnar i avbildningen.
FROM scratch AS ctx
COPY build_files /build_files
COPY system_files /system_files
COPY vault /vault

FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="ForskarOS" \
      org.opencontainers.image.description="Ett forskningsorienterat OS byggt på Bluefin LTS" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/Jtensetti/researchOS"

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build_files/build.sh

RUN bootc container lint
