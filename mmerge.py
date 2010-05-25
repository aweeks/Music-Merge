#!/usr/bin/python
import os, glob, sys, shutil, random, fnmatch
from optparse import OptionParser
from mutagen.mp3 import EasyMP3, MP3

files = set()

artists = set()
albums = set()
titles = set()
genres = set()

artist_files = dict()
file_artists = dict()

album_files = dict()
file_albums = dict()

title_files = dict()
file_titles = dict()

genre_files = dict()
file_genres = dict()

file_tracknos = dict()
file_trackofs = dict()
file_bitrates = dict()
file_lengths  = dict()

def main():
    """
    Main program loop.  Parses command line options and controls execution.
    """
    parser = OptionParser()
    parser.add_option( "-p", "--pretend", action="store_true", dest="pretend", default=False, help="do not write any changes to disk")
    parser.add_option( "-v", "--verbose", action="store_true", dest="verbose", default=False, help="verbose output")
    parser.add_option( "-d", "--debug", action="store_true", dest="debug", default=False, help="debug output")
    parser.add_option( "-i", "--index", action="store_true", dest="index", default=False, help="index media files")
    parser.add_option( "-o", "--organize", action="store_true", dest="organize", default=False, help="organize media files")

    parser.add_option( "-m", "--merge", action="store_true", dest="merge", default=False, help="merge media files")
    parser.add_option( "-t", "--target", type="string", dest="target", default=None, help="target path")
    parser.add_option( "-f", "--format", type="string", dest="format", default="%artist/%album/%tracno %title.%ext", help="organization format")
    
    
    global options, args
    (options, args) = parser.parse_args()
    
    if options.debug:
        print "options:", options
        print "args:", args

    if options.index:
        index()

    if options.organize and not options.merge:
        if not options.target:
            parser.error("no target is selected for organize")
        index()
        organize()

    if options.merge:
        if not options.target:
            parser.error("no target is selected for organize")
        index()
        merge()
        organize()


#Taken from http://www.brunningonline.net/simon/blog/archives/002022.html
def locate(pattern, root):
    for path, dirs, files in os.walk(root):
        for filename in [os.path.abspath(os.path.join(path, filename)) for filename in files if fnmatch.fnmatch(filename, pattern)]:
            yield filename


def merge():
    """
    Examine each candidate file in turn.  Determine whether it is a duplicate.  If it is not a duplicate, add it to merged.
    If it is a duplicate, determine whether it is superior to the file that is already there, and replace it if so.
    """
    global files

    merged = dict()
    for file in files:

        artist = list(file_artists[file])[0]
        album = list(file_albums[file])[0]
        track = list(file_titles[file])[0]
        trackno = file_tracknos[file]
        bitrate = file_bitrates[file]

        unique = (artist, album, track, trackno)
        
        if not unique in merged:
            merged[unique] = file
        else:
            if bitrate > file_bitrates[merged[unique]]:
                if options.verbose:
                    print "collision: replacing with greater bitrate file:", file
                merged[unique] = file
            elif options.verbose:
                print "collision: keeping greater bitdate file:", file
    
    files = set(merged.values())


def index():
    """
    For each source indicated on the command line, iterate through all media files and add them to the index.
    In the process, build a metadata tree.
    """
    for source in args:
        for file in locate("*.mp3", source):
            if options.verbose:
                print "indexing:", file
            
            metadata = EasyMP3(file)
            mp3 = MP3(file)
            if metadata != {}:
                bitrate = mp3.info.bitrate
                length =  mp3.info.length
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
       
                file_tracknos[file] = trackno
                file_trackofs[file] = trackno
                file_bitrates[file] = bitrate
                file_lengths[file]  = length

                
                files.add(file)
                artists.add(artist)
                albums.add(album)
                titles.add(title)
                
                try:
                    for genre in metadata["genre"]:
                        genres.add(genre)
                        index_store( genre_files, file_genre, genre, file )
                except:
                    pass
                
                index_store( artist_files, file_artists, artist, file )
                index_store( album_files, file_albums, album, file )
                index_store( title_files, file_titles, title, file )
            else:
                print "error: invalid metadata"

    if options.debug:
         print "artists:", artists
         print "albums:", albums
         print "titles:", titles
         print "genres:", genres


def format(file, format=None):
    if format==None:
        format = options.format

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

        if options.verbose or options.pretend:
            print "copying:", file, "->", dest
        
        if not options.pretend:
            try:
                os.makedirs(os.path.dirname(dest))
            except:
                pass
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
