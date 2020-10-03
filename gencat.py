import pyimgur
import re
import web
import time

CLIENT_ID = 'put_imgur_api_id_here'
try:
    import secret
    CLIENT_ID = secret.CLIENT_ID
except:
    print("Put CLIENT_ID='whatever' in a file called secret.py if you like")

urls=('/(.*)','pagegen')

app = web.application(urls,globals())

gds={}


class pagegen:
    def __init__(self,cid=CLIENT_ID):
        global gds
        if not 'im' in gds:
            gds['im']=pyimgur.Imgur(cid)
        self.im=gds['im']
        if not 'top' in gds:
            gds['top']=None
        if not 'ctop' in gds:
            gds['ctop']=[]
        if not 'mv' in gds:
            gds['mv']=None
        if not 'cmv' in gds:
            gds['cmv']=[]
        if not 'mv' in gds:
            gds['mv']=None
        if not 'toptime' in gds:
            gds['toptime']=0
        if not 'mvtime' in gds:
            gds['mvtime']=0
        if not 'tags' in gds:
            gds['tags']={}
        self.blacklist=['trump','biden','bleach','skeleton','hydroxy','current','vote','spoopy','skellingtons','pray','covid','shitpost','politic']
        
    def GET(self,url):
        r=re.compile("/([a-zA-Z0-9]+)(/[a-zA-Z0-9]*)?(.*)?")
        m=r.search('/'+url)
        if m is not None:
            mg1=m.group(1) if m.group(1) is not None else ""
            mg2=m.group(2) if m.group(2) is not None else ""
            if 'gallery' in mg1:
                return self.gen_gallery_page(mg2.strip('/'))
            elif 'mostv' in mg1:
                return self.gen_browse_page(mg2.strip('/'),gtype='m')
            elif 'top' in mg1:
                return self.gen_browse_page(mg2.strip('/'),gtype='t')
            elif 'tags' in mg1:
                return str(gds['tags'])
            elif 'a' is mg1:
                return self.gen_album_page(mg2.strip('/'))
            elif mg2 is "":
                return self.gen_image_page(mg1)
            else:
                print("unknown page",mg1,mg2)
                return self.gen_empty_page("Unknown page")
    
    def gen_page_header(self,title=""):
        return """
    <html>
        <head>
        <meta charset="UTF-8" />
        <title>"""+title.strip("<&>")+"""</title></head>
        <body bgcolor="#000000" text="#FFFFFF">
    """
    def gen_page_footer(self):
        return """
        </body>
    </html>
    """
    def gen_image(self,image):
        if image is None:
            return ""
        link=image.link
        if ".mp4" in link or ".webm" in link:
            #this is a video - deal with that somehow
            return """
            <p>
                <video muted="true" playsinline="true" poster="%s" src="%s" loop="true" disablePictureInPicture="true" controls="true" />
                <div class="video-desc">%s</div>
            </p>
            """%(str(image.link_huge_thumbnail),str(image.link),str(image.description if image.description else ""))
        else:
            return """
            <p>
                <a href="%s">
                    <img src="%s"/>
                </a>
                <div class="img-desc">%s</div>
            </p>
            """%(str(image.link),str(image.link_huge_thumbnail),str(image.description if image.description else ""))
    
    def gen_album_page(self,aid):
        print("getting album", aid)
        album=self.im.get_album(aid)
        if album is None:
            return self.gen_empty_page()
        page=self.gen_page_header("r.om:"+(album.title if album.title else aid))
        page+="<h1>%s</h1>\n"%(album.title) if album.title else ""
        for i in album.images:
            page+=self.gen_image(i)
        return page+self.gen_page_footer()
    
    def gen_gallery_page(self,aid,index=None,browse=None):
        print("getting gallery item", aid)
        navbar=""
        if index is not None and index>0 and ('mostv' in browse or 'top' in browse):
            navbar+="""
            <a class="prev" href="%s" > Previous </a>
            """%('/'+browse+'/'+str(index-1))
        navbar+="""
            <a class="self-link" href="%s"> Self </a>
            """%('/gallery/'+aid)
        navbar+="""
            <a class="self-link" href="%s"> <small>imgur</small> </a>
            """%('https://imgur.com/gallery/'+aid)
        if index is not None and index>=0 and ('mostv' in browse or 'top' in browse):
            navbar+="""
            <a class="prev" href="%s" > Next </a>
            """%('/'+browse+'/'+str(index+1))
        navbar+='<br/>'
        album=None
        image=None
        try:
            album=self.im.get_gallery_album(aid)
        except:
            try:
                image=self.im.get_gallery_image(aid)
            except:
                pass
        if album is None:
            if image is None:
                return self.gen_empty_page()
            else:
                page=self.gen_page_header("r.om:"+(image.title if image.title else aid))
                page+=navbar
                page+=("<h1>%s</h1>\n"%(image.title)) if image.title else ""
                page+=self.gen_image(image)
                return page+self.gen_page_footer()
        page=self.gen_page_header("r.om:"+(album.title if album.title else aid))
        page+=navbar
        page+=("<h1>%s</h1>\n"%(album.title)) if album.title else ""
        for i in album.images:
            page+=self.gen_image(i)
        return page+self.gen_page_footer()
    
    def filter(self,item):
        banned=False
        if item.tags is None:
            try:
                item.tags=self.im._send_request(self.im._base_url+'/3/gallery/%s/tags'%(item.id,))
            except:
                print("Failed to get tags")
                banned=True #abundance of caution
        for tag in item.tags:
            if not tag['display_name'] in gds['tags']:
                gds['tags'][tag['display_name']]=1
            else:
                gds['tags'][tag['display_name']]=gds['tags'][tag['display_name']]+1
            if not banned:
                for b in self.blacklist:
                    if b in tag['display_name']:
                        print("banned due to", b)
                        banned=True
                        break
        if not banned:
            return item
        return None

    def gen_browse_page(self,index,gtype='m'):
        ggal=None
        gcgal=None
        if gtype is 'm':
            if gds['mv'] is None or time.time()-gds['mvtime']>3600:
                print("fetching mostv")
                gds['mv']=self.im.get_gallery(section='hot',sort='time',window='day',limit=400)
                if gds['mv'] is not None:
                    for i in gds['mv']:
                        i.tags=None
                    gds['cmv']=[]
                    gds['mvind']=0
                gds['mvtime']=time.time()
            ggal=gds['mv']
        if gtype is 't':
            if gds['top'] is None or time.time()-gds['toptime']>3600:
                print("fetching top")
                gds['top']=self.im.get_gallery(section='top',sort='time',window='day',limit=400)
                if gds['top'] is not None:
                    for i in gds['top']:
                        i.tags=None
                    gds['ctop']=[]
                    gds['topind']=0
                gds['toptime']=time.time()
            ggal=gds['top']
        if ggal is None:
            return self.gen_empty_page("No such thing")
        i=0
        if index.isnumeric() and int(index)>=len(ggal):
            self.gen_empty_page("That's all for today")
        elif gtype is 'm':
            i=0
            if index.isnumeric() and int(index)<len(ggal):
                i=int(index)
            while len(gds['cmv'])<=i and gds['mvind']<len(ggal):
                filtered=self.filter(ggal[gds['mvind']])
                gds['mvind']+=1
                if filtered:
                    gds['cmv'].append(filtered)
            if len(gds['cmv'])<i:
                return self.gen_empty_page("That's all for today")
            return self.gen_gallery_page(gds['cmv'][i].id,i,'mostv')
        elif gtype is 't':
            i=0
            if index.isnumeric() and int(index)<len(ggal):
                i=int(index)
            while len(gds['ctop'])<=i and gds['topind']<len(ggal):
                filtered=self.filter(ggal[gds['topind']])
                gds['topind']+=1
                if filtered:
                    gds['ctop'].append(filtered)
            if len(gds['ctop'])<i:
                return self.gen_empty_page("That's all for today")
            return self.gen_gallery_page(gds['ctop'][i].id,i,'top')
        else:
            return self.gen_empty_page("No idea what I'm doing here")
            
        
    def gen_image_page(self,iid):
        print("getting image", iid)
        image=self.im.get_image(iid)
        if image is None:
            return self.gen_empty_page()
        page=self.gen_page_header("r.om:"+iid)
        page+=("<h1><%s/h1>\n"%(image.title)) if image.title else ""
        page+=self.gen_image(image)
        return page+self.gen_page_footer()

    def gen_empty_page(self,msg="<h1>No noms here</h1>"):
        page=self.gen_page_header("no noms for r.om")
        page+=msg
        return page+self.gen_page_footer()

if __name__ == "__main__":
    app.run()
