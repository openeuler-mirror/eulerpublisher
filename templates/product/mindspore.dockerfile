FROM ascendai/cann:{{ dependence }} as official

# Arguments
ARG MINDSPORE_VERSION={{ version }}
# Change the default shell
SHELL [ "/bin/bash", "-c" ]

# Install mindspore
RUN pip install --no-cache-dir \
        mindspore==${MINDSPORE_VERSION}
