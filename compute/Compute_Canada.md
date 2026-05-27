# Compute Canada Tutorial
Compute Canada is a funded by the federal government and provides access to High-Performance Compute for researchers in Canada. You may find its documentation [here](https://docs.alliancecan.ca/wiki/Technical_documentation).  
This document will walk you through steps to [obtain access](#obtaining-access) to compute clusters on Compute Canada, details of the [file system](#file-system), as well as providing you with some of [my experiences](#personal-experiences) using these compute clusters. I will also go through some details of [using Slurm](#slurm-specs) in Compute Canada clusters.

## Obtaining Access
1. Go to [https://ccdb.alliancecan.ca/](https://ccdb.alliancecan.ca/) to register for your account. If you already have an account, log in to it.
2. If you just registered, skip this step. In you have an account and logged in, check your roles: if your current role is already with your current supervisor, skip this step. Otherwise, go to _My Account_ -> _Apply for a New Role_ and enter your supervisor's information there. You will need your supervisor to give you their _CCRI_.
3. An email will be sent to your supervisor to approve your access if you just registered or switched supervisor. Once approved, you can go to _Resources_ -> _Access Systems_ to gain access to compute servers. We will normally be using servers under _HPC_. Each server has different hardware. You can find details [here](https://docs.alliancecan.ca/wiki/Technical_documentation) under _Resources_ on the left panel.
4. (Optional) if your supervisor is affiliated with the [Vector Institute](https://vectorinstitute.ai/) or [Amii](https://www.amii.ca/), you have access to [Killarney](https://docs.alliancecan.ca/wiki/Killarney) or [Vulcan](https://www.alliancecan.ca/en/services/compute/vulcan). Details for setting up Killarney and Vulcan can be found in [Killarney setup manual](./Killarney.md) and [Vulcan setup manual](./Vulcan.md).
5. Make sure you have [set up MFA](https://docs.alliancecan.ca/wiki/Multifactor_authentication#Use_a_smartphone_or_tablet) and [added your ssh key](https://docs.alliancecan.ca/wiki/SSH_Keys#Installing_your_key).
6. Once you are granted access to compute servers, you can `ssh` into them with your _username_: `ssh username@address`. Server addresses can be found [here](https://docs.alliancecan.ca/wiki/Technical_documentation) under _Resources_ on the left panel.

## File System
There will be two folders, `scratch` and `projects` in your home directory. Please keep all large files or environments in `scratch` folder.

## Personal Experiences
- Compute Canada is open to almost all researchers in Canada, meaning that there are many people competing over a small number of GPUs. The servers use [Slurm](../technical/slurm.md) to manage jobs, which could cause a very long wait time.
- Certain older servers (e.g. Narval) do not have internet in their compute nodes, meaning that when you submit a job, it runs without internet connection. However, newer servers (Fir, Nibi) now have internet connection in compute nodes.
- Setting up the environment could be very tricky as you are not allowed to use `conda`. Instead, they have pre-built wheels for python packages. To set up an environment, I recommend using [`python`'s `virtualenv`](../technical/virtualenv.md). Notice that Compute Canada clusters have [pre-built wheels](https://docs.alliancecan.ca/wiki/Available_Python_wheels) for common packages ready, so you can always first try `pip install --no-index` and then manually download unavailable packages.
- (Not recommended) in certain scenarios where the above `virtualenv` setup cannot meet your requirements, you can use [Apptainer](../technical/apptainer.md).

## Slurm Specs
For basic usage of Slurm, checkout the [Slurm document](../technical/slurm.md). For Compute Canada clusters, you can use `sq` to see status of all your jobs. To start an interactive session, use:
```shell
salloc --time=4:0:0 --mem-per-cpu=16G --ntasks-per-node=8 --gpus-per-node=a100:1 --account=def-xxxxxx
```
Below is a template job script for Compute Canada clusters:
```shell
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --gpus-per-node=a100:1
#SBATCH --ntasks-per-node=8
#SBATCH --mem=24G
#SBATCH --time=1-00:00
#SBATCH --account=def-xxxxxx    # Use your supervisor's username
module load ...
source .../bin/activate
...
```

## Softwares
Like any high-performance computing clusters, Compute Canada has prepared commonly used compilers (cuda, gcc, etc.) and other modules for you. You may load them using:
```shell
module load {module-name}
```
Details are available at the [software information page](https://docs.alliancecan.ca/wiki/Available_software).