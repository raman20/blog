from tornado.web import RequestHandler,Application,StaticFileHandler,url
import tornado.ioloop
import motor.motor_tornado as motor
import os
import datetime

db = motor.MotorClient("mongodb://localhost:27017/")

day = datetime.datetime.now().day
month = datetime.datetime.now().month
year = datetime.datetime.now().year

class home(RequestHandler):
    def get(self):
        self.render("home.html")

class register(RequestHandler):
    def get(self):
        self.render("register.html",error=None)

    async def post(self):
        user = db["web"]["user"]
        uid = await user.estimated_document_count()
        fname = self.get_body_argument("fname")
        lname = self.get_body_argument("lname")
        username = self.get_body_argument("username")
        password = self.get_body_argument("passwd")
        n = await user.find_one({"username":username})
        if not n:
            await user.insert_one({
                "_id":uid+1,
                "fname":fname,
                "lname":lname,
                "username":username,
                "password":password,
                "pid":[],
                "dp":"dfdp.jpeg"
                })
            self.set_secure_cookie("blog_user",str(id))
            self.redirect("/login")
        else:
            self.render("register.html",error="username exist")

class login(RequestHandler):
    def get(self):
        self.render("login.html",error=None)

    async def post(self):
        user = db["web"]["user"]
        username = self.get_body_argument("username")
        user = await user.find_one({"username":username})
        if user :
            if self.get_body_argument("passwd") == user["password"]:
                self.set_secure_cookie("blog_user",str(user["_id"]))
                self.redirect("/user")
            else:
                self.render("login.html",error="Wrong username or password")
        
        else:
            self.render("login.html",error="Wrong username or password")


class logout(RequestHandler):
    def get(self):
        self.clear_cookie("blog_user")
        self.redirect("/")

class user(RequestHandler):
    async def get(self):
        if self.get_secure_cookie("blog_user"):
            user_id = int(self.get_secure_cookie("blog_user"))
            user = db["web"]["user"]
            post = db["web"]["post"]
            req_post = list()
            user_info = await user.find_one({"_id":user_id})
            pid = user_info["pid"]
            if pid:
                for i in pid:
                    req_post.append(await post.find_one({"_id":i}))
                    self.render("user.html",user=user_info,post=req_post)
            self.render("user.html",user=user_info,post=None)
        else:
            self.redirect("/login")

class edit_user(RequestHandler):
    def get(self):
        if self.get_secure_cookie("blog_user"):
            self.render("edit_profile.html")
        else:
            self.redirect("/login")

    async def post(self):
        if self.get_secure_cookie("blog_user"):
            user_id = self.get_secure_cookie("blog_user")
            user_id = int(user_id)
            user = db["web"]["user"]
            user_detail = await user.find_one({"_id":user_id})
            username = user_detail["username"]
            files = self.request.files["img"]
            for f in files:
                f.filename = username+'.'+f.filename.split(".")[-1]
                fh = open(f"static/{f.filename}","wb")
                fh.write(f.body)
                fh.close()
            await user.update_one({"_id":user_id},{
                "$set":{
                    "dp":f.filename
                    }
                })
            self.redirect("/user")
        else:
            self.redirect("/login")
        

class feed(RequestHandler):
    async def get(self):
        if self.get_secure_cookie("blog_user"):
            trend_post = list()
            normal_post = list()
            post = db["web"]["post"]
            post_info = post.find()
            for i in await post_info.to_list(length=100000):
                if i["day"]==day and i["month"]==month and i["year"]==year:
                    if sum(i["like"])+sum(i["dislike"])+len(i["comment"]):
                        trend_post.append(i)
                    else:
                        normal_post.append(i)
                else:
                    normal_post.append(i)
            sorted(trend_post,key=lambda i: sum(i["like"])+sum(i["dislike"])+len(i["comment"]),reverse=True)
            normal_post.reverse()
            self.render("feed.html",trend_post=trend_post,normal_post=normal_post)
        else:
            self.redirect("/login")

class create_post(RequestHandler):
    def get(self):
        if self.get_secure_cookie("blog_user"):
            self.render("create_post.html")
        else:
            self.redirect("/login")

    async def post(self):
        if self.get_secure_cookie("blog_user"):
            user_id = int(self.get_secure_cookie("blog_user"))
            user = db["web"]["user"]
            post = db["web"]["post"]
            user_detail = await user.find_one({"_id":user_id})
            pid = await post.estimated_document_count()
            blog = self.get_body_argument("blog")
            files = self.request.files.get("file")
            if files:
                for f in files:
                    filename = user_detail["username"]+str(pid+1)+'.'+f.filename.split(".")[-1]
                    fh = open(f"static/{filename}","wb")
                    fh.write(f.body)
                    fh.close()
                await post.insert_one({
                    "_id":pid,
                    "uid":user_detail["username"],
                    "file":filename,
                    "blog":blog,
                    "like":[],
                    "dislike":[],
                    "ld_uid":[],
                    "comment":[],
                    "c_uid":[],
                    "day":day,
                    "month":month,
                    "year":year
                    })
            else:
                await post.insert_one({
                    "_id":pid,
                    "uid":user_detail["username"],
                    "file":"",
                    "blog":blog,
                    "like":[],
                    "dislike":[],
                    "comment":[],
                    "c_uid":[],
                    "day":day,
                    "month":month,
                    "year":year
                    })
            await user.update_one({"_id":user_id},{
                "$push":{
                    "pid":pid
                    }
                })
            self.redirect("/user")
        else:
            self.redirect("/login")
                    
                

class edit_post(RequestHandler):
    async def get(self,pid):
        if self.get_secure_cookie("blog_user"):
            post = db["web"]["post"]
            p = await post.find_one({"_id":int(pid)})
            blog = p["blog"]
            self.render("edit_post.html",blog=blog,pid=pid,p=p)
        else:
            self.redirect("/login")
        
    async def post(self,pid):
        if self.get_secure_cookie("blog_user"):
            post = db["web"]["post"]
            pid = int(pid)
            pinfo = await post.find_one({"_id":pid})
            file_name = pinfo["file"]
            blog = self.get_body_argument("blog")
            files = self.request.files.get("img")
            try:
                del_img = self.get_body_argument("del_img")
            except:
                del_img = None
            if files:
                for f in files:
                    file_name = pinfo["uid"]+str(pid)+"."+f.filename.split['.'][-1]
                    fh = open(f"static/{file_name}","wb")
                    fh.write(f.body)
                    fh.close()
            elif del_img:
                os.remove(f"static/{file_name}")
                await post.update_one({"_id":int(pid)},{"$set":{"file":""}})

            await post.update_one({"_id":int(pid)},{"$set":{"blog":blog}})
            self.redirect("/user")
        else:
            self.redirect("/login")

class delete_post(RequestHandler):
    async def get(self,pid):
        if self.get_secure_cookie("blog_user"):
            post = db["web"]["post"]
            user = db["web"]["user"]
            p_info = await post.find_one({"_id":int(pid)})
            for _,_,files in os.walk("static"):
                pass
            if p_info['file'] in files:
                os.remove(f"static/{p_info['file']}")
            await post.delete_one({"_id":int(pid)})
            await user.update_one({"_id":int(self.get_secure_cookie("blog_user"))},{"$pull":{"pid":{"$in":[pid]}}})
            await user.update_one({"_id":int(self.get_secure_cookie("blog_user"))},{"$pull":{"pid":{"$in":[0]}}})
            self.redirect("/user")
        else:
            self.redirect("/login")


class get_post(RequestHandler):
    async def get(self,pid):
        if self.get_secure_cookie("blog_user"):
            post = db["web"]["post"]
            user = db["web"]["user"]
            pid = int(pid)
            user_info = await user.find_one({"_id":int(self.get_secure_cookie("blog_user"))})
            post_info = await post.find_one({"_id":pid})
            self.render("post.html",post=post_info,user=user_info["username"]) 
        else:
            self.redirect("/login")

class add_comment(RequestHandler):
     async def post(self,pid):
         user_id = int(self.get_secure_cookie("blog_user"))
         pid = int(pid)
         cmnt = self.get_body_argument("cmnt")
         post = db["web"]["post"]
         user = db["web"]["user"]
         user_info = await user.find_one({"_id":user_id})
         await post.update_one({"_id":pid},{"$push":{"comment":cmnt,"c_uid":user_info["username"]}})
         self.redirect(f"/get_post/{pid}")

class like(RequestHandler):
    async def post(self,pid):
        if self.get_secure_cookie("blog_user"):
            user_id = int(self.get_secure_cookie("blog_user"))
            post = db["web"]["post"]
            p_info = await post.find_one({"_id":int(pid)})
            ld_uid = p_info["ld_uid"]
            if user_id in ld_uid:
                if p_info["like"][ld_uid.index(user_id)]:
                    await post.update_one({"_id":int(pid)},{"$set":{"like."+str(ld_uid.index(user_id)):0}})
                else:
                    await post.update_one({"_id":int(pid)},{"$set":{"like."+str(ld_uid.index(user_id)):1}})
                    await post.update_one({"_id":int(pid)},{"$set":{"dislike."+str(ld_uid.index(user_id)):0}})
            else:
                await post.update_one({"_id":int(pid)},{"$push":{"ld_uid":user_id}})
                await post.update_one({"_id":int(pid)},{"$push":{"like":1}})
                await post.update_one({"_id":int(pid)},{"$push":{"dislike":0}})
            self.redirect("/feed")

class dislike(RequestHandler):
    async def post(self,pid):
        if self.get_secure_cookie("blog_user"):
            user_id = int(self.get_secure_cookie("blog_user"))
            post = db["web"]["post"]
            p_info = await post.find_one({"_id":int(pid)})
            ld_uid = p_info["ld_uid"]
            if user_id in ld_uid:
                if p_info["dislike"][ld_uid.index(user_id)]:
                    await post.update_one({"_id":int(pid)},{"$set":{"dislike."+str(ld_uid.index(user_id)):0}})
                else:
                    await post.update_one({"_id":int(pid)},{"$set":{"dislike."+str(ld_uid.index(user_id)):1}})
                    await post.update_one({"_id":int(pid)},{"$set":{"like."+str(ld_uid.index(user_id)):0}})
            else:
                await post.update_one({"_id":int(pid)},{"$push":{"ld_uid":user_id}})
                await post.update_one({"_id":int(pid)},{"$push":{"dislike":1}})
                await post.update_one({"_id":int(pid)},{"$push":{"like":0}})
            self.redirect("/feed")


if __name__ == "__main__":
    app = Application([
            (r"/",home),
            (r"/login",login),
            (r"/register",register),
            (r"/feed",feed),
            (r"/user",user),
            (r"/user/edit",edit_user),
            (r"/create_post",create_post),
            (r"/edit_post/(.*)",edit_post),
            (r"/delete_post/(.*)",delete_post),
            (r"/get_post/(.*)",get_post),
            (r"/like/(.*)",like),
            (r"/dislike/(.*)",dislike),
            (r"/comment/(.*)",add_comment),
            (r"/logout",logout)
        ],template_path = "template",
        cookie_secret="123123123123123",
        static_path="static",
        debug=True)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()