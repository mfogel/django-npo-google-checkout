import logging

class FileRequestHandler(logging.FileHandler):
    """
    Append the request body and any other useful info before emiting
    the log record.
    """
    def emit(self, record):
        raw_post_data = None
        if hasattr(record, 'request') and \
                hasattr(record.request, 'raw_post_data'):
            raw_post_data = record.request.raw_post_data
        if hasattr(record, 'raw_post_data'):
            raw_post_data = record.raw_post_data

        if raw_post_data:
            record.msg = "\n -- {0}\n -- raw_post_data below:\n{1}". \
                    format(record.msg, raw_post_data)
        # logging handler classes are still 'classic' classes, arg.
        return logging.FileHandler.emit(self, record)
