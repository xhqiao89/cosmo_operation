FROM ubuntu:16.04
RUN apt update && apt upgrade -y && apt install -y software-properties-common

RUN apt update && apt install --fix-missing -y build-essential \
                                               g++ \
                                               gfortran \
                                               git \
                                               wget \
                                               python \
                                               python-dev \
                                               nano \
                                               vim



RUN cd ~ && \
    mkdir installz && \
    git clone https://github.com/c-h-david/rapid.git && \
    cd rapid && \
    git checkout 20161221 && \
    chmod u+x rapid_install_prereqs.sh && \
    ./rapid_install_prereqs.sh

ENV TACC_NETCDF_LIB /root/installz/netcdf-3.6.3-install/lib
ENV TACC_NETCDF_INC /root/installz/netcdf-3.6.3-install/include
ENV PETSC_DIR /root/installz/petsc-3.6.2
ENV PETSC_ARCH linux-gcc-c

ENV PATH $PATH:/$PETSC_DIR/$PETSC_ARCH/bin
ENV PATH $PATH:/root/installz/netcdf-3.6.3-install/bin

RUN ls /root/installz/petsc-3.6.2/lib/petsc/conf && \
    cd ~/rapid && \
    echo $INSTALLZ_DIR && \
    cd ~/rapid/src && \
    make rapid

RUN cd ~ && \
    wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    bash miniconda.sh -b -p $HOME/miniconda && \
    rm ~/miniconda.sh

ENV PATH="/root/miniconda/bin:${PATH}"


#RUN conda create --name rapidpy python=2.7 && \
#    conda activate rapidpy && \

RUN conda install gdal=2.2.4
RUN conda install -c conda-forge xarray pangaea


CMD [ "/bin/bash" ]