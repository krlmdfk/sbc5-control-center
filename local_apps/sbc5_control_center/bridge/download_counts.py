"""Read-only download counters for uploaded SBC5 GitHub Release ZIP assets.

GitHub does not count generated source archives or ordinary HACS installs.
A missing instrumented ZIP is UNKNOWN (None), never zero installations.
No tokens, visitor tracking, local identifiers or outbound telemetry.
"""
from __future__ import annotations

import json
import logging
import urllib.request

_LOGGER = logging.getLogger(__name__)
_REPOS = {
    "app": "sbc5-control-center",
    "hacs": "sbc5-control-center-integration",
}
_API = "https://api.github.com/repos/krlmdfk"
_PAGE_SIZE = 100
_MAX_PAGES = 20
_TIMEOUT_SECONDS = 6


def _is_downloadable_zip(source: str, name: str) -> bool:
    """Only count recognizable, installable uploaded release artifacts."""
    low = name.lower()
    if not low.endswith(".zip") or "field_test" in low or "field-test" in low:
        return False
    if source == "app":
        return low.startswith("sbc5_update_")
    return "sbc5" in low and ("integration" in low or "control_center" in low)


def count_release_assets(source: str, releases: list[dict]) -> tuple[int, bool]:
    """Return (download count, whether any countable release ZIP exists)."""
    total = 0
    found = False
    seen: set[int] = set()
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        for asset in release.get("assets") or []:
            if not isinstance(asset, dict):
                continue
            name, asset_id = asset.get("name"), asset.get("id")
            downloads = asset.get("download_count")
            if not isinstance(name, str) or not _is_downloadable_zip(source, name):
                continue
            if not isinstance(downloads, int) or isinstance(downloads, bool) or downloads < 0:
                continue
            if isinstance(asset_id, int):
                if asset_id in seen:
                    continue
                seen.add(asset_id)
            found = True
            total += downloads
    return total, found


def _fetch_repo_downloads(source: str) -> int | None:
    repo = _REPOS[source]
    total, found = 0, False
    for page in range(1, _MAX_PAGES + 1):
        url = "%s/%s/releases?per_page=%d&page=%d" % (_API, repo, _PAGE_SIZE, page)
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SBC5-Control-Center-Downloads",
        })
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            payload = response.read(4_000_001)
        if len(payload) > 4_000_000:
            raise ValueError("GitHub releases response too large")
        releases = json.loads(payload)
        if not isinstance(releases, list):
            raise ValueError("GitHub releases response is not a list")
        value, has_zip = count_release_assets(source, releases)
        total += value
        found = found or has_zip
        if len(releases) < _PAGE_SIZE:
            return total if found else None
    # Avoid a false lower count on unexpectedly long release histories.
    raise ValueError("GitHub releases exceed supported pagination")


def fetch_download_counts() -> dict[str, int | None]:
    """Fail independently for each repository; never fabricate a HACS count."""
    counts: dict[str, int | None] = {}
    for source in _REPOS:
        try:
            counts[source] = _fetch_repo_downloads(source)
        except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
            _LOGGER.debug("SBC5 download counter unavailable for %s: %s", source, exc)
            counts[source] = None
    return counts
