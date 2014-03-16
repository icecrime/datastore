from datetime import datetime

from pytz import timezone

from datastore.api import config


def human_size(size):
    for x in [' bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f%s" % (size, x)
        size /= 1024.0


def human_timestamp(ts):
    if not isinstance(ts, datetime):  # pragma: no cover
        ts = datetime.fromtimestamp(ts or .0)
    ts = timezone(config.server_tz).localize(ts)
    return ts.strftime('%a, %d %b %Y %H:%M:%S %z')
