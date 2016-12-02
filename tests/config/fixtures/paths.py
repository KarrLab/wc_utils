""" Configuration; config constants point to config files; they're stored in a separate file,
    so software using wc_utils store config constants and config files locally.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-25
:Copyright: 2016, Karr Lab
:License: MIT
"""


from wc_utils.debug_logs.config import paths as debug_logs_default_paths
import os

debug_logs = debug_logs_default_paths.deepcopy()
debug_logs.default = os.path.join(os.path.dirname(__file__), 'debug.default.cfg')
