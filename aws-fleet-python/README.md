# AWS Autoscaling Group with Launch Template

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new)

## Overview

A Pulumi IaC program written in Python to deploy AWS Autoscaling Group with Launch Template to request Spot Instances for multi-type instances.

## Included:

- AMI ID (Look up the latest AWS Deep Learning AMI GPU CUDA)
- Create new VPC, Subnets (Public and Private), RouteTables and Security Group
- Define Launch Configuration with User Data
- Create Autoscaling Group with Launch Template and Spot Fleet

## Prerequisites

* Python 3.9+
* Pulumi
* AWS CLIv2 & valid credentials configured
* AWS Native CLI Tools

## Quick Start

### Setup

1. Configuring OpenID Connect for AWS:

Follow the guideline [here](https://www.pulumi.com/docs/pulumi-cloud/oidc/aws/) to create an OIDC provider for AWS.

2. Clone the repo:

```bash
git clone https://github.com/mohammadzainabbas/pulumi-labs.git
```

or if GitHub CLI is installed:

```bash
gh repo clone mohammadzainabbas/pulumi-labs
```

3. Change directory:

```bash
cd aws-fleet-python
```

4. Create a new Python virtualenv, activate it, and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

5. Create a new Pulumi stack, which is an isolated deployment target for this example:

```bash
pulumi stack init
```

6. Update your environment:

Now, update your environment (that you'd already setup in step 1) in `Pulumi.dev.yaml` like the following:

```yaml
environment:
  - aws-jarvis
```

> Note that the `aws-jarvis` is the name of the environment that I've created in step 1.

7. Set the AWS region (optional):

To deploy to a region other than the default one configured for your AWS CLI profile, run `pulumi config set aws:region <region>`

```bash
pulumi config set aws:region us-east-1
```

> If you don't specify anything, everything will be deployed in `eu-west-3` region.

8. Run `pulumi up` to preview and deploy changes:

```bash
pulumi up
```

> Note: you can use `--yes` flag to skip the confirmation prompt.

and voila! You've deployed Auto scaling group using spot fleet along with your custom launch config to AWS.

### Cleanup

To destroy the Pulumi stack and all of its resources:

```bash
pulumi destroy
```
