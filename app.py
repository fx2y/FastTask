from fasthtml.common import *

# Initialize the FastHTML application
app, rt = fast_app('data/todo.db')

# Create users table
db = database('data/todo.db')
users = db.t.users
if users not in db.t:
    users.create(dict(name=str, pwd=str), pk='name')
User = users.dataclass()

# Redirect for unauthenticated users
login_redirect = RedirectResponse('/login', status_code=303)


# Serve static files
@rt("/{fname:path}.{ext:static}")
async def static(fname: str, ext: str):
    return FileResponse(f'{fname}.{ext}')


# Define the home route with GET method
@rt("/")
def get(sess):
    if 'auth' not in sess:
        return login_redirect
    return Titled("Todo App",
                  H1(f"Welcome, {sess['auth']}!"),
                  A("Logout", href="/logout"),
                  Link(rel="stylesheet", href="/static/css/style.css"))


@rt("/login")
def get():
    return Titled("Login",
                  Form(Input(id='name', placeholder='Username'),
                       Input(id='pwd', type='password', placeholder='Password'),
                       Button('Login'),
                       action='/login', method='post'))


@rt("/login")
def post(name: str, pwd: str, sess):
    if not name or not pwd:
        return login_redirect
    try:
        user = users[name]
        if compare_digest(user.pwd.encode("utf-8"), pwd.encode("utf-8")):
            sess['auth'] = user.name
            return RedirectResponse('/', status_code=303)
    except NotFoundError:
        pass
    return login_redirect


@rt("/logout")
def get(sess):
    sess.pop('auth', None)
    return login_redirect


@rt("/register")
def get():
    return Titled("Register",
                  Form(Input(id='name', placeholder='Username'),
                       Input(id='pwd', type='password', placeholder='Password'),
                       Button('Register'),
                       action='/register', method='post'))


@rt("/register")
def post(user: User):
    if not user.name or not user.pwd:
        return RedirectResponse('/register', status_code=303)
    try:
        users.insert(user)
        return RedirectResponse('/login', status_code=303)
    except:
        return "Username already exists", 400


# Run the application
if __name__ == "__main__":
    serve()
