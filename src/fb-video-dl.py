#!/usr/bin/python

import sys
import os
import os.path
import urllib2
import re
import argparse
import progressbar as pb
import facebook


#parses command line arguments
def parse_args():
    parser = argparse.ArgumentParser(prog='fb-video-dl', description='download a facebook video')
    parser.add_argument('url', help='facebook video url')
    parser.add_argument('-o', '--output', help='specifies the output file')
    args = parser.parse_args()

    url = args.url

    if args.output:
        path = args.output
    else:
        path = ''

    #print args.output
    return url, path


#verifies the given path
def get_clifilename(path):
    if os.name == 'posix':
        sep = '/'
    elif os.name == 'nt':
        sep = '\\'

    split_path = os.path.split(path)
    abs_path = os.path.abspath(split_path[0])

    if not os.path.exists(abs_path):
       sys.exit('error : path '+abs_path+' does not exist')

    if split_path[1] == '':
        file_name = None
    else :
        file_name = split_path[1]
        print file_name

    return abs_path, file_name


#retrieves video id
def get_fvID(fburl):
    regex = 'http[s]?://www.facebook.[a-z]{2,3}/[A-Za-z0-9\.]*/videos/(vb.[0-9]+/){0,1}([0-9]+)*/'
    match = re.search(regex, fburl)


    if match:
        videoID = match.group(2)
        return videoID
    else:
        sys.exit('cannot find video ID')
        pass


#retrieves video info
def get_vidinfo(videoID):
    try:
        try:
            graph = facebook.GraphAPI()
            vidObject = graph.get_object(videoID)
            video_url = vidObject['source']
        except facebook.GraphAPIError:
            sys.exit('error : unable to reach facebook')


        url_h = urllib2.urlopen(video_url)
        meta  = url_h.info()
        size  = meta['Content-Length']
        content_type = meta['content-type']
        format = re.search('video/(\w+)', content_type).group(1)
        if vidObject.has_key('name'):
            filename = ''.join(e for e in vidObject['name'] if e.isalnum())
        else:
            filename = None
    except urllib2.URLError:
        sys.exit('error : unable to retrieve video info')


    info = {'url':video_url, 'name':filename, 'size':size, 'format':format}
    return info


#downloads the video
def dnl_vid(url, filename, size):
    try:
        file = open(filename, 'wb')
    except IOError:
        sys.exit('cannot access file '+filename)
    size = int(size)
    dsize = 0

    widgets = ['progress: ', pb.Percentage(), ' ', pb.Bar(marker=pb.RotatingMarker()), ' ', pb.ETA(), ' ', pb.FileTransferSpeed()]
    pbar = pb.ProgressBar(widgets=widgets, maxval=size).start()

    try:
        h_url = urllib2.urlopen(url)
    except urllib2.URLError:
        sys.exit('error : cannot open url')
    try:
        while True:
            info = h_url.read(8192)
            if len(info) < 1 :
                break
            dsize += len(info)
            file.write(info)
            pbar += len(info)

        pbar.finish()
    except IOError:
        sys.exit('error : unable to download the video')

    print 'done'
    pass


if __name__ == '__main__':
    #parsing command line arguments
    args = parse_args()
    url = args[0]
    path = args[1]
    #retrieving the absolute path and the filename if any
    pf_pair = get_clifilename(path)
    path = pf_pair[0]
    if path[-1] != '/':
        path += '/'
    file_name = pf_pair[1]

    print 'checking the url'
    videoID = get_fvID(url)
    print 'retrieving information'
    info = get_vidinfo(videoID)

    if file_name:
        file_name = path + file_name + '.' + info['format']
    elif info['name']:
        file_name = path + info['name'] + '.' + info['format']
    else:
        file_name = path + videoID + '.' + info['format']

    size = info['size']
    url = info['url']

    print 'destination : ',file_name
    if int(size) >= 1000000:
        print 'video size  : ', '{:.2f}'.format(int(size)/1024.0/1024), 'M'
    elif int(size) >= 1000:
        print 'video size  : ', '{:.2f}'.format(int(size)/1024.0), 'K'

    dnl_vid(url, file_name, size)
    sys.exit()
