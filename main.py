from tornado.web import RequestHandler,Application,url
import tornado.ioloop
import motor.motor_tornado as motor

class base(RequestHandler):
    pass

class app(Application):
    def __init__(self):
        route = [
            ()
        ]
        settings = dict(
            template_path = "photon/template",
            cookie_secret="<>?><?>123123,.123,>!@<>!<!@#!@1231?>",
            login_url = "/auth/login",
            debug=True
        )
        super(Application, self).__init__(route,**settings)

class home(base):
    pass

class register(base):
    pass

class login(base):
    pass

class logout(base):
    pass

class user(base):
    pass

class feed(base):
    pass

class update(base):
    pass

class post(base):
    pass

class comment(base):
    pass

class like_dislike(base):
    pass

class create(base):
    pass

