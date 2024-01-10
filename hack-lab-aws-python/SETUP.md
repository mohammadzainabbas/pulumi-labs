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
pip install pulumi-aws pulumi-awsx
```

> [!CAUTION]
> Manually add `pulumi-aws` and `pulumi-awsx` in `requirements.txt` file.

3. Change directory:

```bash
cd hack-lab-aws-python
```

4. Create a new Python virtualenv, activate it, and install dependencies:

```bash
python3 -m venv venv
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

> [!NOTE]
> Here, `aws-jarvis` is the name of the environment that I've created in step 1.

7. Set the AWS region (optional):

To deploy to a region other than the default one configured for your AWS CLI profile, run `pulumi config set aws:region <region>`

```bash
pulumi config set aws:region us-east-1
```

> [!IMPORTANT] 
> If you don't specify anything, everything will be deployed in `eu-west-3` region.

8. Run `pulumi up` to preview and deploy changes:

```bash
pulumi up
```

> [!NOTE] 
> You can use `--yes` flag to skip the confirmation prompt.

and voila! You've deployed Auto scaling group using spot fleet along with your custom launch config to AWS.

### Cleanup

To destroy the Pulumi stack and all of its resources:

```bash
pulumi destroy
```

> [!NOTE] 
> You can use `--yes` flag to skip the confirmation prompt.