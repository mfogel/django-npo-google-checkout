from distutils.core import setup

setup(
    name='django-npo-google-checkout',
    version='0.1',
    description="Implements google checkout's non-profit checkout and notification API's.",
    author='Mike Fogel',
    author_email='mike@fogel.ca',
    url='http://github.com/carbonXT/django-npo-google-checkout',
    packages=['npo_google_checkout'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities',
    ],
) 
