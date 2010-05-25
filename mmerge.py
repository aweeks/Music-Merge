#!/usr/bin/python
import os, glob, sys, shutil, random, fnmatch
from optparse import OptionParser
from mutagen.mp3 import EasyMP3

files = set()
artists = set()
albums = set()
titles = set()

artist_files = dict()
file_artists = dict()

album_files = dict()
file_albums = dict()

title_files = dict()
file_titles = dict()

file_tracknos = dict()
file_trackofs = dict()

def main():
    parser = OptionParser()
    parser.add_option( "-p", "--pretend", action="store_true", dest="pretend", default=False, help="do not write any changes to disk")
    parser.add_option( "-v", "--verbose", action="store_true", dest="verbose", default=False, help="verbose output")
    parser.add_option( "-d", "--debug", action="store_true", dest="debug", default=False, help="debug output")
    parser.add_option( "-i", "--index", action="store_true", dest="index", default=False, help="index media files")
    parser.add_option( "-o", "--organize", action="store_true", dest="organize", default=False, help="organize media files")
    parser.add_option( "-t", "--target", type="string", dest="target", default=None, help="target path")
    
    
    global options, args
    (options, args) = parser.parse_args()
    
    if options.debug:
        print "options:", options
        print "args:", args

    if options.index:
        index()

    if options.organize:
        if not options.target:
            parser.error("no target is selected for organize")
        index()
        organize()



#Taken from http://www.brunningonline.net/simon/blog/archives/002022.html
def locate(pattern, root):
    for path, dirs, files in os.walk(root):
        for filename in [os.path.abspath(os.path.join(path, filename)) for filename in files if fnmatch.fnmatch(filename, pattern)]:
            yield filename


def index():
    for source in args:
        for file in locate("*.mp3", source):
            if options.verbose:
                print "indexing:", file
            
            metadata = EasyMP3(file)
            if metadata != {}:
                artist = metadata["artist"][0]
                album = metadata["album"][0]
                title = metadata["title"][0]
                
                trackno = None
                trackof = None
                try:
                    trackno = int( metadata["tracknumber"][0].split('/')[0] )
                    trackof = int( metadata["tracknumber"][0].split('/')[1] )
                except:
                    pass
        
                files.add(file)
                artists.add(artist)
                albums.add(album)
                titles.add(title)

                file_tracknos[file] = trackno
                file_trackofs[file] = trackno

                index_store( artist_files, file_artists, artist, file )
                index_store( album_files, file_albums, album, file )
                index_store( title_files, file_titles, title, file )
            else:
                print "error: invalid metadata"

    if options.debug:
         print "artists:", artists
         print "albums:", albums
         print "titles:", titles


def format(file):
    artist = list(file_artists[file])[0]
    album = list(file_albums[file])[0]
    track = list(file_titles[file])[0]
    trackno = file_tracknos[file]

    format = os.path.join(artist, album, str(trackno).rjust(2,'0') + ' ' + track + '.mp3' )

    return format


def organize():
   
    #Unique set of destinations
    dests = set()

    for file in files:
        dest = os.path.join( options.target, format(file) )

        while dest in dests:
            print "collision: appending unique identifier"
            dest += '.' + str(random.randint(1, 1000)).rjust(4, '0')
           
        dests.add(dest)

        print "copying:", file, "->", dest
        
        if not options.pretend:
            os.makedirs(dest)
            shutil.copy2(file, dest)



def index_store( forward, reverse, a, b): 
        #Store forward relationship
        if a not in forward:
            forward[a] = set([b,])
        else:
            forward[a].add(b)

        #Store reverse relationship
        if b not in reverse:
            reverse[b] = set([a,])
        else:
            reverse[b].add(a)



main()
