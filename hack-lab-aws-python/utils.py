import os
import shutil
import pathlib
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterator, Optional, Union, List
import pulumi
import pulumi_random as random
import zipfile

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def _get_redirect_url(url: str, max_hops: int = 3) -> str:
    initial_url = url
    headers = {"Method": "HEAD", "User-Agent": USER_AGENT}

    for _ in range(max_hops + 1):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as response:
            if response.url == url or response.url is None:
                return url

            url = response.url
    else:
        raise RecursionError(
            f"Request to {initial_url} exceeded {max_hops} redirects. The last redirect points to {url}."
        )

def _save_response_content(
    content: Iterator[bytes],
    destination: str,
) -> None:
    with open(destination, "wb") as fh:
        for chunk in content:
            if not chunk: continue # filter out keep-alive new chunks
            fh.write(chunk)

def _urlretrieve(url: str, filename: str, chunk_size: int = 1024 * 32) -> None:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT})) as response:
        _save_response_content(iter(lambda: response.read(chunk_size), b""), filename)

def download_url(
        url: str,
        output_dir: Union[str, pathlib.Path],
        filename: Optional[str] = None,
        max_redirect_hops: int = 3
    ):
    """
    Download a file from a url and place it in output_dir.

    Args:
        url (str): URL to download file from
        output_dir (str): Directory to place downloaded file in
        filename (str, optional): Name to save the file under. If None, use the basename of the URL
        max_redirect_hops (int, optional): Maximum number of redirect hops allowed
    """
    output_dir = os.path.expanduser(output_dir)
    if not filename: filename = os.path.basename(url)
    fpath = os.fspath(os.path.join(output_dir, filename))
    os.makedirs(output_dir, exist_ok=True)
    url = _get_redirect_url(url, max_hops=max_redirect_hops) # expand redirect chain if needed
    try: # download the file
        print("Downloading " + url + " to " + fpath)
        _urlretrieve(url, fpath)
    except (urllib.error.URLError, OSError) as e:  # type: ignore[attr-defined]
        if url[:5] == "https":
            url = url.replace("https:", "http:")
            print("Failed download. Trying https -> http instead. Downloading " + url + " to " + fpath)
            _urlretrieve(url, fpath)
        else:
            raise e

#----------------------------------------------
# DownloadUnzip - Pulumi Dynamic Provider
#----------------------------------------------
@dataclass
class DownloadUnzipInputArgs:
    url: str = ""
    output_dir: Union[str, pathlib.Path] | None = None
    filename: Optional[str] = None

@dataclass
class DownloadUnzipOutputArgs(DownloadUnzipInputArgs):
    id: str = ""
    name: str = ""
    ova_filename: str | None = None
    extract_dir: Union[str, pathlib.Path] | None = None

class DownloadUnzipProvider(pulumi.dynamic.ResourceProvider):
    """
    Custom dynamic provider to download and unzip the file.
    """
    def __init__(self, name: str) -> None:
        self.name = name
    
    def check(self, _olds: DownloadUnzipInputArgs, _news: DownloadUnzipInputArgs) -> pulumi.dynamic.CheckResult:        
        failures: List[pulumi.dynamic.CheckFailure] = []
        required_props: str = ["url", "output_dir"]
        for prop in required_props:
            if not getattr(_news, prop): failures.append(pulumi.dynamic.CheckFailure(property=prop, reason=f"'{prop}' is required"))
        return pulumi.dynamic.CheckResult(inputs=_olds if len(failures) else _news, failures=failures)

    def create(self, inputs: DownloadUnzipInputArgs) -> pulumi.dynamic.CreateResult:
        url, output_dir, filename = inputs["url"], inputs["output_dir"], inputs["filename"]
        if not filename: filename = os.path.basename(url)
        _outs = DownloadUnzipOutputArgs(
            name=self.name,
            url=url,
            output_dir=output_dir,
            filename=filename,
        )
        try:
            # Downloading zip file.
            download_url(url, output_dir, filename)
            file_path = os.path.join(output_dir, filename)
            # Unzipping to extract the .ova file.
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_name_without_ext, _ = os.path.splitext(filename)
                extract_dir = os.path.join(output_dir, file_name_without_ext)
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir)
                else: # remove everything in the temp directory
                    for f in os.listdir(extract_dir): os.remove(os.path.join(extract_dir, f)) 
                zip_ref.extractall(extract_dir)
                for filename in os.listdir(extract_dir):
                    if filename.endswith('.ova'):
                        _outs.ova_filename = os.path.join(extract_dir, filename)
                        break
            if _outs.ova_filename:
                _id = random.RandomId("id", keepers={ "file": _outs.ova_filename }, byte_length=4).hex
                _outs.id = _id
                _outs.extract_dir = extract_dir
                return pulumi.dynamic.CreateResult(id=_id, outs=_outs)
        except Exception as e: raise Exception(f"Failed to download and unzip: {str(e)}")
        return pulumi.dynamic.CreateResult(id_="", outs=_outs)
    
    def update(self, id: str, _olds: DownloadUnzipOutputArgs, _news: DownloadUnzipInputArgs) -> pulumi.dynamic.UpdateResult:
        _outs: DownloadUnzipOutputArgs = _olds
        _props: List[str] = ["url", "output_dir", "filename"]
        for prop in _props:
            if getattr(_olds, prop) != getattr(_news, prop): setattr(_outs, prop, getattr(_news, prop))
        return pulumi.dynamic.UpdateResult(id=id, outs=_outs)
    
    def delete(self, id: str, _props: DownloadUnzipOutputArgs) -> None:
        print(f"Deleting {_props.name}({id}) ...")
        if os.path.exists(_props.extract_dir):
            print(f"Deleting {_props.extract_dir}...")
            shutil.rmtree(_props.extract_dir)
        _file = os.path.join(_props.output_dir, _props.filename)
        if os.path.exists(_file):
            print(f"Deleting {_props.filename} from {_props.output_dir}...")
            os.remove(_file)
        print(f"Deleted {_props.name}({id})")

class DownloadUnzip(pulumi.dynamic.Resource):
    def __init__(
            self,
            name: str,
            args: DownloadUnzipInputArgs,
            opts: Optional[pulumi.ResourceOptions] = None,
        ):
        super().__init__(DownloadUnzipProvider(name), f"download:zip:{name}", args, opts)