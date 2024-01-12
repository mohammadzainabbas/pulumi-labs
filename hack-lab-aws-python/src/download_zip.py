import pulumi
import pulumi_command as command
import pulumi_random as random

class DownloadZipArgs:
    """
    The arguments necessary to construct a `DownloadZip` resource.
    """
    def __init__(
            self,
            bucket_name: pulumi.Input[str],
            vuln_os_file: pulumi.Input[str],
            vuln_os_output_dir: pulumi.Input[str],
            vuln_os_url: pulumi.Input[str],
            vuln_os_name: pulumi.Input[str]
        ):
        """
        :param pulumi.Input[str] bucket_name: The name of the s3 bucket
        :param pulumi.Input[str] vuln_os_file: The name of the zip file to download
        :param pulumi.Input[str] vuln_os_output_dir: The output directory to download the zip file to
        :param pulumi.Input[str] vuln_os_url: The url to download the zip file from
        :param pulumi.Input[str] vuln_os_name: The name of the zip file to upload to s3
        """
        self.bucket_name = bucket_name
        self.vuln_os_file = vuln_os_file
        self.vuln_os_output_dir = vuln_os_output_dir
        self.vuln_os_url = vuln_os_url
        self.vuln_os_name = vuln_os_name

class DownloadZip(pulumi.ComponentResource):
    """
    A component resource that downloads a zip file from a url.
    """
    def __init__(
            self,
            name: str,
            args: DownloadZipArgs,
            opts: pulumi.ResourceOptions = None
        ):
        """
        """
        super().__init__("hack-lab-aws-python:DownloadZip", name, {}, opts)

        # Create a random string to use as a unique id for the zip file.
        random_string = random.RandomString(
            f"{name}-random-string",
            length=8,
            special=False,
            upper=False,
            number=False,
        )

        # Create a command to download the zip file.
        download_zip_command = command.Command(
            f"{name}-download-zip",
            command=f"wget -O {args.vuln_os_output_dir}/{args.vuln_os_file} {args.vuln_os_url}",
            user="root",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Create a command to upload the zip file to s3.
        upload_zip_command = command.Command(
            f"{name}-upload-zip",
            command=f"aws s3 cp {args.vuln_os_output_dir}/{args.vuln_os_file} s3://{args.bucket_name}/{args.vuln_os_name}",
            user="root",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Export the commands.
        self.download_zip_command = download_zip_command
        self.upload_zip_command = upload_zip_command

        # Export the random string.
        self.random_string = random_string

        # Export the component resource.
        self.register_outputs({})