#!/usr/bin/env python
# encoding: utf-8


"""Mangafox Download Script by Kunal Sarkhel <theninja@bluedevs.net>"""

import sys
import os
import glob
import shutil
import re
import json
from zipfile import ZipFile
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
from contextlib import closing
try:
        from collections import OrderedDict
except ImportError:
        from ordereddict import OrderedDict
try:
    from urllib.request import urlopen, urlretrieve
except ImportError:
    from urllib import urlopen, urlretrieve
from itertools import islice
from functools import reduce

URL_BASE = "http://www.mangapanda.com/"
chapter_names = None

    
def get_manga_url(manga_name):
    """Return the url of the given manga"""
    replace = lambda s, k: s.replace(k, '-')
    manga_name = reduce(replace, [' ', '-'], manga_name.lower())
    url = URL_BASE + manga_name + '/'
    print('Url: ' + url)
    return url

def get_page_soup(url):
    """Download a page and return a BeautifulSoup object of the html"""
    with closing(urlopen(url)) as html_file:
        page = html_file.read()
    if re.search("404 Not Found", str(page)):
        return None
    else:
        return BeautifulSoup(page)
    
def get_nb_pages(page):
    """Get the number of pages of this chapter"""
    div = page.find('div', {'id':'selectpage'})
    options = div.select('option')
    return len(options)

def getMangaId(page):
    """Parse the managa Id"""
    search = re.search('document\[\'mangaid\'\] = (.+);', str(page))
    if search is not None:
        return search.group(1)
    else:
        return None

def get_chapter_name(page, chapter_number):
    """Return the parsed chapter name"""
    global chapter_names
    mangaid = getMangaId(page)
    if mangaid is not None:
        url = URL_BASE + 'actions/selector/?id={0}&which=0'.format(mangaid)
        if chapter_names is None:
            chapter_names = urlopen(url).read();
            chapter_names = json.loads(chapter_names.decode())
        for i in range(len(chapter_names)):
            if int(chapter_names[i]['chapter']) == chapter_number:
                return chapter_names[i]['chapter_name']
    return ''
    
def create_download_dir(manga_name):
    download_dir = './{0}/temp'.format(manga_name)
    try:
        os.makedirs(download_dir)
    except OSError:
        pass
    return download_dir

def download_image(filename, image_url):
    """Download the image to the given directory"""
    print('Downloading {0} to {1}'.format(image_url, filename))
    urlretrieve(image_url, filename)
   
def make_cbz(dirname, chapter, chapter_name):
    """Create CBZ files for all JPEG image files in a directory."""
    if chapter < 10:
        chapter = '0' + str(chapter)
    zipname = '{0}/[{1}] {2}.cbz'.format(dirname, chapter, chapter_name)
    zipname = os.path.abspath(zipname)
    images = glob.glob(os.path.abspath(dirname) + '/temp/*.jpg')
    with closing(ZipFile(zipname, 'w')) as zipfile:
        for filename in images:
            print('writing {0} to {1}'.format(filename, zipname))
            zipfile.write(filename)

    
    
def download_chapter(url, manga_name, chapter, chapter_name, nb_pages):
    """ Download the chapter of the given url"""
    download_dir = create_download_dir(manga_name)
    for i in range(1, nb_pages+1):
        page_url = '{0}/{1}'.format(url, i)
        page = get_page_soup(page_url)
        if page is not None:
            image_url = page.find('img', {'id':'img'})['src']
            filename = '{0}/{1}.jpg'.format(download_dir, i)
            download_image(filename, image_url)
    save_dir = os.path.join(download_dir, os.pardir)
    make_cbz(save_dir, chapter, chapter_name)
    shutil.rmtree(download_dir)

def download_manga(manga_name, start=None, end=None):
    """Download the chapters of a manga from start to end
       If start is None we start downloading from chapter 1
       If end is None we download all chapter until the 
       last availible chapter.
    """
    url = get_manga_url(manga_name)
    if start is None:
        start = 1
    else:
        start = int(start)
    if end is not None:
        end = int(end)
    while end is None or end >= start:
        chapter_url = url + str(start)
        page = get_page_soup(chapter_url)
        if page is None:
            print('Got None from ' + chapter_url)
            break
        chapter_name = get_chapter_name(page, start)
        nb_pages = get_nb_pages(page)
        print("There's {0} pages".format(nb_pages))
        download_chapter(chapter_url, manga_name, start, chapter_name, nb_pages)
        start = start + 1

if __name__ == '__main__':
    size = len(sys.argv)
    if size == 4:
        if sys.argv[2] == '-s':
            download_manga(sys.argv[1], sys.argv[3])
        else:
            download_manga(sys.argv[1], sys.argv[2], sys.argv[3])
    elif size == 3:
        download_manga(sys.argv[1], sys.argv[2], sys.argv[2])
    elif size == 2:
        download_manga(sys.argv[1])
    else:
        print('USAGE: {0} MANGA_NAME'.format(sys.argv[0]))
        print('       {0} MANGA_NAME -s START_CHAPTER'.format(sys.argv[0]))
        print('       {0} MANGA_NAME CHAPTER_NUMBER'.format(sys.argv[0]))
        print('       {0} MANGA_NAME START_CHAPTER END_CHAPTER'.format(sys.argv[0]))
