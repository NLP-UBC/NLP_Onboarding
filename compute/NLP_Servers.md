# UBC NLP Servers
Our lab has a total of 17 GPUs. Access to these GPUs are restricted to only members of our group.  
This document will walk you through steps to [obtain access](#obtaining-access) to our servers, details about the [file system](#file-system), as well as providing you with some of [my experiences](#personal-experiences) using these compute clusters. More information can be found [here](https://my.cs.ubc.ca/docs/using-department-research-cluster)

## Getting Access
1. To obtain access, email the help desk at [help@cs.ubc.ca](help@cs.ubc.ca) and CC your supervisor. You will need access to [remote.cs.ubc.ca](remote.cs.ubc.ca) and Slurm submission servers with addresses `submit-cs.cs.ubc.ca`, `newcastle.cs.ubc.ca`, and `submit-ml`. For `submit-ml`, you will need to use Slurm with `partition=ubcml-nlp`. For the other two, you will use `--partition=ubcgpo`.
2. To login to our compute servers, you will need to proxy jump from UBC Remote server. On command line, this will be `ssh -J CWL@remote.cs.ubc.ca CWL@submit-cs.cs.ubc.ca`. Alternatively, you can first `ssh CWL@remote.cs.ubc.ca` and then do `ssh CWL@submit-cs.cs.ubc.ca` there. To configure your ssh config file, see the [configuration section](#ssh-configuration).
3. (Optional) you are given 10GB storage upon approval of access to the cluster. If you want more storage, email the help desk at [help@cs.ubc.ca](help@cs.ubc.ca) and CC your supervisor to get allocation under `/ubc/cs/research/nlp-raid/students`.
4. (Optional) if you want to avoid entering your password each time you log in, consider [adding your ssh key](../technical/ssh_key.md) to `remote.cs.ubc.ca`.

## SSH Configuration
You can setup your ssh config list like this:
```
Host UBC-Remote-Research
    HostName remote.cs.ubc.ca
    User <cwl>
    ForwardX11 yes
Host UBC-Submit-CS
    HostName submit-cs.cs.ubc.ca
    User <cwl>
    ProxyJump UBC-Remote-Research
    ForwardX11 yes
Host UBC-NewCastle
    HostName newcastle.cs.ubc.ca
    User <cwl>
    ForwardX11 yes
    ProxyJump UBC-Remote-Research
```
Now `ssh -J CWL@remote.cs.ubc.ca CWL@submit-cs.cs.ubc.ca` becomes `ssh UBC-Submit-CS`.

## Using NewCastle
To use `Slurm` on NewCastle, you must `source /opt/slurm/set_submit_cs`.

## File System
Our storage directory is in `/ubc/cs/research/nlp-raid/students/CWL/`. Please be reminded to consistently deleting unused files, as we often run out of storage. The old directory `/ubc/cs/research/nlp/CWL/` had ran out of space. Note that this is a different file system from the your home directory and will cause bugs if your `.bashrc` is trying to run things there.

## Slurm Specs
For basic usage of Slurm, checkout the [Slurm document](../technical/slurm.md). Full information can be found [here](https://my.cs.ubc.ca/docs/using-department-research-cluster). To start an interactive session, use:
```shell
salloc --time=4:0:0 --mem-per-cpu=16G --nodes=1 --gpus=1 --partition=nlpgpo
```
Below is a template job script:
```shell
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --mem-per-cpu=16G
#SBATCH --time=12:0:0
#SBATCH --partition=nlpgpo
...
```

## Personal Experiences
1. Do not switch to another network while you are connected to the server: you may create zombie vscode server process that blocks you from logging in next time.
2. If you installed tools (e.g. `conda`) in the storage directory, remember to remove the initialization code from your `.bashrc`. Having those code in your `.bashrc` could block your VSCode to log in to the server.

## Using Jupyter Notebook
To use jupyter notebook on compute nodes, use `sbatch` to submit the following script:
```shell
#!/bin/bash

#SBATCH --job-name=my_jupyter_notebook
#SBATCH --time=3-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=16
#SBATCH --partition=nlpgpo

################################################################################

export NOTEBOOK_HOME_DIR="/ubc/cs/research/nlp-raid/students/<your_id>"

# Change directory into the job dir
cd $SLURM_SUBMIT_DIR

# Load software environment
# module load cuda/12.4.0 intel-oneapi-compilers/2023.1.0 python/3.11.6 gcc
export ENVDIR=/ubc/cs/research/nlp-raid/students/<your_id>/venv     # change accordingly
source $ENVDIR/bin/activate
# export TRITON_CACHE_DIR="/scratch/st-jzhu71-1/shenranw/triton_cache"
# export HF_HOME="/scratch/st-jzhu71-1/shenranw/transformers_cache"

# Set RANDFILE location to writeable dir
# export RANDFILE=$TMPDIR/.rnd

# Generate a unique token (password) for Jupyter Notebooks
export APPTAINERENV_JUPYTER_TOKEN=$(openssl rand -base64 15)

# Find a unique port for Jupyter Notebooks to listen on
readonly PORT=$(python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')

# Print connection details to file
cat > ./connection_${SLURM_JOB_ID}.txt <<END

1. Create an SSH tunnel to Jupyter Notebooks from your local workstation using the following command:

ssh -N -L 8888:${HOSTNAME}:${PORT} ${USER}@submit-cs.cs.ubc.ca -J ${USER}@remote.cs.ubc.ca

2. Point your web browser to http://localhost:8888

3. Login to Jupyter Notebooks using the following token (password):

${APPTAINERENV_JUPYTER_TOKEN}

When done using Jupyter Notebooks, terminate the job by:

1. Quit or Logout of Jupyter Notebooks
2. Issue the following command on the login node (if you did Logout instead of Quit):

scancel ${SLURM_JOB_ID}

END

# Execute jupyter within the Apptainer container
jupyter notebook --no-browser --port=${PORT} --ip=0.0.0.0 --notebook-dir=$NOTEBOOK_HOME_DIR --NotebookApp.token=${APPTAINERENV_JUPYTER_TOKEN}
```