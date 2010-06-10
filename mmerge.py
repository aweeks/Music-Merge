#!/usr/bin/python
#
#Music Merge.  Sane music library merging.
#Copyright (C) 2010  Alex Weeks
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, glob, sys, shutil, random, fnmatch, pickle
from optparse import OptionParser
from mediafile import *

#Ugly hack, set output encoding to utf8
reload(sys)
sys.setdefaultencoding('utf8')


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
file_tracknos = dict()
file_trackofs = dict()
file_disknos  = dict()
file_diskofs  = dict()
file_dates        = dict()

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
    for path, dirs, files in os.walk(root):
        for file in [os.path.abspath(os.path.join(path, filename)) for filename in files]:
            yield file


def merge_resolve():
    for fingerprint in merge:
        conflicted = [ (file, file.bitrate, ) for file in merge[fingerprint] ]
        
        #Sort by bitrate (high to low)
        ordered = sorted(conflicted, key=lambda x:x[1], reverse=True)
        
        #Refactor the ordered list, only selecting files
        ordered = [ entry[0] for entry in ordered ]
        
        #Place selected file back in merge
        merge[fingerprint] = ordered[0]
        
        if options.verbose:
            print "selected:", "(%f kb/s)" % (file.bitrate/1000.0,), ordered[0]
            for file in ordered[1:]:
                print "discarded:", "(%f kb/s)" % (file.bitrate/1000.0,), file

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
        fingerprint = file.fingerprint()
        if fingerprint in merge:
            merge[fingerprint].append(file)
        else:
            merge[fingerprint] = [file,]

        if options.verbose:
            print "merged:", file
    
    merge_resolve() 


def index_file( path ):
    try:
        file = MediaFile.auto(path)
    except:
        print >> sys.stderr, "invalid file:", path
        return
    if not isinstance(file, MediaFile):
        return

    files.add(file)
    
    index_store( file_artists, artist_files, file, file.metadata["artist"] )
    index_store( file_albums,  album_files,  file, file.metadata["album"] )
    index_store( file_titles,  title_files,  file, file.metadata["title"] )
    index_store( file_genres,  genre_files,  file, file.metadata["genre"] )
        
    index_store( file_tracknos, None, file, file.metadata["trackno"] )
    index_store( file_trackofs, None, file, file.metadata["trackof"] )
    
    index_store( file_disknos,  None, file, file.metadata["diskno" ] )
    index_store( file_diskofs,  None, file, file.metadata["diskof" ] )


    #index_store( file_dates,  None, file, get_tag(media, "date" ) )
    
    if options.verbose:
        print "indexed:", file
    if options.debug:
        print "length:", file.length
        print "bitrate:", file.bitrate
        print file.metadata


def index():
    """
    For each source indicated on the command line, iterate through all media files and add them to the index.
    In the process, build a metadata tree.
    """
    print "\nINDEXING..."

    count = 0

    for source in args:
        for path in locate(["*.mp3", "*.flac",], source):
            index_file(path)

    if options.debug:
         print "files:", files
         print "artists:", artist_files.keys()
         print "albums:", album_files.keys()
         print "titles:", title_files.keys()
         print "genres:", genre_files.keys()


def organize():
  
    print "\nORGANIZING..."

    #Unique set of destinations
    dests = set()
    
    global files
    for file in files:
        dest = os.path.join( options.target, file.format(options.format)  )

        while dest in dests:
            print "collision, appending unique identifier"
            dest += '.' + unicode(random.randint(1, 1000)).rjust(4, '0')
           
        dests.add(dest)
        
        if not options.pretend:
            try:
                os.makedirs(os.path.dirname(dest))
            except:
                pass
            try:
            	if options.copy:
                	shutil.copy2(file.path, dest)
            	else:
                	shutil.move(file.path, dest)
	    except:
	        pass

        try:
		if options.verbose:
			if options.copy:
               	 		print  "copy: %s -> %s" % (file.path, dest,)
            		else:
               	 		print  "move: %s -> %s" % (file.path, dest,)
	except:
		pass
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
