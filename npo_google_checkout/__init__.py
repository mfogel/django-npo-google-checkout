"""
thsutton's approach to application-specfic default settings, with
minor modifications.
https://github.com/thsutton/django-application-settings/

LICENSE FOR CODE IN THIS FILE:
https://github.com/thsutton/django-application-settings/blob/master/LICENSE
Reproduced as found on 2011/4/5:

--------------------
Copyright (c) 2009-2010 Thomas Sutton
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--------------------

"""

# TODO:
#   this fails if the setting is not defined in the user's orginial
#   settings.py
#   I guess that means this doesn't really work at all.

from sys import modules

def inject_application_default_settings(application):
    """Inject an application's default settings"""

    try:
        __import__('%s.settings' % application)

        # Import our defaults, project defaults, and project settings
        app_settings = modules['%s.settings' % application]
        def_settings = modules['django.conf.global_settings']
        settings = modules['django.conf'].settings

        # Add the values from the application.settings module
        for k in dir(app_settings):
            if k.isupper():
                name = k
                value = getattr(app_settings, name)

                # Add the value to the default settings module
                setattr(def_settings, name, value)

                # Add the value to the settings, if not already present
                if not hasattr(settings, name):
                    setattr(settings, name, value)

    except ImportError:
        # Silently skip failing settings modules
        pass

inject_application_default_settings(__name__)
