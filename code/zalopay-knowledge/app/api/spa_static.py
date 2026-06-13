from __future__ import annotations

"""Static file serving with SPA client-route fallback."""

from pathlib import PurePosixPath

import anyio.to_thread
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


def should_spa_fallback(path: str) -> bool:
    """Return True when a missing path should serve index.html (client routes)."""
    name = PurePosixPath(path).name
    if not name or name == ".":
        return True
    # Asset requests (e.g. /assets/app.js) should stay 404 when missing.
    return "." not in name


class SPAStaticFiles(StaticFiles):
    """StaticFiles that falls back to index.html for unknown client routes."""

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or not self.html or not should_spa_fallback(path):
                raise

            index_path, stat_result = await anyio.to_thread.run_sync(self.lookup_path, "index.html")
            if stat_result is None:
                raise

            import stat as stat_module

            if not stat_module.S_ISREG(stat_result.st_mode):
                raise exc

            return self.file_response(index_path, stat_result, scope)
