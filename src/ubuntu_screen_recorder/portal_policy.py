from typing import Tuple


def screenshot_request_policy(
    target: int,
    version: int,
    available_targets: int,
) -> Tuple[bool, bool]:
    """Return (targeted, interactive) for a Screenshot portal request.

    Screenshot target selection was added in portal v3. Older portals,
    or v3 portals that do not advertise the requested target, must fall
    back to the legacy interactive flow without a target key.
    """
    targeted = (
        version >= 3
        and bool(available_targets & target)
    )
    interactive = target in (2, 4) or not targeted
    return targeted, interactive


def screenshot_result_is_app_managed(version: int) -> bool:
    """Whether the app should copy/save the returned screenshot URI.

    Portal v2 delegates the interactive workflow to the system screenshot
    tool, which already owns persistence. Copying its URI creates duplicate
    files. Portal v3+ supports app-directed targets/results and may be saved
    by the application.
    """
    return version >= 3
