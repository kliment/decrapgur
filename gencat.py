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

class gallery:
    def __init__(self,name):
        self.name=name
        self.items=None
        self.time=0
        self.index=0
        self.citems=[]

class pagegen:

    def __init__(self,cid=CLIENT_ID):
        global gds
        if not 'im' in gds:
            gds['im']=pyimgur.Imgur(cid)
        self.im=gds['im']
        if not 'gal' in gds:
            gds['gal']={}
        if not '_m' in gds['gal']:
            gds['gal']['_m']=gallery('_m')
        if not '_t' in gds['gal']:
            gds['gal']['_t']=gallery('_t')
        if not 'tags' in gds:
            gds['tags']={}
        self.craplist=['trump','biden','bleach','skeleton','hydroxy','current','vote','spoopy','skellingtons','pray','covid','shitpost','politic']
        
    def GET(self,url):
        r=re.compile("/([a-zA-Z0-9]+)(/[a-zA-Z0-9+]*)?(/[a-zA-Z0-9+]*)?(.*)?")
        m=r.search('/'+url)
        if m is not None:
            mg1=m.group(1) if m.group(1) is not None else ""
            mg2=m.group(2) if m.group(2) is not None else ""
            mg3=m.group(3) if m.group(3) is not None else ""
            if 'gallery' in mg1:
                return self.gen_gallery_page(mg2.strip('/'))
            elif 'mostv' in mg1:
                return self.gen_browse_page(mg2.strip('/'),gtype='_m')
            elif 'top' in mg1:
                return self.gen_browse_page(mg2.strip('/'),gtype='_t')
            elif 'tags' in mg1:
                return str(gds['tags'])
            elif 'a' is mg1:
                return self.gen_album_page(mg2.strip('/'))
            elif 'r' is mg1 and len(mg2):
                return self.gen_browse_page(mg3.strip('/'),gtype=mg2.strip('/'))
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
    
    def gen_gallery_page(self,aid,index=None,gallery=None):
        print("getting gallery item", aid)
        navbar=""
        browse=""
        gal="gallery/"
        rgal="gallery/"
        if gallery is not None:
            if gallery.name is '_m':
                browse="mostv"
            elif gallery.name is '_t':
                browse="top"
            else:
                browse='r/'+gallery.name
                gal=""
                rgal=browse+"/"
        if index is not None and index>0 and gallery is not None:
            navbar+="""
            <a class="prev" href="%s" > Previous </a>
            """%('/'+browse+'/'+str(index-1))
        navbar+="""
            <a class="self-link" href="%s"> Self </a>
            """%('/'+gal+aid)
        navbar+="""
            <a class="self-link" href="%s"> <small>imgur</small> </a>
            """%('https://imgur.com/'+rgal+aid)
        if index is not None and index>=0 and browse is not None:
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
                try:
                    if gallery is not None:
                        image=self.im.get_subreddit_image(gallery.name,aid)
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
                for b in self.craplist:
                    if b in tag['display_name']:
                        print("banned due to", b)
                        banned=True
                        break
        if not banned:
            return item
        return None

    def gen_browse_page(self,index,gtype='_m'):
        if not gtype in gds['gal']:
            gds['gal'][gtype]=gallery(gtype)
        g=gds['gal'][gtype]
        if g.items is None or time.time()-g.time>3600:
                print("fetching:",gtype)
                if gtype is '_m':
                    g.items=self.im.get_gallery(section='hot',sort='time',window='day',limit=400)
                elif gtype is '_t':
                    g.items=self.im.get_gallery(section='top',sort='time',window='day',limit=400)
                else:
                    g.items=self.im.get_subreddit_gallery(gtype, sort='top', window='day', limit=None)
                if g.items is not None:
                    print("fetched %d items"%(len(g.items),))
                    for i in g.items:
                        i.tags=None
                    g.citems=[]
                    if(gtype is not '_m' and gtype is not '_t'):
                        g.citems=g.items
                    g.index=0
                g.time=time.time()
        if g.items is None:
            return self.gen_empty_page("No such thing")
        if index.isnumeric() and int(index)>=len(g.items):
            self.gen_empty_page("That's all for today")
        i=0
        if index.isnumeric() and int(index)<len(g.items):
            i=int(index)
        while len(g.citems)<=i and g.index<len(g.items):
            filtered=self.filter(g.items[g.index])
            g.index+=1
            if filtered:
                g.citems.append(filtered)
        if len(g.citems)<i:
            return self.gen_empty_page("That's all for today")
        return self.gen_gallery_page(g.items[i].id,i,g)
            
        
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
