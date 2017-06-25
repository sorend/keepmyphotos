#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 by Soren Atmakuri Davidsen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

import urllib.request, re, sys, os, shutil, argparse
from slugify import slugify
import colorama

import urllib3
urllib3.disable_warnings()

from flickrapi import FlickrAPI
try:
    import pycurl
except:
    pass

try:
    from HTMLParser import HTMLParser   # python2
except ImportError:
    from html.parser import HTMLParser  # python3

# the api key for keepmyphotos
api_key = u'b2aa3882209c7ba57ee0930246f4ce7e'
api_secret = u'cf1da08d96ce0671'
api_access_level = u'read'

class UrllibInterface(object):
    """ URL interface with urllib based """
    def __init__(self):
        pass

    def __open(self, url):
        return urllib.request.urlopen(url)

    def read(self, url):
        return self.__open(url).read()

    def download(self, url, fh):
        reader = self.__open(url)
        fh.write(reader.read())
        reader.close()
        fh.flush()

class LibcurlInterface(object):
    """ URL interface libcurl based """
    def __init__(self):
        pass

    def read(self, url):
        body = []

        def body_callback(html):
            body.append(html)

        params = [ (pycurl.URL, url),
                   (pycurl.FOLLOWLOCATION, 1),
                   (pycurl.WRITEFUNCTION, body_callback),
                   (pycurl.NOPROGRESS, 1),
                   (pycurl.FAILONERROR, 1) ]
        self.__exec(params)

        return ''.join(body)

    def download(self, url, fh):
        params = [ (pycurl.URL, url),
                   (pycurl.FOLLOWLOCATION, 1),
                   (pycurl.WRITEDATA, fh),
                   (pycurl.NOPROGRESS, 1),
                   (pycurl.FAILONERROR, 1) ]
        self.__exec(params)

    def __exec(self, params):
        curl = pycurl.Curl()
        for name, val in params:
            curl.setopt(name, val)
        curl.perform()

class KeepMyPhotos(object):
    """
    Helper functions for importing stuff from flickr
    """
    def __init__(self, flickr, args):
        self.flickr = flickr
        self.args = args
        self.path = args.dir
        try:
            import pycurl
            self.downloader = LibcurlInterface()
            print("Using libcurl downloader")
        except:
            self.downloader = UrllibInterface()
            print("Using urllib downloader (install pycurl for more speed)")

    def find_user_id(url):
        """
        Find the user@id from flickr by loading the user-url and parsing the id (kind of hacky)
        """
        html = urllib.request.urlopen(url).read().decode('utf-8')

        m = re.search(r"href=\"/services/feeds/photos_public.gne\?([^\"]+)", html)
        if m:
            h = HTMLParser()
            uid = h.unescape(m.group(1))
            uid = uid[3:uid.index("&")]
            return uid
        else:
            return None

    find_user_id = staticmethod(find_user_id)

    def text_or_none(self, pxml, str):
        pxml.find(str).text if pxml.find(str) is not None else None

    def find_best_size(self, photo_id):
        xml = self.flickr.photos_getSizes(photo_id=photo_id)
        sizes = []
        for size in xml.find('sizes').findall('size'):
            if size.attrib['media'] == 'photo':
                sizes.append(size)
        url = sizes[-1].attrib['source']
        filename = url[url.rfind('/') + 1:]
        if '_o.' in url:
            return True, url, filename
        else:
            return False, url, filename

    def download_photo(self, url, save_file):

        # create a temp file name
        temp_file = save_file + '.temp'
        # temp_file = os.path.join(tempfile.gettempdir(), os.path.basename(save_file))

        # download to the file
        for i in range(3):
            try:
                # open temp file
                save_to = open(temp_file, 'wb')

                # download to temp file
                self.downloader.download(url, save_to)

                # flush+close
                save_to.flush()
                save_to.close()

                # move the file in place.
                shutil.move(temp_file, save_file)

                # return, we're done
                return True
            except pycurl.error:
                pass

        return False

    def backup_photo(self, photo, photos_url, slug):

        photo_id, title = int(photo.attrib['id']), photo.attrib['title']

        original, url, filename = self.find_best_size(photo_id)

        orig = '_o' if original else ''

        save_as = "%d-%s%s.jpg" % (photo_id, slugify(title), orig)

        print("\033[100D\033[K"+colorama.Fore.GREEN+" - %s" % (save_as,), end="")
        sys.stdout.flush()
        
        if self.args.original_only and not original:
            raise Exception('Original not found for %s%s/' % (photos_url, photo_id))

        # load metadata
        # xml = self.flickr.photos_getInfo(photo_id=photo_id)
        # photo = xml.find('photo')

        # save-location optoins
        save_file = os.path.join(self.path, slug, save_as)

        # setup reader/writer
        if not os.path.exists(os.path.join(self.path, slug)):
            os.makedirs(os.path.join(self.path, slug))

        # get the image if we don't have it already
        if not os.path.exists(save_file):
            self.download_photo(url, save_file)

    def find_user_url(self, user_id):
        xml = self.flickr.people_getInfo(user_id=user_id)
        return xml.find('person').find('photosurl').text

    def find_existing_photo_ids(self):
        existing_ids = []
        for dirpath in os.listdir(self.path):
            try:
                photoset_id = int(dirpath.split('-')[0])
            except:
                photoset_id = '_not_in_set'

            filenames = [ f for f in os.listdir(os.path.join(self.path, dirpath)) if f.endswith('.jpg') ]

            for filename in filenames:
                try:
                    photo_id = int(filename.split('-')[0])
                    existing_ids.append((photoset_id, photo_id))
                except:
                    pass

        return existing_ids

    def backup_flickr_all(self, user_id):

        existing_ids = self.find_existing_photo_ids()

        photos_url = self.find_user_url(user_id)

        if not self.args.not_in_set_only:
            photosets = self.flickr.photosets_getList(user_id=user_id).\
                find('photosets')

            for photoset in photosets:
                photoset_id, title = int(photoset.attrib['id']), photoset.find('title').text
                slug = "%d-%s" % (photoset_id, slugify(title))
                print(colorama.Fore.BLUE + "Processing", title, "slug", slug)
                walker = self.flickr.walk_set(photoset_id)
                for photo in walker:
                    photo_id = int(photo.attrib['id'])
                    if (photoset_id, photo_id) in existing_ids:
                        continue

                    self.backup_photo(photo=photo,
                                      slug=slug,
                                      photos_url=photos_url)
                print("")

        photos = self.flickr.photos_getNotInSet().find('photos')
        print(colorama.Fore.BLUE + "Processing 'not in set'")
        for photo in photos:
            photo_id = int(photo.attrib['id'])
            if ('_not_in_set', photo_id) in existing_ids:
                continue

            self.backup_photo(photo=photo,
                              photos_url=photos_url,
                              slug='_not_in_set')
        print("")
        print(colorama.Fore.GREEN + "All done :-)")

def main():
    """ Main, for running from command line """

    parser = argparse.ArgumentParser(description='Keep My Photos for backup of flickr photos')
    parser.add_argument('-u', '--url', help='The photos URL of the user eg. http://www.flickr.com/photos/keepmyphotos/')
    parser.add_argument('-d', '--dir', help='The directory where the backup resides', required=True)
    parser.add_argument('-i', '--id', help='The flickr user ID eg 12345678@N01')
    parser.add_argument('-o', '--original-only', help='Fail if original photos are not available', action='store_true')
    parser.add_argument('-N', '--not-in-set-only', help='Process "not in set" pictures only.', action='store_true')
    args = parser.parse_args()

    if args.url is not None:
        args.id = KeepMyPhotos.find_user_id(args.url)

    if args.id is None:
        print(colorama.Fore.RED + "Please specify -u <photostream url> OR -i user@id")
    else:
        # get api
        flickr = FlickrAPI(api_key, api_secret)

        # init authentication for the flickr api.
        if not flickr.token_valid(perms=api_access_level):
            flickr.get_request_token(oauth_callback='oob')
            authorize_url = flickr.auth_url(perms=api_access_level)
            print("Open authorize_url: %s" % (authorize_url,))
            verifier = input('Verifier code: ')
            flickr.get_access_token(verifier)

        kmp = KeepMyPhotos(flickr, args)
        kmp.backup_flickr_all(args.id)

if __name__ == "__main__":
    main()
