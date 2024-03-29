# How this project was setup ?

> [!NOTE]
> Follow the steps below to setup this project from scratch.

## Key Concepts

- [x] AMI ID (Look up the latest AWS Deep Learning AMI GPU CUDA)
- [x] Create new VPC, Subnets (Public and Private), RouteTables and Security Group
- [x] Define Launch Configuration with User Data
- [x] Create Autoscaling Group with Launch Template and Spot Fleet


### Setup

1. Create an empty directory and change directory:

```bash
mkdir hack-lab-aws-python
cd hack-lab-aws-python
```

2. Setup a pulumi project:

```bash
pulumi new python
```

> [!IMPORTANT]
> Change anything if you need to, if you want to keep the default values, just press <kbd> <br> Enter <br> </kbd> and it'll be skipped.

3. Activate the virtual environment and install new dependencies:

```bash
source venv/bin/activate
pip install pulumi-aws pulumi-awsx pulumi-random pulumi-command
```

> [!CAUTION]
> Manually, add `pulumi-aws`, `pulumi-awsx`, `pulumi-random` and `pulumi-command` (see below) in `requirements.txt` file, if you want to use `pip install -r requirements.txt` command later.

```console
pulumi>=3.0.0,<4.0.0
pulumi-aws>=6.0.0,<7.0.0
pulumi-awsx>=2.0.0,<3.0.0
pulumi-random>=3.0.0,<5.0.0
pulumi-command>=0.5.0,<1.0.0
```

4. Add configuration variables:

```bash
pulumi config set aws:region eu-west-3
pulumi config set keypair jarvis
pulumi config set vpcNetworkCidr 192.168.110.0/24
```

> [!IMPORTANT]
> Also, add the following in `Pulumi.dev.yaml` file:

```yaml
environment:
  - aws-jarvis
```

5. Run the following command to run the program:

```bash
pulumi up
```

6. Run the following command in remote server to setup desktop gui:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mohammadzainabbas/pulumi-labs/main/hack-lab-aws-python/scripts/setup_desktop.sh)"
```

> [!NOTE]
> This will take some time, so be patient.
