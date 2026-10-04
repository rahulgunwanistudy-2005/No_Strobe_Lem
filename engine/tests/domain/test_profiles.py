import subprocess
import sys
from dataclasses import FrozenInstanceError, replace

import pytest

from nostrobe.domain.profiles import get_profile
from nostrobe.errors import ProfileError


def test_profile_values_and_hash() -> None:
    broadcast, local, kids = [get_profile(name) for name in ("broadcast", "local", "kids")]
    assert [p.max_changes_per_s for p in (broadcast, local, kids)] == [6, 6, 4]
    assert [p.area_rule for p in (broadcast, local, kids)] == ["global", "local", "local"]
    assert [p.veil_warn for p in (broadcast, local, kids)] == [False, False, True]
    assert len({p.params_hash() for p in (broadcast, local, kids)}) == 3
    assert replace(broadcast, sync_tolerance_s=0.2).params_hash() != broadcast.params_hash()
    with pytest.raises(FrozenInstanceError):
        broadcast.lead_s = 0
    with pytest.raises(ProfileError):
        get_profile("typo")


def test_hash_is_stable_across_processes() -> None:
    command = [
        sys.executable,
        "-c",
        "from nostrobe.domain.profiles import get_profile; "
        "print(get_profile('broadcast').params_hash())",
    ]
    result = subprocess.check_output(command, text=True).strip()
    assert result == get_profile("broadcast").params_hash()
