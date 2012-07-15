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

#Credit to divingmule for a portion of the stream location and playback code.
#http://code.google.com/p/divingmules-repo/downloads/list



import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from xml.dom.minidom import parse, parseString

try:
    import json
except:
    import simplejson as json
    
LISTLIVEVIDEOS = 1
PLAYVIDEO = 2
LISTFAVORITES = 3
LISTGAMES = 4
SHOWSTARCRAFT = 5
SHOWDIABLO = 6
SHOWLOL = 7
SHOWDOTA = 8
SHOWCOUNTER = 9
SHOWWOW = 10
SEARCHLIVE = 11
SHOWGAME = 12

SHOWSTARCRAFT = 5
SHOWDIABLO = 6
SHOWLOL = 7
SHOWDOTA = 8
SHOWCOUNTER = 9
SHOWWOW = 10

LIVE = 1
VOD = 2
OFFLINE = 3
CHECKLIVE = 4
NAMELABEL = 5
OTHER = 6

OWN3D=1
TWITCH=2

QUALITY = ['live','480p','360p','240p']

CDN1= 'rtmp://fml.2010.edgecastcdn.net:1935/202010'
CDN2= 'rtmp://owned.fc.llnwd.net/owned'
OWNSWF='http://static.ec.own3d.tv/player/Own3dPlayerV2_86.swf'

#Collects stream ID, stream name, game name, stream cover, and stream thumbnail
OWNLIVEREGEX='<img class="VIDEOS-thumbnail small_tn_img originalTN".+rel="(\d+)"\ssrc="(.+)"\salt="(.+)".+\s.+src="(.+)"\salt='      
#<a class='thumb' href='/tsm_theoddone'>
#<img alt="" class="cap" src="http://static-cdn.jtvnw.net/previews/live_user_tsm_theoddone-320x240.jpg" />
#</a>
#<div class='meta'>
#<a href="/directory/League of Legends" class="boxart" title="League of Legends"><img onerror="this.parentNode.removeChild(this);" src="http://static-cdn.jtvnw.net/ttv-boxart/League of Legends.jpg" /></a>
#<p class='title'><a href="/tsm_theoddone">TSM TheOddOne getting carried (while carrying Dyrus) power hour stream!</a></p>

STREAMIDREGEX="<a class='thumb' href='/(.+)'>"

LIVEREGEX="<a class='thumb' href='/(.+)'>\s<img alt=\"\" class=\"cap\" src=\"(.+)\" />(\s\s.+\s.+\s.+\s<p class='title'><a href=\".+\">(.+)</a></p>"
FINALLIVEREGEX="<div class='video  clearfix' data-href='/(.+)'>"

SWF="http://www.justin.tv/widgets/live_embed_player.swf?channel="

LIVEURL="http://www.twitch.tv/directory/all"

STARCRAFTURL="http://www.twitch.tv/directory/StarCraft%20II:%20Wings%20of%20Liberty"
DIABLOURL="http://www.twitch.tv/directory/Diablo%20III"
LOLURL="http://www.twitch.tv/directory/League%20of%20Legends"
DOTAURL="http://www.twitch.tv/directory/Dota%202"
COUNTERURL="http://www.twitch.tv/directory/Counter-Strike:%20Source"
WOWURL="http://www.twitch.tv/directory/World%20of%20Warcraft:%20Cataclysm"

STARCRAFTTHUMB="http://static-cdn.jtvnw.net/ttv-boxart/StarCraft%20II:%20Wings%20of%20Liberty.jpg"
LOLTHUMB="http://static-cdn.jtvnw.net/ttv-boxart/League%20of%20Legends.jpg"
DIABLOTHUMB="http://static-cdn.jtvnw.net/ttv-boxart/Diablo%20III.jpg"
DOTATHUMB="http://static-cdn.jtvnw.net/ttv-boxart/Dota%202.jpg"
COUNTERTHUMB="http://static-cdn.jtvnw.net/ttv-boxart/Counter-Strike:%20Source.jpg"
WOWTHUMB="http://static-cdn.jtvnw.net/ttv-boxart/World%20of%20Warcraft:%20Cataclysm.jpg"





OWNLIVEURL="http://www.own3d.tv/live"

OWNSTARCRAFTURL="http://www.own3d.tv/game/StarCraft+II"
OWNDIABLOURL="http://www.own3d.tv/game/Diablo+3"
OWNLOLURL="http://www.own3d.tv/game/League+of+Legends"
OWNDOTAURL="http://www.own3d.tv/game/Dota+2"
OWNCOUNTERURL="http://www.own3d.tv/game/Counter-Strike"
OWNWOWURL="http://www.own3d.tv/game/World+of+Warcraft"

class Channel:
    def __init__(self,streamID,type):
        self.streamID=streamID
        self.type=type
       
        self.activeCDN=0
        self.activeStream=0
        self.rtmpBase=None
        self.rtmpPath=None
        
        self.playbackURL=None
        self.rtmpURL=None
        self.pageURL=None
        self.swfURL=None
        self.playPath=None
        self.live=None
        self.verify=None
        
        self.channel=None
        self.title=None
        self.user=None
        self.game=None
        self.thumbnail=None
        self.cdnList=[]
        self.streamList=[]
    
    def playStream(self):
        listItem = xbmcgui.ListItem("Stream",thumbnailImage=self.thumbnail)
        listItem.setInfo( type="Video", infoLabels={"Title": self.title, "Plot": self.user} )
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(self.playbackURL,listItem)
        
    def loadInfo(self):
        #Load and parse own3d info page
        print "Loading Stream Information."
        infoURL="http://www.own3d.tv/livecfg/"+str(self.streamID)
        try:
            infoPage=urllib.urlopen(infoURL)
        except:
            xbmc.executebuiltin("XBMC.Notification(own3D.tv,Error Loading Stream,5000,"+ICON+")")
            print "Error loading stream. Check your internet connection"
            return 1
        self.infoDOM=parse(infoPage)
        self.channel=self.infoDOM.getElementsByTagName("channel")[0]
        

        #Parse Channel title,user,game,etc
        self.title=self.channel.attributes["name"].value
        self.user=self.channel.attributes["owner"].value
        self.game=self.channel.attributes["description"].value
        
        if owncheckLive(self.streamID) != LIVE:
        #if self.infoDOM.getElementsByTagName("thumb")[0].firstChild == None:
            #print ICON
            print "Stream is not live."
            xbmc.executebuiltin("XBMC.Notification(own3D.tv,Error Loading Stream,5000,"+ICON+")")
            return 1
        try:
            self.thumbnail=str(self.infoDOM.getElementsByTagName("thumb")[0].firstChild.data)
        except:
            print "Error Loading thumbnail."
        #Think this may be wrong. Does this just fail to provide a thumbnail if there's no static thumbnail?
        if '?' in self.thumbnail:
            self.thumbnail="icon.png"
        #print "Thumbnail: "+self.thumbnail
        
        
        findCDN=None
        #Load CDN's and Streams
        if settings.getSetting('preferredCDN') == 'true':
            print "Trying CDN1 first."
            findCDN='${cdn1}'
        else:
            print "Trying CDN2 first."
            findCDN='${cdn2}'
            
        self.cdnList=self.channel.getElementsByTagName("item")
        cdn=len(self.cdnList)
        i=0
        self.rtmpBase=None
        while i<cdn:
            self.rtmpBase=self.cdnList[i].attributes["base"].value
            if self.rtmpBase == findCDN:
                self.activeCDN=i
                break
            i=i+1
            
        if self.rtmpBase==None:
            i=0
            print "Preferred CDN not found."
            if settings.getSetting('preferredCDN') == 'true':
                findCDN='${cdn2}'
            else:
                findCDN='${cdn1}'
            while i<cdn:
                self.rtmpBase=self.cdnList[i].attributes["base"].value
                if self.rtmpBase == findCDN:
                    self.activeCDN=i
                    break
            i=i+1
            
        if(self.rtmpBase == "${cdn1}"):
            print "Using CDN1"
            self.rtmpBase = CDN1
        elif(self.rtmpBase == "${cdn2}"):
            print "Using CDN2"
            self.rtmpBase = CDN2
        else:
            print "CDN Not Recognized! Aborting."
            xbmc.executebuiltin("XBMC.Notification(own3D.tv,CDN Not Recognized!,5000,"+ICON+")")
            return 1

        self.streamList=self.cdnList[self.activeCDN].getElementsByTagName("stream")
        
        #Set Quality
        self.activeStream=int(settings.getSetting('quality'))
        print "Active Stream: " +str(self.activeStream)
        print "Available Streams: "+str(len(self.streamList))
        availableStream=(len(self.streamList)-1)
        if self.activeStream > availableStream :
            self.activeStream=availableStream
        print self.activeStream
        self.rtmpPath=self.streamList[self.activeStream].attributes["name"].value
        
        #Only the right side is useful if there's a question mark separator in the stream url.
        if '?' in self.rtmpPath:
            self.rtmpURL=self.rtmpBase+'?'+self.rtmpPath.split('?',1)[1]
        else:
            self.rtmpURL=self.rtmpBase+'?'+self.rtmpPath
        
        #pageURL
        self.pageURL=self.channel.attributes["ownerLink"].value
        
        #playPath
        self.playPath=self.rtmpPath
        
        #Live and verify
        self.live='True'
        self.verify='True'
        
        self.playbackURL=self.rtmpURL+" pageUrl="+self.pageURL+" Playpath="+self.playPath+" swfUrl="+OWNSWF+" swfVfy="+self.verify+" Live="+self.live
        
        #Parse Channel title,user,game,etc
        self.title=self.channel.attributes["name"].value+" | "+self.streamList[self.activeStream].attributes["label"].value
        self.user=self.channel.attributes["owner"].value
        self.game=self.channel.attributes["description"].value
        
        print "Loading Stream."
        print "--------------------------------------------"
        print "Title: "+self.title
        print "User: "+self.user
        print "Game: "+self.game
        print "Playback URL: "+self.playbackURL
        
        
        
        
        
def get_params():
    #Generic XBMC function to parse an arguement url given to the plugin.
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


def owncheckLive(streamID):
    #Checks if the streamID is live via the own3d api.
    print "Checking if "+str(streamID)+" is live."
    liveURL="http://api.own3d.tv/liveCheck.php?live_id="+str(streamID)
    try:
        livePage=urllib.urlopen(liveURL)
    except:
        print "Error checking if "+str(streamID)+" is live."
        return OTHER
    liveDOM=parse(livePage)
    live=liveDOM.getElementsByTagName("liveEvent")[0]
    print "Checking if Live."
    print live.getElementsByTagName("isLive")[0].firstChild.data
    if live.getElementsByTagName("isLive")[0].firstChild.data == "true":
        return LIVE
    else:
        return OFFLINE
    
def searchLive(searchString):
    #Performs a search of live videos.
    print "Searching: "+"http://api.justin.tv/api/stream/search/"+searchString.replace(" ","+")+".json"
    url="http://api.justin.tv/api/stream/search/"+searchString.replace(" ","+")+".json"
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
               'Referer' : 'http://api.justin.tv/'}
    #req = urllib2.Request(url, None, headers)
    #response = urllib2.urlopen(req)
    data = json.loads(get_request(url,headers))
    streams= len(data)
    print str(streams) +" streams found."
    i=0
    results=[]
    while i < streams:
        print "Loading stream "+str(i)
        try:
            title = data[i]['title']
        except:
            title=""
        name = data[i]['channel']['login']
        thumbnail = data[i]['channel']['screen_cap_url_large']
        results.append([name,thumbnail,title,name])
        i=i+1
    #pageContents = response.read()
    #searchDom=parseString(pageContents)
    #streams = searchDom.getElementsByTagName("streams")
    #streams = streams[0].getElementsByTagName("stream")
    #numStreams=len(streams)
    #i=0
    #results=[]
    #while i< numStreams:
    #    title= streams[i].getElementsByTagName("title")[0].contains
    #    print title
    #    channel=streams[i].getElementsByTagName("channel")[0]
    #    name = channel.getElementsByTagName("login").firstchild.data
    #    thumbnail = channel.getElementsByTagName("screen_cap_url_large").firstchild.data
    #    results.append([name,thumbnail,title,name])
    #    i=i+1
        
    displayVideos(results, NAMELABEL)
    #http://api.justin.tv/api/stream/search/query.format
def getViewers(streamID):
    #Checks if the streamID is live via the own3d api.
    print "Checking number of viewers on: "+str(streamID)
    liveURL="http://api.own3d.tv/liveCheck.php?live_id="+str(streamID)
    try:
        livePage=urllib.urlopen(liveURL)
    except:
        print "Error checking  "+str(streamID)+" viewrs."
        return OTHER
    liveDOM=parse(livePage)
    live=liveDOM.getElementsByTagName("liveEvent")[0]
    print str(live.getElementsByTagName("liveViewers")[0].firstChild.data)+" viewers."
    return int(live.getElementsByTagName("liveViewers")[0].firstChild.data)
    
def ownloadPage(url):
    #Opens a URL and returns the raw content of the page.
    page=urllib.urlopen(url)
    pageContents=page.read()
    page.close()
    return pageContents    
def ownloadLive(url):
    #Scrapes a URL for live videos using the defined regular expression at the head of the source code.
    try:
        pageContents=ownloadPage(url)
    except:
        print "Error loading page. Are you connected to the internet?"
        xbmc.executebuiltin("XBMC.Notification(own3D.tv,Error Locating Streams,2000,"+ICON+")")
        return None
    a=re.compile(OWNLIVEREGEX)
    match=a.findall(pageContents)
    print "Found these streams: "
    print match
    match2=[]
    checkViewers=True
    if checkViewers == True:
        for streamID, thumbnail, name, preview in match:
            match2.append([streamID,thumbnail,name,name,getViewers(streamID),OWN3D])
    print "Added viewers"
    print match2
    return match2
        
def loadLive(url):
    #Scrapes a URL for live videos using the defined regular expression at the head of the source code.
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
               'Referer' : 'http://www.justin.tv/'}
    req = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(req)
    pageContents = response.read()

    a=re.compile(STREAMIDREGEX)
    match=a.findall(pageContents)
    
    streams=[]
    #find thumbnails, title, etc
    for streamID in match:
        name = None
        title = None
        nameRegEx="<a href=\"/"+streamID+"/videos\">(.+)</a>"
        a=re.compile(nameRegEx)
        name=a.findall(pageContents)
        titleRegEx="<p class='title'><a href=\"/"+streamID+"\">(.+)\s?</a></p>"
        a=re.compile(titleRegEx)
        title=a.findall(pageContents)
        viewersRegEx="<span class='channel_count'>(.+)</span>\s.+\s<a href=\"/"+streamID
        a=re.compile(viewersRegEx)
        viewers=a.findall(pageContents)[0]
        viewers=int(viewers.replace(",",""))
        print "Viewers: "+str(viewers)
#        <span class='channel_count'>9,453</span>
#        viewers on
#        <a href="/onemoregametv/videos">OneMoreGameTV</a>
        if len(title)==0:
            #print "Broken title found...Fixing it."
            titleRegEx="<p class='title'><a href=\"/"+streamID+"\">(.+)\s(.+)</a></p>"
            a=re.compile(titleRegEx)
            titleFix=a.findall(pageContents)
            #print titleFix
            #print len(titleFix)
            if len(titleFix)>0:
                for title1, title2 in titleFix:
                    title=[title1+title2]
                    #print "Fixed Title."

                    
        #print title
        #print name
        if len(name)>0:
            if len(title)>0:      
                streams.append([streamID,"http://static-cdn.jtvnw.net/previews/live_user_"+streamID+"-320x240.jpg",title[0],name[0],viewers,TWITCH])
            else:
                streams.append([streamID,"http://static-cdn.jtvnw.net/previews/live_user_"+streamID+"-320x240.jpg",'',name[0],viewers,TWITCH])
        else:
            print "Error scraping stream info."
            
            
            
    
    print "Found these streams: "
    print match
    print "Found stream info: "
    print streams
    return streams   

def loadMenu():
    addMenuItem("Live Streams",LISTLIVEVIDEOS,'')
    addMenuItem("Games",LISTGAMES,'')
    addMenuItem("Search Live",SEARCHLIVE,'')
    addMenuItem("Favorites",LISTFAVORITES,'')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def addMenuItem(name,mode,iconimage,game=None):
    #Add a generic menu item. doesn't link to content, so only mode is required in URL.
    if game == None:
        url=sys.argv[0]+"?mode="+str(mode)
    else:
        print "Listing gameID: "+str(game)
        url=sys.argv[0]+"?mode="+str(SHOWGAME)+"&gameURL="+urllib.quote_plus(str(game))
        
    ok=True
    listItem=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listItem.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listItem,True)
    return ok

def addVideoLink(streamID, thumbnail, name, title, videoType,site):
    #set link click to begin playback.
    url=sys.argv[0]+"?mode="+urllib.quote_plus(str(PLAYVIDEO))+"&streamID="+urllib.quote_plus(str(streamID))+"&site="+urllib.quote_plus(str(site))+"&name="+urllib.quote_plus(name)+"&title="+title+"&videoType="+urllib.quote_plus(str(videoType))
    
    #do we need to test if source is live?
    if videoType == CHECKLIVE:
        videoType = checkLive(streamID)
    

    #Generate stream tag based on videoType
    if videoType == LIVE:
        listItem=xbmcgui.ListItem("[Live] "+title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
    elif videoType == OFFLINE:
        listItem=xbmcgui.ListItem("[Offline] "+title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
    elif videoType == NAMELABEL:
        videoString="["+name+"]   "
        #i=0
        #length=20-len(videoString)
        #while i<length:
        #    videoString+=" "
        #    i=i+1;  
        videoString+=title
        listItem=xbmcgui.ListItem(videoString, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)        
    else:
        listItem=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
         
    #Generate an "Add to favorites" context menu item. ("Remove from favorites" if viewing favorites list.)
    if mode == LISTFAVORITES:
        title = ("Remove "+name+" from favorites." )                
        browse =  "XBMC.Container.Refresh("+str(sys.argv[0])+str(sys.argv[2])+"&favorite=2"+"&favStreamID="+urllib.quote_plus(str(streamID))+"&favName="+urllib.quote_plus(str(name))+"&favThumbnail="+urllib.quote_plus(str(thumbnail))+"&favPreview="+urllib.quote_plus(str(preview))+")"
    else:
        title = ("Add "+name+" to favorites." )                
        browse =  "XBMC.Container.Refresh("+str(sys.argv[0])+str(sys.argv[2])+"&favorite=1"+"&favStreamID="+urllib.quote_plus(str(streamID))+"&favName="+urllib.quote_plus(str(name))+"&favThumbnail="+urllib.quote_plus(str(thumbnail))+"&favPreview="+urllib.quote_plus(str(preview))+")"    
    cm=[]
    cm.append((title, browse  ))
    listItem.addContextMenuItems( cm, replaceItems=False )
    ok=xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listItem)
    
def displayVideos(videos, videoType):
    #Generates a menu of video links from a scraped list of live videos
    if videos != None:
        if len(videos[0]) == 6:
            videos.sort(key=lambda x: x[4],reverse=True)
            for streamID, thumbnail, title, name, viewers, site in videos:
                print "Viewers: "+str(viewers)
                addVideoLink(streamID,thumbnail,name,title,videoType,site)
        else:
            for streamID, thumbnail, title, name, site in videos:
                addVideoLink(streamID,thumbnail,name,title,videoType,site)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
 
def loadGames():
    addMenuItem("Starcraft 2",SHOWGAME,STARCRAFTTHUMB,STARCRAFTURL)
    addMenuItem("Diablo III",SHOWGAME,DIABLOTHUMB,DIABLOURL)
    addMenuItem("League of Legends",SHOWGAME,LOLTHUMB,LOLURL)
    addMenuItem("Dota 2",SHOWGAME,DOTATHUMB,DOTAURL)
    addMenuItem("Counter-Strike",SHOWGAME,COUNTERTHUMB,COUNTERURL)
    addMenuItem("World of Warcraft",SHOWGAME,WOWTHUMB,WOWURL)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
     
def get_request(url, headers=None):
        try:
            if headers is None:
                headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                           'Referer' : 'http://www.justin.tv/'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            errorStr = str(e.read())
            if debug == 'true':
                print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                if debug == 'true':
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                if str(e.code) == '403':
                    if 'archive' in url:
                        xbmc.executebuiltin("XBMC.Notification(TwitchTV,No archives found for "+name+",5000,"+ICON+")")
                if debug == 'true':
                    print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification(TwitchTV,HTTP ERROR: "+str(e.code)+",5000,"+ICON+")")

      
def getSwfUrl(channel_name):
        """Helper method to grab the swf url, resolving HTTP 301/302 along the way"""
        base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.justin.tv/'+channel_name}
        req = urllib2.Request(base_url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()

  
def playLive(name,title, play=False, password=None,):
        swf_url = getSwfUrl(name)
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : swf_url}

        data = []
        qualitySetting=int(settings.getSetting('quality'))
        quality = QUALITY[qualitySetting]
        
        while data == []:
            print "Trying quality: "+quality
            
            url = 'http://usher.justin.tv/find/'+name+'.json?type='+quality
            print "URL: "+url
            data = json.loads(get_request(url,headers))  
            print qualitySetting
            print len(QUALITY)-1
            if data != []:
                print "Data Found!"
                break
            elif int(qualitySetting)<int(len(QUALITY)-1):
                print "No data found. Lowering quality setting."
                qualitySetting=qualitySetting+1
                quality=QUALITY[qualitySetting]
            else:
                print "Error locating specified quality. Searching for live stream."
                quality="live"
                url = 'http://usher.justin.tv/find/'+name+'.json?type='+quality
 
                data = json.loads(get_request(url,headers))
                if data == []:
                    xbmc.executebuiltin("XBMC.Notification(TwitchTV,Live Data Not Found,2000,"+ICON+")")
                    return
                      
        if data == []:
            if debug == 'true':
                print '---- No Data, Live? ----'
            xbmc.executebuiltin("XBMC.Notification(TwitchTV,Live Data Not Found,2000,"+ICON+")")
            return
        elif data[0]['needed_info'] == 'private':
            password = getPassword()
            if password is None:
                return
            url += '&private_code='+password
            data = json.loads(get_request(url,headers))
        try:
            token = ' jtv='+data[0]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        except:
            if debug == 'true':
                print '---- User Token Error ----'
            xbmc.executebuiltin("XBMC.Notification(Jtv,User Token Error ,5000,"+ICON+")")
            return
        rtmp = data[0]['connect']+'/'+data[0]['play']
        swf = ' swfUrl=%s swfVfy=1 live=1' % swf_url
        Pageurl = ' Pageurl=http://www.justin.tv/'+name
        url = rtmp+token+swf+Pageurl
        if play == True:
            info = xbmcgui.ListItem(title+" | "+QUALITY[qualitySetting])
            playlist = xbmc.PlayList(1)
            playlist.clear()
            playlist.add(url, info)
            xbmc.executebuiltin('playlist.playoffset(video,0)')
        else:
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
def checkLive(streamID):
    swf_url = getSwfUrl(streamID)
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
               'Referer' : swf_url}
    url = 'http://usher.justin.tv/find/'+streamID+'.json?type=live&group='
    data = json.loads(get_request(url,headers))
    if data == []:
        return OFFLINE
    else:
        return LIVE
    
def loadFavorites(favorites):
    if settings.getSetting('checkLive') =="true":
        displayVideos(favorites,CHECKLIVE)
    else:
        displayVideos(favorites,OTHER)
        
      
#Plugin Start       
        
#Initialize variables
mode=None
streamID=None
streamIDAdd=None
nameAdd=None
thumbnailAdd=None
title=""
activeStream=None
videoType=None
thumbnail=None
name=None
game=None
favorite=None
preview=None
favorites=[]
debug=False
site=None

#Load url paramaters, settings, and plugin icon.
parameters=get_params()
settings = xbmcaddon.Addon("plugin.video.engineeredchaos.esportsviewer")
ICON = xbmc.translatePath( os.path.join( settings.getAddonInfo('path'), 'icon.png' ) )

    
#try to extract any applicable parameters.
try:
    favorite=int(parameters["favorite"])
except:
    pass
try:
    site=int(parameters["site"])
except:
    pass
try:
    title=parameters["title"]
except:
    pass
try:
    mode=int(parameters["mode"])
except:
    pass
try:
    streamID=urllib.unquote_plus(parameters["streamID"])
except:
    pass
try:
    videoType=int(parameters["type"])
except:
    pass
try:
    name=parameters["name"]
except:
    pass
try:
    thumbnail=parameters["thumbnail"]
except:
    pass
try:
    preview=parameters["preview"]
except:
    pass
try:
    streamIDAdd=parameters["favStreamID"]
except:
    pass
try:
    nameAdd=urllib.unquote_plus(parameters["favName"])
except:
    pass
try:
    thumbnailAdd=urllib.unquote_plus(parameters["favThumbnail"])
except:
    pass
try:
    previewAdd=urllib.unquote_plus(parameters["favPreview"])
except:
    pass
try:
    game=urllib.unquote_plus(parameters["gameURL"])
except:
    pass

#Load favorites from the settings string.
tempFavorites=[]
favoriteSplit3=[]

favoriteString= settings.getSetting("favorites")
favoriteSplit= favoriteString.split("&&&")

for favoriteSplit2 in favoriteSplit:
    favoriteSplit3.append(favoriteSplit2.split("###"))

for favoriteItem in favoriteSplit3:
    if len(favoriteItem)==4:
        tempFavorites.append(favoriteItem)
for streamIDTemp,thumbnailTemp,nameTemp,previewTemp in tempFavorites:
    favorites.append([streamIDTemp,thumbnailTemp,nameTemp,nameTemp])

#Favorite addition requested
if favorite == 1:
    print "Adding "+nameAdd+" to favorites."
    alreadyAdded=0
    favoriteString="";

    for streamIDTemp,thumbnailTemp,nameTemp,previewTemp in favorites:
        if nameAdd in nameTemp:
            alreadyAdded=1
        favoriteString=favoriteString+str(streamIDTemp)+"###"+str(thumbnailTemp)+"###"+str(nameTemp)+"###"+str(previewTemp)+"&&&"
        
    if alreadyAdded==0:
        favoriteString=favoriteString+str(streamIDAdd)+"###"+str(thumbnailAdd)+"###"+str(nameAdd)+"###"+str(previewAdd)
        favorites.append([streamIDAdd,thumbnailAdd,nameAdd,previewAdd])
    else:
        print nameAdd+" is already in favorites."
    settings.setSetting("favorites",favoriteString)
    print "Saving Favorites."

#Favorite removal requested.
if favorite ==2:
    print "Removing "+nameAdd+" from favorites."
    newFavorites=[]
    favoriteString="";

    for streamIDTemp,thumbnailTemp,nameTemp,previewTemp in favorites:
        if nameTemp in nameAdd:
            print "Match Found...Removing."
        else:
            newFavorites.append([streamIDTemp,thumbnailTemp,nameTemp,previewTemp])
            favoriteString=favoriteString+str(streamIDTemp)+"###"+str(thumbnailTemp)+"###"+str(nameTemp)+"###"+str(previewTemp)+"&&&"
    print "Saving Favorites."
    settings.setSetting("favorites",favoriteString)
    favorites=newFavorites
    
    
    
#Plugin States

print "Mode: "+str(mode)
if mode == None:
    loadMenu()
    
elif mode == LISTLIVEVIDEOS:
    videos=loadLive(LIVEURL)
    videos2=ownloadLive(OWNLIVEURL)
    for video in videos2:
        videos.append(video)
    displayVideos(videos,NAMELABEL)
    
elif mode == LISTGAMES:
    loadGames()
    
elif mode == LISTFAVORITES:
    loadFavorites(favorites)

elif mode == SHOWGAME:
    print "Showing GameURL: "+str(game)
    displayVideos(loadLive(game),NAMELABEL)

elif mode == SEARCHLIVE:
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        searchLive(keyboard.getText())
        
elif mode == PLAYVIDEO:
    if streamID != None:
        print "Attempting to play StreamID: "+str(streamID)
        if site == TWITCH:
            print "Playing from twitch.tv"
            playLive(streamID,title,True)
        elif site == OWN3D:
            print "Playing from own3d.tv"
            activeStream=Channel(streamID,videoType)
            if activeStream.loadInfo() != 1:
                print "Playing Stream."
                activeStream.playStream()
            else:
                print "Error loading stream info. Aborting playback."
        #activeStream=Channel(streamID,videoType)
        #if activeStream.loadInfo() != 1:
        #    print "Playing Stream."
        #    activeStream.playStream()
        #else:
        #    print "Error loading stream info. Aborting playback."
    else:
        print "No streamID to play."
    
