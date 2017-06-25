
KeepMyPhotos
============

Keep My Photos is a simple Flickr backup application. It will download
your photos into a specified folder, while maintaining the Flickr filename.

Files are put into folders according to their set memberships.

Running
-------

The recommended way is to use virtualenv and pip. Please see virtualenv
documentation for installing it.

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    python keepmyphotos.py -u http://www.flickr.com/photos/mine -d ~/backup

The first time, a browser window will be opened where you can authorize
KeepMyPhotos to allow to see your pictures.

Usage
-----

Run with -h argument to see all arguments:

        (venv)sorend@rebala:~/projects/KeepMyPhotos$ python mkeepmyphotos.py -h

        usage: main.py [-h] [-u URL] -d DIR [-i ID] [-o] [-N]

        Keep My Photos for backup of flickr photos

        optional arguments:
          -h, --help            show this help message and exit
          -u URL, --url URL     The photos URL of the user eg.
                        http://www.flickr.com/photos/keepmyphotos/
          -d DIR, --dir DIR     The directory where the backup resides
          -i ID, --id ID        The flickr user ID eg 12345678@N01
          -o, --original-only   Fail if original photos are not available
          -N, --not-in-set-only
                                Process "not in set" pictures only.


License
-------

License is BSD-style.
