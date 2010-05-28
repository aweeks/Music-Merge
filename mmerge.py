#!/usr/bin/python
import os, glob, sys, shutil, random, fnmatch
from optparse import OptionParser
from mutagen.mp3 import EasyMP3, MP3
from mutagen.flac import FLAC

#Ugly hack, set output encoding to utf8
reload(sys)
sys.setdefaultencoding('utf8')

class MediaFile:
    FLAC = 1
    MP3  = 2
    ext = {FLAC: "flac", MP3: "mp3",}

#All files that we find
files = set()
file_types = dict()

#Artist index
artist_files = dict()
file_artists = dict()

#Album index
album_files = dict()
file_albums = dict()

#Title index
title_files = dict()
file_titles = dict()

#Genre index
genre_files = dict()
file_genres = dict()

#File info
file_tracknumbers = dict()
file_disknumbers  = dict()
file_dates        = dict()

file_bitrates = dict()
file_lengths  = dict()

def main():
    """
    Main program loop.  Parses command line options and controls execution.
    """
    parser = OptionParser(usage="usage: mmerge [OPTIONS] -t [TARGET] SRC [SRC] ...")
    parser.add_option( "-p", "--pretend", action="store_true", dest="pretend", default=False, help="do not write any changes to disk")
    parser.add_option( "-v", "--verbose", action="store_true", dest="verbose", default=False, help="verbose output")
    
    parser.add_option( "-d", "--debug", action="store_true", dest="debug", default=False, help="debug output.  Implies --verbose")
    parser.add_option( "-i", "--index", action="store_true", dest="index", default=False, help="index media files (implied by --merge or --organize)")

    parser.add_option( "-t", "--tag", action="store_true", dest="tag", default=False, help="update tags on media files based upon Music Brainz database")

    parser.add_option( "-o", "--organize", action="store_true", dest="organize", default=False, help="organize media files.  ")

    parser.add_option( "-m", "--merge", action="store_true", dest="merge", default=False, help="merge media files")
    parser.add_option( "-c", "--copy", action="store_true", dest="copy", default=False, help="copy, don't move files")

    parser.add_option( "-T", "--target", type="string", dest="target", default=None, help="target path.  When organizing or merging, files will be copied to this location according to FORMAT.")
    parser.add_option( "-P", "--priority", type="string", dest="priority", default="flac,alac,+bitrate,ogg,mp3,", help="merge file priority.  Consists of a set of order that are applied succecutively to any duplicate files.  After all orders have been applied, the first file is selected.  Default: \"{[flac,alac,ogg,mp3],+bitrate\".  This will prioritize flac, alac, ogg and mp3 in that order.  If there are two flac files with different bitrates, the file with greater bitrate will be selected, and so on.  Examples: \"+bitrate:\": select for higher bitrate regardless of format.  \"[mp3,+bitrate],[flac,-bitrate]\": select mp3 files with high bitrates, next select flac files with low bitrates.\"")
    parser.add_option( "-f", "--format", type="string", dest="format", default="%artist/%album/%trackno2 %title.%ext", help="target organization format.  When organizing or merging, files will be copied to the path specified by TARGET/FORMAT.  Options are %album, %artist, %title, %trackno[2-9] (zero padding), %trackof[2-9] (zero padding), %path, %filename, %ext (auto-selected file extension).  Default: \"%artist/%album/%trackno2 %title.%ext\".")
    
    #Perform argument parsing
    global options, args
    (options, args) = parser.parse_args()
    
    if options.debug:
        print "options:", options
        print "args:", args

    
    #Ensure target is selected if organizing or merging
    if options.organize or options.merge:
        if not options.target:
            parser.error("a target is required for --organize and --merge")
    
    if options.debug:
        options.verbose = True

    if options.merge:
        index()
        merge()
        organize()
    
    elif options.organize:
        index()
        organize()

    elif options.index:
        index()

#Taken from http://www.brunningonline.net/simon/blog/archives/002022.html
def locate(patterns, root):
    for pattern in patterns:
        for path, dirs, files in os.walk(root):
            for filename in [os.path.abspath(os.path.join(path, filename)) for filename in files if fnmatch.fnmatch(filename, pattern)]:
                yield filename



def fingerprint(file):
    artist  = list( file_artists[file] )[0]
    album   = list( file_albums[file]  )[0]
    track   = list( file_titles[file]  )[0]
        
    trackno = file_tracknumbers[file][0]
    diskno  = file_disknumbers [file][0] 
    bitrate = file_bitrates[file]

    return  (artist, album, track, trackno,)


def merge_resolve():
    for f in merge:
        conflicted = [ (file_types[file], file_bitrates[file], file,) for file in merge[f] ]
        
        #Sort by bitrate (high to low)
        ordered = sorted(conflicted, key=lambda x:x[1], reverse=True)
        
        #Sort by type
        ordered = sorted(ordered, key=lambda x:x[0])
       
        ordered = [ entry[2] for entry in ordered ]
        
        merge[f] = ordered[0]
        if options.verbose:
            print "selected:", ordered[0]
            for file in ordered[1:]:
                print "discarded:", file

    global files
    files = merge.values()


def merge():
    """
    Examine each candidate file in turn.  Determine whether it is a duplicate.
    """

    print "\nMERGING..."

    global files, merge
    merge = dict()
    
    for file in files:
        f = fingerprint(file)
        if f in merge:
            merge[f].append(file)
        else:
            merge[f] = [file,]

        if options.verbose:
            print "merged:", file
    
    merge_resolve() 

def get_tag(mp3, tag):
    if ( tag == "tracknumber" or tag == "disknumber" ):
        try:
            data = [int(val) for val in mp3[tag][0].split('/') ]
            if len(data) == 1:
                data.append(None)
        except:
            data = [None, None]
    else:
        try:
            data = mp3[tag]
        except:
            data = [None,]
    return data


def index_file(file):
    try:
        if file.endswith(".mp3"):
            media = EasyMP3(file)
            type = MediaFile.MP3
        elif file.endswith(".flac"):
            media = FLAC(file)
            type = MediaFile.FLAC
    except:
        print >> sys.stderr, "invalid file:", file
        return
        
    files.add(file)
    file_types[file] = type

    if type == MediaFile.MP3:
        file_bitrates[file] = media.info.bitrate
    else:
        file_bitrates[file] = None
    
    file_lengths[file]  = media.info.length

    index_store( file_artists, artist_files, file, get_tag(media, "artist")[0] )
    index_store( file_albums,  album_files,  file, get_tag(media, "album" )[0] )
    index_store( file_titles,  title_files,  file, get_tag(media, "title" )[0] )
    index_store( file_genres,  genre_files,  file, get_tag(media, "genre" )[0] )
        
    index_store( file_tracknumbers, None, file, get_tag(media, "tracknumber") )
    index_store( file_disknumbers,  None, file, get_tag(media, "disknumber" ) )

    index_store( file_dates,  None, file, get_tag(media, "date" ) )
    
    if options.verbose:
        print "indexed:", file
    if options.debug:
        print "    " + media.pprint().replace("\n", "\n    ")


def index():
    """
    For each source indicated on the command line, iterate through all media files and add them to the index.
    In the process, build a metadata tree.
    """
    print "\nINDEXING..."

    count = 0

    for source in args:
        for path in locate(["*.mp3", "*.flac"], source):
            index_file(path)

    if options.debug:
         print "artists:", artist_files.keys()
         print "albums:", album_files.keys()
         print "titles:", title_files.keys()
         print "genres:", genre_files.keys()
        #print file_tracknumbers.values()
        #print file_disknumbers.values()

def format(file, format=None):
    if format==None:
        format = options.format

    artist  = unicode( list(file_artists[file])[0] ).replace("/", "-")
    album   = unicode( list(file_albums[file] )[0] ).replace("/", "-")
    title   = unicode( list(file_titles[file] )[0] ).replace("/", "-")

    trackno = file_tracknumbers[file][0]
    trackof = file_tracknumbers[file][1]
    diskno  = file_disknumbers[file][0]
    diskof  = file_tracknumbers[file][1]
    
    result = format
    result = result.replace("%artist", artist)
    result = result.replace("%album",  album )
    result = result.replace("%title",  title )

    result = result.replace("%trackno2", repr(trackno).rjust(2, "0") )
    result = result.replace("%trackof2", repr(trackno).rjust(2, "0") )
    
    result = result.replace("%diskno2",  repr(diskno).rjust(2, "0") )
    result = result.replace("%diskof2",  repr(diskno).rjust(2, "0") )

    result = result.replace("%ext"    ,  MediaFile.ext[file_types[file]] )
    
    return result
    #= os.path.join(artist, album, trackno.rjust(2,'0') + ' ' + track + '.mp3' )


def organize():
  
    print "\nORGANIZING..."

    #Unique set of destinations
    dests = set()

    for file in files:
        dest = os.path.join( options.target, format(file) )

        while dest in dests:
            print "collision, appending unique identifier"
            dest += '.' + unicode(random.randint(1, 1000)).rjust(4, '0')
           
        dests.add(dest)
        
        

        if not options.pretend:
            try:
                os.makedirs(os.path.dirname(dest))
            except:
                pass
            
            if options.copy:
                shutil.copy2(file, dest)
            else:
                shutil.move(file, dest)

        if options.verbose:
            if options.copy:
                print  "copy: %s -> %s" % (file, dest,)
            else:
                print  "move: %s -> %s" % (file, dest,)

def index_store( forward, reverse, a, b): 
    
    if reverse == None:
        forward[a] = b
    else:
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
