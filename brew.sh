#!/bin/bash
# Script to install required Homebrew formulae and casks for har-oa3-converter project

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

echo "Installing Homebrew formulae..."

# Install formulae
brew install \
  autoconf \
  awscli \
  bazel \
  bazelisk \
  bosh-cli \
  brotli \
  c-ares \
  ca-certificates \
  cairo \
  certifi \
  cffi \
  cryptography \
  expat \
  fontconfig \
  freetype \
  gdbm \
  gettext \
  giflib \
  git \
  glib \
  go \
  graphite2 \
  grep \
  harfbuzz \
  "icu4c@77" \
  jpeg-turbo \
  libice \
  libnghttp2 \
  libpng \
  libsm \
  libtiff \
  libunistring \
  libuv \
  libx11 \
  libxau \
  libxaw \
  libxcb \
  libxdmcp \
  libxext \
  libxft \
  libxinerama \
  libxmu \
  libxpm \
  libxrender \
  libxt \
  little-cms2 \
  locateme \
  lz4 \
  lzo \
  m1-terraform-provider-helper \
  m4 \
  mpdecimal \
  node \
  "openjdk@21" \
  "openssl@3" \
  pcre2 \
  pixman \
  pkenv \
  pkgconf \
  poetry \
  pycparser \
  pyenv \
  "python@3.10" \
  "python@3.12" \
  "python@3.13" \
  "python@3.9" \
  readline \
  sqlite \
  telnet \
  tfenv \
  xorgproto \
  xterm \
  xz \
  zlib \
  zstd

echo "Installing Homebrew casks..."

# Install casks
brew install --cask \
  git-credential-manager

echo "Installation complete!"
