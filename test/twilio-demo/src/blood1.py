import webapp2
import webapp2
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import blobstore
import cgi 
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
import jinja2
import os
import json
import time
from datetime import date
#setting the environment for templates
JINJA_ENVIRONMENT = jinja2.Environment(
	    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	        extensions=['jinja2.ext.autoescape'],
		    autoescape=True)




from math import sin, cos, asin, sqrt, degrees, radians

Earth_radius_km = 6371.0
RADIUS = Earth_radius_km

def haversine(angle_radians):
    return sin(angle_radians / 2.0) ** 2

def inverse_haversine(h):
    return 2 * asin(sqrt(h)) # radians

def distance_between_points(lat1, lon1, lat2, lon2):
    # all args are in degrees
    # WARNING: loss of absolute precision when points are near-antipodal
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlat = lat2 - lat1
    dlon = radians(lon2 - lon1)
    h = haversine(dlat) + cos(lat1) * cos(lat2) * haversine(dlon)
    return RADIUS * inverse_haversine(h)

def bounding_box(lat, lon, distance):
    # Input and output lats/longs are in degrees.
    # Distance arg must be in same units as RADIUS.
    # Returns (dlat, dlon) such that
    # no points outside lat +/- dlat or outside lon +/- dlon
    # are <= "distance" from the (lat, lon) point.
    # Derived from: http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
    # WARNING: problems if North/South Pole is in circle of interest
    # WARNING: problems if longitude meridian +/-180 degrees intersects circle of interest
    # See quoted article for how to detect and overcome the above problems.
    # Note: the result is independent of the longitude of the central point, so the
    # "lon" arg is not used.
    dlat = distance / RADIUS
    dlon = asin(sin(dlat) / cos(radians(lat)))
    return degrees(dlat), degrees(dlon)

if __name__ == "__main__":

    # Examples from Jan Matuschek's article

    def test(lat, lon, dist):
        print "test bounding box", lat, lon, dist
        dlat, dlon = bounding_box(lat, lon, dist)
        print "dlat, dlon degrees", dlat, dlon
        print "lat min/max rads", map(radians, (lat - dlat, lat + dlat))
        print "lon min/max rads", map(radians, (lon - dlon, lon + dlon))

    print "liberty to eiffel"
    print distance_between_points(40.6892, -74.0444, 48.8583, 2.2945) # about 5837 km
    print
    print "calc min/max lat/lon"
    degs = map(degrees, (1.3963, -0.6981))
    test(*degs, dist=1000)
    print
    degs = map(degrees, (1.3963, -0.6981, 1.4618, -1.6021))
    print degs, "distance", distance_between_points(*degs) # 872 km

class donor(db.Model):
             dname=db.StringProperty(required=True)
	     duser=db.UserProperty()
	     bgroup=db.StringProperty(required=True,choices=set(["A+","A-","B+","B-","AB+","AB-","O+","O-"]))
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     coordinates=db.GeoPtProperty()
	     age=db.StringProperty(required=True)
	     blob_key=blobstore.BlobReferenceProperty()
class recipient(db.Model):
    	     ruser=db.UserProperty()
	     rname=db.StringProperty(required=True)
	     bgroup=db.StringProperty(required=True,choices=set(["A+","A-","B+","B-","AB+","AB-","O+","O-"]))
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     bunit=db.StringProperty(required=True)
	     bdate=db.DateProperty()
	     coord=db.GeoPtProperty()

class hospital(db.Model):
    	     huser=db.UserProperty()
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     rname=db.StringProperty(required=True)
	     abgroup=db.StringListProperty()

class camp(db.Model):
    	     cuser=db.UserProperty()
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     cname=db.StringProperty(required=True)
	     sdate=db.StringProperty(required=True)
	     edate=db.StringProperty(required=True)
class link(db.Model):
	    cid=db.StringProperty()
	    guser=db.StringProperty()
	    flag=db.IntegerProperty()

class posts(db.Model):
            puser=db.UserProperty()
            comment=db.TextProperty()
            campid=db.StringProperty()
class story(db.Model):
	    suser=db.UserProperty()
	    story=db.TextProperty()
	    tag=db.TextProperty()
class notification(db.Model):
	    did=db.UserProperty()
	    rid=db.StringProperty()
	    flag=db.IntegerProperty()

class main(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	    	login=users.create_login_url("/index")
		template_values={'login':login}
		template=JINJA_ENVIRONMENT.get_template('html/main.html')
		self.response.write(template.render(template_values))

class index(webapp2.RequestHandler):
    	def get(self):
		user=users.get_current_user()
		notify=notification.all().filter("rid = ",str(user)).filter("flag = ",0)
		request=[]
		for i in notify:
				request.append(i)
		r=recipient.all()
		user = users.get_current_user()
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout,'user':user,'request':request,'r':r}
	    	template=JINJA_ENVIRONMENT.get_template('html/index.html')
		self.response.write(template.render(template_values))

class donate_blood(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	        if user:
			self.redirect('/pinfo')
		else:
			self.redirect(users.create_login_url(self.request.uri))
	    	template_values={}
		upload_url=blobstore.create_upload_url('/upload_photo')
	    	template=JINJA_ENVIRONMENT.get_template('html/donate_blood.html')
#		self.response.out.write('<html><body>')
 #self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
  #self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
#         name="submit" value="Submit"> </form></body></html>''')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		s=v+","+l
		var=donor(dname=self.request.get("name"),duser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),age=self.request.get("age"),coordinates=s)
		var.put()
		self.redirect("/index")

class pinfo(webapp2.RequestHandler):
	def get(self):
		flag=0
		user = users.get_current_user()
		if user:
			result=donor.all().filter('duser =',user)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result}
	    		template=JINJA_ENVIRONMENT.get_template('html/pinfo.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		user=users.get_current_user()
		result=donor.all().filter('duser =',user)
		if result.count()>0:
			k=result[0].key()
			obj=donor.get(k)
			obj.age=self.request.get("age")
			obj.dname=self.request.get("name")
			obj.address=self.request.get("address")
			obj.contact=self.request.get("phone")
			obj.bgroup=self.request.get("bgroup")
			obj.put()
		else:
			v=str(self.request.get("lat"))
			l=str(self.request.get("long"))
			s=v+", "+l
			var=donor(dname=self.request.get("name"),duser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),age=self.request.get("age"),coordinates=s)
			var.put()
		self.redirect("/hero")

class photoupload(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
	  try:
            upload = self.get_uploads()[0]
            user_photo = UserPhoto(user=users.get_current_user().user_id(),
                                   blob_key=upload.key())
            db.put(user_photo)

            self.redirect('/view_photo/%s' % upload.key())

          except:
            self.redirect('/html/upload_failure.html')
class map_donate(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		q=donor.all().filter("duser = ", user)
		v=q[0].address
		template_values={'locate':v}
		template=JINJA_ENVIRONMENT.get_template('html/map_donate.html')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		user=users.get_current_user()
		k=donor.all().filter("duser = ", user)
		for i in k:
			i.coordinates=v+","+l
			i.put()
		self.redirect("/index")
class moveTo(webapp2.RequestHandler):
	def get(self):
		template_values={}
                template=JINJA_ENVIRONMENT.get_template('html/index.html')
                self.response.write(template.render(template_values))
	def post(self):
		q=db.GQLQuery('Select * from donor where duser= :1',users.get_current_user())
		s=str(self.request.get("latFld"))
		d=str(self.request.get("lngFld"))
		q['coordinate']=db.GeoPt(s,d)
class recieve_blood(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	        if user:
			self.redirect('/prinfo')
		else:
			self.redirect(users.create_login_url(self.request.uri))
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/recieve_blood.html')
		self.response.write(template.render(template_values))
	def post(self):
		var=recipient(rname=self.request.get("name"),ruser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"))
		var.put()
		self.redirect("/map_view")

class prinfo(webapp2.RequestHandler):
	def get(self):
		flag=0
		user = users.get_current_user()
		if user:
			result=recipient.all().filter('ruser =',user)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result}
	    		template=JINJA_ENVIRONMENT.get_template('html/prinfo.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		user=users.get_current_user()
		result=recipient.all().filter('ruser =',user)
		if result.count()>0:
			k=result[0].key()
			obj=recipient.get(k)
			obj.rname=self.request.get("name")
			obj.address=self.request.get("address")
			obj.contact=self.request.get("phone")
			obj.bgroup=self.request.get("bgroup")
			obj.put()
		else:
			v=str(self.request.get("lat"))
             		l=str(self.request.get("long"))
			var=recipient(rname=self.request.get("name"),ruser=users.get_current_user(),bdate=date.today(),bunit=self.request.get("bunit"),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),coord=v+','+l)
			var.put()
		self.redirect("/show_donor")


class cinfo(webapp2.RequestHandler):
	def get(self):
		flag=0
		user=users.get_current_user()
		if user:		  
	  		logout=users.create_logout_url("/")
	    		template_values={}
	    		template=JINJA_ENVIRONMENT.get_template('html/cinfo.html')
			self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
             	l=str(self.request.get("long"))
		var=camp(cname=self.request.get("name"),cuser=users.get_current_user(),sdate=self.request.get("sdate"),edate=self.request.get("edate"),contact=self.request.get("phone"),address=self.request.get("address"),coord=v+','+l)
		var.put()
		self.redirect("/organise")

class send_mail(webapp2.RequestHandler):
	def post(self):
		user=users.get_current_user()
		rst=recipient.all().filter("ruser =", user)
		rbgroup=rst[0].bgroup
		don=donor.all().filter("bgroup =",rbgroup)
		for i in don:
#to_addr = self.request.get("friend_email")	
			to_addr=i.duser.email()
			self.response.write(to_addr)
			message = mail.EmailMessage()
			message.sender = user.email()
			message.to = to_addr
			message.body = """You can save many lives : this user needs this units of blood dated on this please help him by donating the blood """ 
			message.send()
		self.redirect("/view_mail")
class view_mail(webapp2.RequestHandler):
	def get(self):

		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/send_mail.html')
		self.response.write(template.render(template_values))		
class hero(webapp2.RequestHandler):
	def get(self):

		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/hero.html')
		self.response.write(template.render(template_values))		

class view_request(webapp2.RequestHandler):
	def get(self,param1):
		p=param1
		value=None
		rec=recipient.all()
		for i in rec:
			if str(i.key())==str(param1):
				value=i
				break
		logout=users.create_logout_url("/")
	    	template_values={'value':value,'p':p,'param1':param1,'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/view_request.html')
		self.response.write(template.render(template_values))		

class camps_detail(webapp2.RequestHandler):
    	def get(self):
	    user=users.get_current_user()
	    if user:
	    	result=camp.all()
	    	li=link.all()
	    	having=[]
	    	rest=[]
		logout=users.create_logout_url("/")
	    	for i in result:
	    		fl=0
	    		for j in li:
	    			if str(i.key())==str(j.cid) and j.guser==user.email() and j.flag==1:
	    				having.append(i)
	    				fl=1
	    				break
	    		if fl==0:
	    			rest.append(i)		
	    	template_values={'having':having,'rest':rest,'user':user,'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/camps_detail.html')
	    	self.response.write(template.render(template_values))		
    	    else:
			self.redirect(users.create_login_url(self.request.uri))

class camp_post(webapp2.RequestHandler):
	def get(self,camp_id):
	    name=camp.all()
	    for i in name:
		if str(i.key())==str(camp_id):
			cur_camp=i		
	    user=users.get_current_user()
	    post=posts.all().filter("campid = ",str(camp_id))
	    template_values={'post':post,'cuser':user,'cur_camp':cur_camp}
	    template=JINJA_ENVIRONMENT.get_template('html/camp_post.html')
	    self.response.write(template.render(template_values))			    
	def post(self,camp_id):
	    user=users.get_current_user()
	    var=posts(campid=str(camp_id),puser=user,comment=self.request.get("comment"))
	    var.put()
	    self.redirect('/camp_post/'+camp_id)
class map_view(webapp2.RequestHandler):
    	def get(self):
		user=users.get_current_user()
		q=recipient.all().filter("ruser = ", user)
		v=q[0].address
		template_values={'locate':v}
		template=JINJA_ENVIRONMENT.get_template('html/map_view.html')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		user=users.get_current_user()
		k=recipient.all().filter("ruser = ", user)
		for i in k:
			i.coord=v+","+l
			i.put()
		self.redirect("/show_donor")

class recipient_request(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		if user:	
			logout=users.create_logout_url("/")
			r=recipient.all()
	    		template_values={'r':r,'user':user,'logout':logout}
	    		template=JINJA_ENVIRONMENT.get_template('html/recipient_request.html')
			self.response.write(template.render(template_values))		
    		else:
			self.redirect(users.create_login_url(self.request.uri))
class add_notification(webapp2.RequestHandler):
	def get(self,rec_id):
		user=users.get_current_user()
		var=notification(did=user,rid=str(rec_id),flag=0)
		var.put()
		self.redirect("/hero")
class show_notification(webapp2.RequestHandler):
	def get(self,get_key):	
		user=users.get_current_user()
		notify=notification.all()
		request=[]
		for i in notify:
			if str(i.key())==str(get_key):
				request.append(i)
	    	template_values={'request':request}
	    	template=JINJA_ENVIRONMENT.get_template('html/show_notification.html')
		self.response.write(template.render(template_values))		
class pop(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/pop.html')
		self.response.write(template.render(template_values))		
class show_donor(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		k=recipient.all().filter("ruser = ",user)
		q=donor.all().filter("bgroup = ", k[0].bgroup)
		r=str(k[0].coord)
		r=r.split(",")
		a={}
		lat=[]
		lng=[]
		final=[]
		add=[]
		name=[]
		lis=[]
		for i in q:
			s=str(i.coordinates)
			l=s.split(",")
			lis.append(distance_between_points(float(l[0]),float(l[1]),float(r[0]),float(r[1])))
			lis.append(i.address)
			lis.append(i.contact)
                        lis.append(i.duser.email())
			a[i.dname]=lis
			lis=[]
			lat.append(i.dname)
			lat.append(float(l[0]))	
			lat.append(float(l[1]))
			final.append(lat)
			lat=[]
			add.append(i.address)
			add.append(i.dname)
			name.append(add)
			add=[]
		sorted(a.values())

		logout=users.create_logout_url("/")
		template_values={'locate':k[0].address,'vivek':a,'final':json.dumps(final),'long':float(r[1]),'latit':float(r[0]),'name':name,'a':a,'logout':logout}
		template=JINJA_ENVIRONMENT.get_template('html/show_donor.html')
		self.response.write(template.render(template_values))
		'''v=self.request.get("location")
	    	template_values={'locate':v}
	    	template=JINJA_ENVIRONMENT.get_template('map_view.html')
		self.response.write(template.render(template_values))'''
class going_event(webapp2.RequestHandler):
    	def get(self,camp_id):
	    user=users.get_current_user()
	    var=link(cid=str(camp_id),guser=str(user.email()),flag=1)
	    var.put()
	    c_all=camp.all()
	    for i in c_all:
			if str(i.key())==camp_id:
				camp_name=i.cname
				ad=i.address
				st=i.sdate
				et=i.edate
	    s=st.split(",")
	    l=s[0].split()
	    start=""
	
	    if l[1]=="November":
		start+=s[1][1:]+"-"+"11-"+l[0]
	    if l[1]=="December":
		start+=s[1][1:]+"-"+"12-"+l[0]
	    
	    if l[1]=="January":
		start+=s[1][1:]+"-"+"1-"+l[0]
	    if l[1]=="February":
		start+=s[1][1:]+"-"+"2-"+l[0]
	    if l[1]=="March":
		start+=s[1][1:]+"-"+"3-"+l[0]
	    if l[1]=="April":
		start+=s[1][1:]+"-"+"4-"+l[0]
	    if l[1]=="May":
		start+=s[1][1:]+"-"+"5-"+l[0]
	    if l[1]=="June":
		start+=s[1][1:]+"-"+"6-"+l[0]

	    if l[1]=="July":
		start+=s[1][1:]+"-"+"7-"+l[0]
	    if l[1]=="August":
		start+=s[1][1:]+"-"+"8-"+l[0]
	    if l[1]=="September":
		start+=s[1][1:]+"-"+"9-"+l[0]
	
	    if l[1]=="October":
		start+=s[1][1:]+"-"+"10-"+l[0]
	    fs=start
	    s=et.split(",")
	    l=s[0].split()
	    start=""
	    if l[1]=="November":
		start+=s[1][1:]+"-"+"11-"+l[0]
	    if l[1]=="December":
		start+=s[1][1:]+"-"+"12-"+l[0]
	    
	    if l[1]=="January":
		start+=s[1][1:]+"-"+"1-"+l[0]
	    if l[1]=="February":
		start+=s[1][1:]+"-"+"2-"+l[0]
	    if l[1]=="March":
		start+=s[1][1:]+"-"+"3-"+l[0]
	    if l[1]=="April":
		start+=s[1][1:]+"-"+"4-"+l[0]
	    if l[1]=="May":
		start+=s[1][1:]+"-"+"5-"+l[0]
	    if l[1]=="June":
		start+=s[1][1:]+"-"+"6-"+l[0]

	    if l[1]=="July":
		start+=s[1][1:]+"-"+"7-"+l[0]
	    if l[1]=="August":
		start+=s[1][1:]+"-"+"8-"+l[0]
	    if l[1]=="September":
		start+=s[1][1:]+"-"+"9-"+l[0]
	
	    if l[1]=="October":
		start+=s[1][1:]+"-"+"10-"+l[0]

	    fe=start

            logout=users.create_logout_url("/")
	    template_values={'user':user,'camp_user':camp_name,'address':ad,'start':fs,'end':fe,'logout':logout}
	    template=JINJA_ENVIRONMENT.get_template('html/going_event.html')
	    self.response.write(template.render(template_values))	
	    
class coming_donors(webapp2.RequestHandler):
    	def get(self):
	    user=users.get_current_user()
	    logout=users.create_logout_url("/")
	    s=str(user.email())
	    donr=link.all().filter("cuser =",s) 
	    out="Name	Email	Contact     Address                                                                                    "
	    don=donor.all()
	    a=[]
	    for i in donr:
		fl=0
	    	for j in don:
	 		st=str(j.duser.email())
			if st==i.guser:
				fl=1
				out+="j.name	st	j.contact	j.address                                                        "
				break
		
	    template_values={'donor':donr,'out':out,'logout':logout}
	    template=JINJA_ENVIRONMENT.get_template('html/coming_donors.html')
	    self.response.write(template.render(template_values))	
class final_receive(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/final_receive.html')
		self.response.write(template.render(template_values))		
class about(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/about.html')
		self.response.write(template.render(template_values))		
class contact(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/contact.html')
		self.response.write(template.render(template_values))		
class organise(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
		user=users.get_current_user()
		q=link.all().filter("cuser =",user.email())
		if q.count()!=0:
			flag=1
		else:
			flag=0	
	    	template_values={'logout':logout,'flag':flag}
	    	template=JINJA_ENVIRONMENT.get_template('html/organise.html')
		self.response.write(template.render(template_values))		

class about1(webapp2.RequestHandler):
	def get(self):
		login=users.create_login_url("/index")
	    	template_values={'login':login}
	    	template=JINJA_ENVIRONMENT.get_template('html/about1.html')
		self.response.write(template.render(template_values))		
class contact1(webapp2.RequestHandler):
	def get(self):
		login=users.create_login_url("/index")
	    	template_values={'login':login}
	    	template=JINJA_ENVIRONMENT.get_template('html/contact1.html')
		self.response.write(template.render(template_values))		
			
class gplus(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/gplus.html')
		self.response.write(template.render(template_values))		
	def post(self):
		'''if request.args.get('state', '') != session['state']:
		     response = make_response(json.dumps('Invalid state parameter.'), 401)
		     response.headers['Content-Type'] = 'application/json'
		     self.response.write(response)
 		gplus_id = request.args.get('gplus_id')
		code = request.data
	
		try:
		    # Upgrade the authorization code into a credentials object
    		 	oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		 	oauth_flow.redirect_uri = 'postmessage'
    		 	credentials = oauth_flow.step2_exchange(code)
  		except FlowExchangeError:
    			response = make_response(
        		json.dumps('Failed to upgrade the authorization code.'), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Check that the access token is valid.
  		access_token = credentials.access_token
  		url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        		 % access_token)
  		h = httplib2.Http()
  		result = json.loads(h.request(url, 'GET')[1])
  # If there was an error in the access token info, abort.
  		if result.get('error') is not None:
    			response = make_response(json.dumps(result.get('error')), 500)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Verify that the access token is used for the intended user.
  		if result['user_id'] != gplus_id:
    			response = make_response(
        			json.dumps("Token's user ID doesn't match given user ID."), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Verify that the access token is valid for this app.
  		if result['issued_to'] != CLIENT_ID:
    			response = make_response(
      			  json.dumps("Token's client ID does not match app's."), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  		stored_credentials = session.get('credentials')
  		stored_gplus_id = session.get('gplus_id')
  		if stored_credentials is not None and gplus_id == stored_gplus_id:
    			response = make_response(json.dumps('Current user is already connected.'),
                             200)
    			response.headers['Content-Type'] = 'application/json'
    		i	return response
  # Store the access token in the session for later use.
  		session['credentials'] = credentials
  		session['gplus_id'] = gplus_id
  		response = make_response(json.dumps('Successfully connected user.', 200))'''
class share(webapp2.RequestHandler):
	def get(self):
	    	user=users.get_current_user()		
		pstories=story.all().filter("suser =",user)
	    	template_values={'pstories':pstories}
	    	template=JINJA_ENVIRONMENT.get_template('html/share.html')
		self.response.write(template.render(template_values))			
class putstory(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/putstory.html')
		self.response.write(template.render(template_values))			
	def post(self):
	    	user=users.get_current_user()		
		var=story(story=self.request.get("story"),tag=self.request.get("tag"),suser=user)
		var.put()
		self.redirect("/share")
class stry(webapp2.RequestHandler):
	def get(self):
		all_story=story.all()
	    	template_values={'stories':all_story}
	    	template=JINJA_ENVIRONMENT.get_template('html/stry.html')
		self.response.write(template.render(template_values))			

class copy(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/copy.html')
		self.response.write(template.render(template_values))			

class faq(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/faq.html')
		self.response.write(template.render(template_values))			

application=webapp2.WSGIApplication([
	                ("/",main),
                        ("/faq",faq),
	                ("/index",index),
	                ("/donate_blood",donate_blood),
	                ("/recieve_blood",recieve_blood),
	                ("/map_view",map_view),
			("/map_donate",map_donate),
			("/moveTo",moveTo),
			("/show_donor",show_donor),
			("/pinfo",pinfo),
			("/prinfo",prinfo),
			("/cinfo",cinfo),
			("/stry",stry),
			("/add_notification/(\S+)",add_notification),
			("/send_mail",send_mail),
			("/view_mail",view_mail),
			("/recipient_request",recipient_request),
			("/view_request/(\S+)",view_request),
			("/camps_detail",camps_detail),
			("/camp_post/(\S+)",camp_post),
			("/upload_photo",photoupload),
			("/final_receive",final_receive),
			("/copy",copy),
			#("/going_event/(\w+@\w+\.\w+)",going_event),
			("/going_event/(\S+)",going_event),
			("/about",about),
			("/contact",contact),
			("/coming_donors",coming_donors),
			("/putstory",putstory),
			("/about1",about1),
			("/contact1",contact1),
			("/share",share),
			("/putstory",putstory),
			("/show_notification/(\S+)",show_notification),
			("/hero",hero),
			("/pop",pop),
			("/organise",organise),
			("/gplus",gplus),
],debug=True)

