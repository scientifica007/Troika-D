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
