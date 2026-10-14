# Working PyArrow environment (GitHub Actions)

The workflow `.github/workflows/pyarrow-environment.yml` defines a fresh Ubuntu 24.04 Linux worker with Python 3.11. It installs compatible PyArrow, Pandas, NumPy and Optuna using `requirements-research-ci.txt`, prints installed versions, executes synthetic Parquet read tests and then the repository's full Python unittest suite.

It runs on changes to itself, the requirements-linked files, and by manual dispatch. GitHub-hosted runners have internet access under ordinary service conditions, unlike the present offline container.

**This creates an executable environment definition, but its success must be confirmed in Actions logs before claiming the environment is operational.** The workflow has no access to the user's three ZIP uploads or private original cache, and does not run the actual 1,475,332-row original formal backtest. Such input must be staged separately in a private, audited channel.

No secrets, market rows, strategy files, AWS credentials or live-exchange code are committed. Existing research acceptance criteria are unchanged.
