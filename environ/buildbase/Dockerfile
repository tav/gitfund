# Public Domain (-) 2015-2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

FROM debian:jessie

# Base Packages
RUN echo "image base: 2016-06-28" && apt-get -q update && apt-get -q -y upgrade
RUN apt-get install --no-install-recommends -q -y build-essential \
  ca-certificates \
  curl \
  git \
  mercurial \
  python-dev \
  python-pip \
  sudo \
  wget \
  unzip

# Checksum Verifier
ADD verify-checksum /usr/local/bin/verify-checksum

# Go
RUN curl -O https://storage.googleapis.com/golang/go1.7beta2.linux-amd64.tar.gz && \
  verify-checksum go1.7beta2.linux-amd64.tar.gz af3d46bdb1ab9adda599bd14de51e3bce85a72b875dc45c8875222a0007d973f83e036587e7b7cae3979881e2d2266f4d83e632b9a8dd95e85e63cc8a3ae9b16 && \
  tar -C /usr/local -xzf go1.7beta2.linux-amd64.tar.gz && \
  rm go1.7beta2.linux-amd64.tar.gz

# Service Directory
RUN mkdir service
WORKDIR /service

# Build Environment
ENV CPPFLAGS=-I/service/include \
    LDFLAGS=-L/service/lib \
    LD_LIBRARY_PATH=/service/lib

# zlib
RUN curl -O http://zlib.net/zlib-1.2.8.tar.gz && \
  verify-checksum zlib-1.2.8.tar.gz ece209d4c7ec0cb58ede791444dc754e0d10811cbbdebe3df61c0fd9f9f9867c1c3ccd5f1827f847c005e24eef34fb5bf87b5d3f894d75da04f1797538290e4a && \
  tar -xzf zlib-1.2.8.tar.gz && \
  cd zlib-1.2.8 && \
  ./configure --shared && \
  make install prefix=/service && \
  rm -rf /service/zlib-*

# pcre
RUN curl -O ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-8.39.tar.bz2 && \
  verify-checksum pcre-8.39.tar.bz2 8b0f14ae5947c4b2d74876a795b04e532fd71c2479a64dbe0ed817e7c7894ea3cae533413de8c17322d305cb7f4e275d72b43e4e828eaca77dc4bcaf04529cf6 && \
  tar -xjf pcre-8.39.tar.bz2 && \
  cd pcre-8.39 && \
  ./configure --prefix=/service && \
  make && \
  make install && \
  rm -rf /service/pcre-*

# openssl
RUN curl -O https://www.openssl.org/source/openssl-1.0.2h.tar.gz && \
  verify-checksum openssl-1.0.2h.tar.gz 780601f6f3f32f42b6d7bbc4c593db39a3575f9db80294a10a68b2b0bb79448d9bd529ca700b9977354cbdfc65887c76af0aa7b90d3ee421f74ab53e6f15c303 && \
  tar -xzf openssl-1.0.2h.tar.gz && \
  cd openssl-1.0.2h && \
  ./Configure linux-x86_64 shared no-idea no-krb5 no-mdc2 zlib --prefix=/service --openssldir=/service/share/ssl -L/service/lib -I/service/include && \
  make depend && \
  make && \
  make install && \
  rm -rf /service/openssl-*

# Python
RUN curl -O https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz && \
  verify-checksum Python-2.7.12.tgz e3c04b1c66ff659c08e09a5adc34fd856ca0c786e5820c05471747416fef38555f1711978ac5e81ff4fdf7c16311796212f638e5e2d43e2404b2a42fc139edb0 && \
  tar -xzf Python-2.7.12.tgz && \
  cd Python-2.7.12 && \
  ./configure --enable-unicode=ucs2 --enable-ipv6 --prefix=/service && \
  make && \
  make install && \
  rm -rf /service/Python-*

# Build Utilities
ADD build-service-tarball bin/
ADD export-env bin/

# Runtime Environment
ENV GOBIN=/service/bin \
    GOPATH=/service/go \
    PATH=/service/bin:/service/go/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONPATH=/service/pypkg

# Pip Support
RUN python -m ensurepip --upgrade && \
    mkdir pypkg && \
    pip install --upgrade pip
