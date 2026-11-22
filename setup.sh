#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
export UV_CACHE_DIR="$PWD/.cache/uv"
uv venv --allow-existing --python 3.12 .venv
uv pip sync --system-certs --link-mode copy --require-hashes requirements.txt
mkdir -p .native/downloads
while read -r hash path; do
    deb=".native/downloads/${path##*/}"
    if [[ ! -f "$deb" ]] || ! echo "$hash  $deb" | sha256sum --check --status; then
        curl --fail --silent --show-error --location "https://deb.debian.org/debian/$path" -o "$deb"
    fi
    echo "$hash  $deb" | sha256sum --check
    dpkg-deb -x "$deb" .native
done < native.lock
ln -sfn ../../.native/usr/bin/pngquant .venv/bin/pngquant
sed -i "s|^prefix=/usr$|prefix=$PWD/.native/usr|" .native/usr/lib/x86_64-linux-gnu/pkgconfig/imagequant.pc
