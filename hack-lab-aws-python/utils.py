import hashlib
import os
from typing import Any, Callable, Dict, IO, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union
import pathlib

def download_url(
    url: str,
    root: Union[str, pathlib.Path],
    filename: Optional[str] = None,
    md5: Optional[str] = None,
    max_redirect_hops: int = 3,
) -> None:
    """Download a file from a url and place it in root.

    Args:
        url (str): URL to download file from
        root (str): Directory to place downloaded file in
        filename (str, optional): Name to save the file under. If None, use the basename of the URL
        md5 (str, optional): MD5 checksum of the download. If None, do not check
        max_redirect_hops (int, optional): Maximum number of redirect hops allowed
    """
    root = os.path.expanduser(root)
    if not filename:
        filename = os.path.basename(url)
    fpath = os.fspath(os.path.join(root, filename))

    os.makedirs(root, exist_ok=True)

    # check if file is already present locally
    if check_integrity(fpath, md5):
        print("Using downloaded and verified file: " + fpath)
        return

    if _is_remote_location_available():
        _download_file_from_remote_location(fpath, url)
    else:
        # expand redirect chain if needed
        url = _get_redirect_url(url, max_hops=max_redirect_hops)

        # check if file is located on Google Drive
        file_id = _get_google_drive_file_id(url)
        if file_id is not None:
            return download_file_from_google_drive(file_id, root, filename, md5)

        # download the file
        try:
            print("Downloading " + url + " to " + fpath)
            _urlretrieve(url, fpath)
        except (urllib.error.URLError, OSError) as e:  # type: ignore[attr-defined]
            if url[:5] == "https":
                url = url.replace("https:", "http:")
                print("Failed download. Trying https -> http instead. Downloading " + url + " to " + fpath)
                _urlretrieve(url, fpath)
            else:
                raise e

    # check integrity of downloaded file
    if not check_integrity(fpath, md5):
        raise RuntimeError("File not found or corrupted.")