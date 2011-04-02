"""
An http client that can make requests similar to how the google checkout
bot when it implements the notification api, version 2.5
"""

from django.test.client import Client

class GCClient(Client):
    def post_notification(self, path, raw_post_data):
        """
        Post a notificaiton similar to how google checkout bot does it.
        """
        content_type = "application/xml; charset=UTF-8"
        return self.post(path, data=raw_post_data, content_type=content_type)



    



