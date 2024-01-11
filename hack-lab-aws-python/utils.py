import os
import pathlib
import urllib.error
import urllib.request
from typing import Iterator, Optional, Union
import pulumi

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
        _save_response_content(iter(lambda: response.read(chunk_size), b""), filename, length=response.length)

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

class DownloadUnzipProvider(pulumi.dynamic.ResourceProvider):
    """
    Custom dynamic provider to download and unzip the file.
    """
    def create(self, props):
        url, output_dir, filename = props["url"], props["output_dir"], props["filename"]
        if not filename: filename = os.path.basename(url)
        try:
            # Downloading zip file.
            file_path = f"{output_dir}/{filename}"
            download_url(url, output_dir, filename)
            import zipfile
            # Unzipping to extract the .ova file.
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
                for filename in os.listdir(output_dir):
                    if filename.endswith('.ova'):
                        ova_file_path = f"{output_dir}/{filename}"
                        break
            if ova_file_path:
                return pulumi.dynamic.CreateResult(ova_file_path, {})
        except Exception as e:
            raise Exception(f"Failed to download and unzip: {str(e)}")

        return pulumi.dynamic.CreateResult(id_="", outs={})

class DownloadUnzip(pulumi.dynamic.Resource):
    def __init__(
            self,
            name: str,
            url: str,
            output_dir: Union[str, pathlib.Path],
            filename: Optional[str] = None,
            opts=None
        ):
        super().__init__(DownloadUnzipProvider(), name, {
            'url': url,
            'output_dir': output_dir,
            'filename': filename,
        }, opts)