import logging

class FileRequestHandler(logging.FileHandler):
    """
    Append the request body and any other useful info before emiting
    the log record.
    """

    fmt = '%(levelname)-3.3s:%(asctime)s:%(filename)s:%(lineno)s: %(message)s'

    def __init__(self, *args, **kwargs):
        # the __init__ method of the parent sets self.formatter to None.
        logging.FileHandler.__init__(self, *args, **kwargs)
        self.setFormatter(logging.Formatter(self.fmt))

    def emit(self, record):
        raw_post_data = None
        if hasattr(record, 'request') and \
                hasattr(record.request, 'raw_post_data'):
            raw_post_data = record.request.raw_post_data
        if hasattr(record, 'raw_post_data'):
            raw_post_data = record.raw_post_data

        if raw_post_data:
            record.msg = "{0}\n{1}\n". \
                    format(record.msg, raw_post_data)
        # logging handler classes are still 'classic' classes, arg.
        return logging.FileHandler.emit(self, record)
