FROM cosmiqworks/spacenet-utilities-gpu:latest
LABEL maintainer dlindenbaum


# ensure specific packages are installed using apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        wget \
        vim \
        libatlas-base-dev \
        libboost-all-dev \
        libgflags-dev \
        libgoogle-glog-dev \
        libhdf5-serial-dev \
        libleveldb-dev \
        liblmdb-dev \
        libopencv-dev \
        libprotobuf-dev \
        libsnappy-dev \
        protobuf-compiler \
        python-dev \
        python-numpy \
        python-pip \
        python-setuptools \
        python-scipy \
        gdal-bin \
        python-gdal




# define Git Location

ENV GIT_BASE=/opt/
# switch working directory to GIT_BASE
WORKDIR $GIT_BASE

# download and install python pip
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py
RUN pip install --upgrade


# make a direcectory to copy source code into
RUN mkdir spaceSSD

# copy entire directory where docker file is into docker container at /opt/spaceSSD
COPY . /opt/spaceSSD/

# define environment variable for location of CAFFE_ROOT
ENV CAFFE_ROOT=/opt/spaceSSD/caffe-ssd/

# Switch to that directory
WORKDIR $CAFFE_ROOT

# Move into Python directory and install requirements.txt file
RUN cd python && for req in $(cat requirements.txt) pydot; do pip install $req; done && cd ..

# download nccl git code and compile NCCL
RUN git clone https://github.com/NVIDIA/nccl.git && cd nccl && make -j install && cd .. && rm -rf nccl

# Make Build Directory and run make to compile CAFFE code
RUN mkdir build && cd build && \
    cmake -DUSE_CUDNN=1 -DUSE_NCCL=1 .. && \
    make -j"$(nproc)"

# Define python variables

ENV PYCAFFE_ROOT $CAFFE_ROOT/python
ENV PYTHONPATH $PYCAFFE_ROOT:$PYTHONPATH
ENV PATH $CAFFE_ROOT/build/tools:$PYCAFFE_ROOT:$PATH
RUN echo "$CAFFE_ROOT/build/lib" >> /etc/ld.so.conf.d/caffe.conf && ldconfig

# make pycaffe
RUN cd build && make pycaffe

##

WORKDIR /workspace


