"""Lexical operations on path metadata recorded by another operating system."""

from pathlib import PurePosixPath, PureWindowsPath


def _path(value: str) -> PurePosixPath | PureWindowsPath:
    if "\\" in value or value.startswith("//") or (len(value) >= 2 and value[1] == ":"):
        return PureWindowsPath(value)
    return PurePosixPath(value)


def stored_parent(value: str) -> str:
    return str(_path(value).parent) if value else ""


def stored_path_key(value: str) -> str:
    if not value:
        return ""
    path = _path(value)
    key = path.as_posix()
    return key.casefold() if isinstance(path, PureWindowsPath) else key
