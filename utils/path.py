import os
from os.path import abspath, exists, join
from typing import List


def build_path(paths: List[str], use_cwd=False, with_filename=True) -> str:
    filename = ""
    if with_filename:
        filename = paths.pop()
    if use_cwd:
        directory = join(*paths)
    else:
        directory = join(root_dir(), *paths)
    if not exists(directory):
        os.makedirs(directory)
    return join(directory, filename) if with_filename else directory


def root_dir():
    return abspath(os.sep)
