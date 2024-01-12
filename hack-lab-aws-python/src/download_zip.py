import pulumi
import pulumi_command as command
import pulumi_random as random

class DownloadZipArgs:
    """
    The set of arguments for constructing a DownloadZip resource.
    """
    def __init__(self,
                 bucket_name: pulumi.Input[str],
                 vuln_os_file: pulumi.Input[str],
                 vuln_os_output_dir: pulumi.Input[str],
                 vuln_os_url: pulumi.Input[str],
                 vuln_os_name: pulumi.Input[str]):
        self.bucket_name = bucket_name
        self.vuln_os_file = vuln_os_file
        self.vuln_os_output_dir = vuln_os_output_dir
        self.vuln_os_url = vuln_os_url
        self.vuln_os_name = vuln_os_name