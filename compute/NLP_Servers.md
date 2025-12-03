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
For basic usage of Slurm, checkout the [Slurm document](../technical/slurm.md). To start an interactive session, use:
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