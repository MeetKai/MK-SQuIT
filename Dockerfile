# Copyright (c) 2020 MeetKai Inc. All rights reserved.

FROM nvidia/cuda:11.1-base

ENV DEBIAN_FRONTEND=noninteractive

# Install git
RUN apt-get -y update && \
    apt-get install -y git curl gcc python3-pip && \
    apt-get -y update && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install NeMo NLP from main
RUN pip3 install --disable-pip-version-check --no-cache-dir Cython
RUN python3 -m pip install git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[nlp]

# Use torch nightly for rtx 30xx support
RUN pip3 install --no-cache-dir --upgrade --pre torch torchvision torchtext -f https://download.pytorch.org/whl/nightly/cu110/torch_nightly.html

# Install generation requirements
COPY requirements.txt requirements.txt
RUN pip3 install --disable-pip-version-check --no-cache-dir -r requirements.txt
RUN python3 -m spacy download en_core_web_sm

# Install nodejs for jupyterlab
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get install -y nodejs

# install JupyterLab extensions
RUN pip3 install --disable-pip-version-check --no-cache-dir ipython ipywidgets jupyterlab jupyterlab-nvdashboard
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
RUN jupyter labextension install jupyterlab-nvdashboard
RUN jupyter lab build

# Copy data and scripts
COPY . /mk_squit
COPY out/workspaces /root/.jupyter/lab/workspaces

# Expose Jupyter & Tensorboard
EXPOSE 8888
EXPOSE 6006

WORKDIR /mk_squit

# Start Jupyter by default
ENTRYPOINT [ "/bin/sh" ]
CMD ["-c", "jupyter lab  --notebook-dir=/mk_squit --ip=0.0.0.0 --no-browser --allow-root --port=8888 --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*' --NotebookApp.base_url=${NB_PREFIX}"]