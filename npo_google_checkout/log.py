import logging

class FileRequestHandler(logging.FileHandler):
    """
    Append the request body and any other useful info before emiting
    the log record.
    """
    def emit(self, record):
        if record.request:
            record.msg = "\n -- {0} request.raw_post_data below --\n{1}".\
                    format(record.msg, record.request.raw_post_data)
        # logging handler classes are still 'classic' classes, arg.
        return logging.FileHandler.emit(self, record)
