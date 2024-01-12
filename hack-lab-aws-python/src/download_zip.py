import pulumi
import pulumi_command as command
import pulumi_random as random
import pathlib
import os

class DownloadZipArgs:
    """
    The arguments necessary to construct a `DownloadZip` resource.
    """
    def __init__(
            self,
            url: pulumi.Input[str],
            output_dir: pulumi.Input[str] | pulumi.Input[pathlib.Path],
            filename: pulumi.Input[str] | pulumi.Input[pathlib.Path] | None = None
        ):
        """
        Constructs a DownloadZipArgs.

        url: Url to download the zip file from.
        output_dir: The directory to download the zip file to.
        filename: The name of the zip file to save as. If not provided, the filename will be extracted from the url.
        """
        self.url = url
        self.output_dir = output_dir
        self.filename = filename

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
        _name = f"download:zip"
        super().__init__(f"{pulumi.get_project()}:{_name}", name, vars(args), opts)

        # self.env = command.local.Command(
        #     f"env", 
        #     args=command.local.CommandArgs(
        #         create="env | grep AWS",
        #         update="env | grep AWS",
        #         delete="env | grep AWS",
        #     ),
        # )
        args.output_dir = os.path.expanduser(args.output_dir)
        if not args.filename: args.filename = os.path.basename(args.url)
        fpath = os.fspath(os.path.join(args.output_dir, args.filename))
        os.makedirs(args.output_dir, exist_ok=True)

        # self.wget = command.local.run(
        #     command=f"wget {args.url} -O {fpath}",
        #     interpreter=["/bin/bash", "-c"],
        # )

        self.wget = command.local.Command(
            f"{_name}:wget",
            args=command.local.CommandArgs(
                create=f"wget {args.url} -O {fpath}",
                update=f"wget {args.url} -O {fpath}",
                delete=f"rm {fpath}",
            ),
        )



        # # Create a random string to use as a unique id for the zip file.
        # random_string = random.RandomString(
        #     f"{name}-random-string",
        #     length=8,
        #     special=False,
        #     upper=False,
        #     number=False,
        # )

        # # Create a command to download the zip file.
        # download_zip_command = command.Command(
        #     f"{name}-download-zip",
        #     command=f"wget -O {args.vuln_os_output_dir}/{args.vuln_os_file} {args.vuln_os_url}",
        #     user="root",
        #     opts=pulumi.ResourceOptions(parent=self),
        # )

        # # Create a command to upload the zip file to s3.
        # upload_zip_command = command.Command(
        #     f"{name}-upload-zip",
        #     command=f"aws s3 cp {args.vuln_os_output_dir}/{args.vuln_os_file} s3://{args.bucket_name}/{args.vuln_os_name}",
        #     user="root",
        #     opts=pulumi.ResourceOptions(parent=self),
        # )

        # # Export the commands.
        # self.download_zip_command = download_zip_command
        # self.upload_zip_command = upload_zip_command

        # # Export the random string.
        # self.random_string = random_string

        # Export the component resource.
        self.register_outputs({})