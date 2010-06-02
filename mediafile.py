from mutagen.mp3 import EasyMP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

class MediaFile(object):
  
    @staticmethod
    def auto(path):
        if path.endswith(".mp3"):
            return MP3File(path)
        elif path.endswith(".flac"):
            return FLACFile(path)
        elif path.endswith(".mp4") or path.endswith(".m4a"):
            return MP4File(path)

        return None

    def __init__(self, path):
        self.path = path
    
    def __eq__(self, other):
        return self.path == other.path
        
    
    def __hash__(self):
        return self.path.__hash__()

    def fingerprint(self):
        return (self.metadata["artist"], self.metadata["album"],
            self.metadata["title"], self.metadata["trackno"],)

    def format(self, format):
        artist  = unicode(self.metadata["artist"]).replace("/", "-")
        
        album   = unicode(self.metadata["album"]).replace("/", "-")
        title   = unicode(self.metadata["title"]).replace("/", "-")

        trackno = self.metadata["trackno"]
        trackof = self.metadata["trackof"]
        diskno  = self.metadata["diskno" ]
        diskof  = self.metadata["diskof" ]
    
        result = format
        result = result.replace("%artist", artist)
        result = result.replace("%album",  album )
        result = result.replace("%title",  title )

        result = result.replace("%trackno2", repr(trackno).rjust(2, "0") )
        result = result.replace("%trackof2", repr(trackno).rjust(2, "0") )
    
        result = result.replace("%diskno2",  repr(diskno).rjust(2, "0") )
        result = result.replace("%diskof2",  repr(diskno).rjust(2, "0") )

        result = result.replace("%ext"    ,  self.extension )
    
        return result


    def parse_no(self, string):
        try:
            no = int( string.split("/")[0] )
        except:
            no = None
        return no

    def parse_of(self, string):
        try:
            of = int( string.split("/")[1] )
        except:
            of = None
        return of

    def __repr__(self):
        return "MediaFile: %s" % (self.path,)
            

class MP3File(MediaFile):
    def __init__(self, path):
        super(MP3File, self).__init__(path)
        self.extension = "mp3"

        media = EasyMP3(path)
        
        self.bitrate = media.info.bitrate
        self.length  = media.info.length

        self.metadata = {
            "artist": media.get( "artist", default=[None,] )[0],
            "album":  media.get( "album",  default=[None,] )[0],
            "title":  media.get( "title",  default=[None,] )[0],

            "genre":  media.get( "genre",  default=[None,] )[0],
            
            "trackno":  self.parse_no( media.get("tracknumber", default=["",])[0] ),
            "trackof":  self.parse_of( media.get("tracknumber", default=["",])[0] ),
            
            "diskno":  self.parse_no( media.get("disknumber", default=["",])[0] ),
            "diskof":  self.parse_of( media.get("disknumber", default=["",])[0] ),
        }

    def __repr__(self):
        return "MP3File: %s" % (self.path,)

class FLACFile(MediaFile):
    def __init__(self, path):
        super(FLACFile, self).__init__(path)
        self.extension = "flac"

        media = FLAC(path)

        self.bitrate = media.info.total_samples * media.info.bits_per_sample / media.info.length
        self.length  = media.info.length

        self.metadata = {
            "artist": media.get( "artist", default=[None,] )[0],
            "album":  media.get( "album",  default=[None,] )[0],
            "title":  media.get( "title",  default=[None,] )[0],

            "genre":  media.get( "genre",  default=[None,] )[0],
            
            "trackno":  self.parse_no( media.get("tracknumber", default=["",])[0] ),
            "trackof":  self.parse_of( media.get("tracknumber", default=["",])[0] ),
            
            "diskno":  self.parse_no( media.get("disknumber", default=["",])[0] ),
            "diskof":  self.parse_of( media.get("disknumber", default=["",])[0] ),
        }



    def __repr__(self):
        return "FLACFile: %s" % (self.path,)

class MP4File(MediaFile):
    def __init__(self, path):
        super(MP4File, self).__init__(path)
        self.extension = "mp4"

        media = MP4(path)

        self.bitrate = media.info.bitrate
        self.length  = media.info.length
        

        nos = [(None,None),]
        self.metadata = {
            "artist": media.tags.get( "\xa9ART", default=[None,] )[0],
            "album":  media.tags.get( "\xa9alb",  default=[None,] )[0],
            "title":  media.get( "\xa9nam",  default=[None,] )[0],

            "genre":  media.get( "\xa9gen",  default=[None,] )[0],
            
            "trackno":  media.get("trkn", default=nos)[0][0],
            "trackof":  media.get("trkn", default=nos)[0][1],
            
            "diskno":  media.get("disk", default=nos)[0][0],
            "diskof":  media.get("disk", default=nos)[0][1],
        }



    def __repr__(self):
        return "MP4File: %s" % (self.path,)
