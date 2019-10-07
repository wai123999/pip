import logging
import os
import site
import sys

from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Optional, List

logger = logging.getLogger(__name__)


def _running_under_venv():
    # type: () -> bool
    """Checks if sys.base_prefix and sys.prefix match.

    This handles PEP 405 compliant virtual environments.
    """
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _running_under_regular_virtualenv():
    # type: () -> bool
    """Checks if sys.real_prefix is set.

    This handles virtual environments created with pypa's virtualenv.
    """
    # pypa/virtualenv case
    return hasattr(sys, 'real_prefix')


def running_under_virtualenv():
    # type: () -> bool
    """Return a boolean, whether running under a virtual environment.
    """
    return _running_under_venv() or _running_under_regular_virtualenv()


def _get_pyvenv_cfg_lines():
    # type: () -> Optional[List[str]]
    """Reads {sys.prefix}/pyvenv.cfg and returns its contents as list of lines

    Returns None, if it could not read/access the file.
    """
    pyvenv_cfg_file = os.path.join(sys.prefix, 'pyvenv.cfg')
    try:
        with open(pyvenv_cfg_file) as f:
            return f.read().splitlines()  # avoids trailing newlines
    except OSError:
        return None


def _no_global_under_venv():
    # type: () -> bool
    """Check `{sys.prefix}/pyvenv.cfg` for system site-packages inclusion

    PEP 405 specifies that when system site-packages are not supposed to be
    visible from a virtual environment, `pyvenv.cfg` must contain the following
    line:

        include-system-site-packages = false

    Additionally, log a warning if accessing the file fails.
    """
    cfg_lines = _get_pyvenv_cfg_lines()
    if cfg_lines is None:
        # We're not in a "sane" venv, so assume there is no system
        # site-packages access (since that's PEP 405's default state).
        logger.warning(
            "Could not access 'pyvenv.cfg' despite a virtual environment "
            "being active. Assuming global site-packages is not accessible "
            "in this environment."
        )
        return True

    return "include-system-site-packages = false" in cfg_lines


def _no_global_under_regular_virtualenv():
    # type: () -> bool
    """Check if "no-global-site-packages.txt" exists beside site.py

    This mirrors logic in pypa/virtualenv for determining whether system
    site-packages are visible in the virtual environment.
    """
    site_mod_dir = os.path.dirname(os.path.abspath(site.__file__))
    no_global_site_packages_file = os.path.join(
        site_mod_dir, 'no-global-site-packages.txt',
    )
    return os.path.exists(no_global_site_packages_file)


def virtualenv_no_global():
    # type: () -> bool
    """Returns a boolean, whether running in venv with no system site-packages.
    """

    if _running_under_regular_virtualenv():
        return _no_global_under_regular_virtualenv()

    if _running_under_venv():
        return _no_global_under_venv()

    return False
