from tornado.web import RequestHandler,Application,url
import tornado.ioloop
import motor.motor_tornado as motor
import bcrypt
import tornado.escape

db = motor.MotorClient("mongodb://localhost:27017")

class app(Application):
    def __init__(self,db):
        route = [
            url("/",home,name="home"),
            url("/login",login,name="login"),
            url("/register",register,name="register")
        ]
        settings = dict(
            template_path = "photon/template",
            cookie_secret="edugorilla is a good company",
            login_url = "/login",
            debug=True,
            db = db
        )
        super(app, self).__init__(route,**settings)

class home(RequestHandler):
    def get(self):
        self.render("home.html")

class register(RequestHandler):
    def get(self):
        self.render("register.html")

    async def post(self):
        db = self.settings["db"]
        user = db["photon"]["user"]
        id = user.count()+1
        name = self.get_body_argument("name")
        username = self.get_body_argument("username")
        password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_body_argument("passwd")),
            bcrypt.gensalt(),
        )
        n = await user.find_one({"username":username})
        if not n:
            await user.insert_one({"_id":id,"name":name,"username":username,"password":password})
            self.set_secure_cookie("blog_user",str(id))
            self.redirect("/login")
        else:
            self.render("register.html",error="username exist")

class login(RequestHandler):
    def get(self):
        self.render("login.html")

    async def post(self):
        db = self.settings["db"]
        user = db["photon"]["user"]
        username = self.get_body_argument("username")
        user = await user.find_one({"username":username})
        if username == user["username"]:
            password = self.get_body_argument("password")
            hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                bcrypt.hashpw,
                tornado.escape.utf8(password),
                tornado.escape.utf8(user["password"]),
            )
            hashed_password = tornado.escape.to_unicode(hashed_password)
            if hashed_password == user["password"]:
                self.set_secure_cookie("blog_user",str(user["_id"]))
                self.redirect("")
        
        else:
            self.render("login.html",error="Wrong username or password")


class logout(RequestHandler):
    def get(self):
        self.clear_cookie("blog_user")
        self.redirect("/")

class user(RequestHandler):
    pass

class feed(RequestHandler):
    pass

class update(RequestHandler):
    pass

class post(RequestHandler):
    pass

class comment(RequestHandler):
    pass

class like_dislike(RequestHandler):
    pass

class create(RequestHandler):
    pass

async def main():
    app = Application(db)
    app.listen(8888)