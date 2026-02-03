# `uv` Tutorial
[`uv`](https://github.com/astral-sh/uv) is a python package manager. It automatically keep track of your installed packages and sort out the correct version of each package. It is also 10x faster than `pip`, which saves significant amount of time if you are working on a HDD machine.

## When to use `uv`
1. Your project is entirely pythonic
2. Whenever you can use `uv`

## When to not use `uv`
1. You are compiling languages other than python
2. Using `uv` is not supported in the cluster

## Using `uv`
Once you installed `uv`, go to your project directory and run:
```shell
uv init
```
This will create 3 files: `main.py`, `pyproject.toml` and `uv.lock`. You can delete the `main.py`, but do not delete the other two.

Now you can create an environment. Note that this is not mandatory, as `uv` by default will create an environment under your project directory. However, most cluster have limited project storage, so you may want to store the environment somewhere else. To do that:
```shell
uv venv path/to/venv --python python.version
```

Now that you have an environment already, you can activate it just like any [`virtualenv`](virtualenv.md):
```shell
source path/to/venv/bin/activate
```
Note that this also work for any virtualenv created not with `uv`. `uv` only manage packages.

To install packages to this environment, use:
```shell
uv add <package_name> --active
```
The `--active` here will make uv install the package to the activated virtualenv. Otherwise it will create a `.venv` under your project directory and install everything there. To install packages in a `requirements.txt`, use:
```shell
uv add -r requirements.txt --active
```

To remove a package, use
```shell
uv remove <package_name>
```

In case of a change in environment setup (e.g. one of your teammates added a new package and updated `pyproject.toml` or `uv.lock`), you can just sync the dependencies by:
```shell
uv sync --active
```