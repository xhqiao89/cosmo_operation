FROM zhiyuli/rapid_base:1.0


RUN cd ~ && \
    git clone https://github.com/BYU-Hydroinformatics/RAPIDpy.git && \
    cd RAPIDpy && \
    git checkout cosmo && \
    python setup.py install


CMD [ "/bin/bash" ]
