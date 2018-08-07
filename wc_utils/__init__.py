import pkg_resources

with open(pkg_resources.resource_filename('wc_utils', 'VERSION'), 'r') as file:
    __version__ = file.read().strip()
# :obj:`str`: version

# define API
from . import config
from . import data_logs
from . import debug_logs
from . import quilt
from . import util
from . import workbook
