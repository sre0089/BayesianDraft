import os

from pydantic import BaseModel

from bayesiandraft import __version__


class BuildInfo(BaseModel):
    name: str = "bayesiandraft"
    version: str
    commit_sha: str | None = None
    build_timestamp: str | None = None


def build_info_from_env() -> BuildInfo:
    return BuildInfo(
        version=os.getenv("BAYESIANDRAFT_VERSION", __version__),
        commit_sha=os.getenv("BAYESIANDRAFT_COMMIT_SHA"),
        build_timestamp=os.getenv("BAYESIANDRAFT_BUILD_TIMESTAMP"),
    )
