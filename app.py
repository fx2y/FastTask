import logging

from fasthtml.common import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastHTML application
app, rt = fast_app('data/todo.db')

# Create users and todos tables
db = database('data/todo.db')
users = db.t.users
todos = db.t.todos

if users not in db.t:
    users.create(dict(name=str, pwd=str), pk='name')
User = users.dataclass()

if todos not in db.t:
    todos.create(dict(id=int, title=str, completed=bool, user=str), pk='id')
Todo = todos.dataclass()

# Redirect for unauthenticated users
login_redirect = RedirectResponse('/login', status_code=303)


def before(req, sess):
    try:
        auth = req.scope['auth'] = sess.get('auth', None)
        if not auth:
            logger.info(f"Unauthenticated access attempt to {req.url.path}")
            return login_redirect
        todos.xtra(user=auth)
        logger.info(f"User {auth} authenticated for {req.url.path}")
    except Exception as e:
        logger.error(f"Error in authentication middleware: {str(e)}")
        return login_redirect


# Create a Beforeware instance
beforeware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login', '/register'])

# Pass the beforeware to fast_app
app, rt = fast_app('data/todo.db', before=beforeware)


# Serve static files
@rt("/{fname:path}.{ext:static}")
async def static(fname: str, ext: str):
    return FileResponse(f'{fname}.{ext}')


@patch
def __ft__(self: Todo):
    show = AX(self.title, f'/todos/{self.id}', 'current-todo')
    edit = AX('edit', f'/edit/{self.id}', 'current-todo')
    dt = '✅ ' if self.completed else ''
    return Li(dt, show, ' | ', edit, Hidden(id="id", value=self.id), id=f'todo-{self.id}')


# Define the home route with GET method
@rt("/")
def get(auth):
    user_todos = todos(order_by='id')
    todo_form = Form(Input(name="title", placeholder="New Todo"),
                     Button("Add Todo"),
                     hx_post="/todos", hx_target="#todo-list", hx_swap="beforeend")
    return Titled("Todo App",
                  H1(f"Welcome, {auth}!"),
                  todo_form,
                  Ul(*user_todos, id='todo-list'),
                  Div(id='current-todo'),
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


# CREATE (INSERT) operation for todos
@rt("/todos")
def post(title: str, auth):
    if not title or len(title) > 100:  # Basic validation
        return "Invalid title", 400
    new_todo = Todo(id=None, title=title, completed=False, user=auth)
    return todos.insert(new_todo)


# READ (SELECT) operation for todos
@rt("/todos/{id:int}")
def get(id: int):
    todo = todos[id]
    return Div(Div(todo.title),
               Button('delete', hx_delete=f'/todos/{todo.id}',
                      hx_target=f'#todo-{todo.id}', hx_swap="outerHTML"))


# UPDATE operation for todos
@rt("/edit/{id:int}")
def get(id: int):
    todo = todos[id]
    return Form(Group(Input(id="title", value=todo.title),
                      Button("Save")),
                Hidden(id="id", value=todo.id),
                Checkbox(id="completed", label='Completed', checked=todo.completed),
                hx_put=f"/todos/{id}", hx_target=f"#todo-{id}")


@rt("/todos/{id:int}")
def put(id: int, title: str, completed: bool):
    if not title or len(title) > 100:  # Basic validation
        return "Invalid title", 400
    existing_todo = todos[id]
    existing_todo.title = title
    existing_todo.completed = completed
    return todos.update(existing_todo)


# DELETE operation for todos
@rt("/todos/{id:int}")
def delete(id: int):
    todos.delete(id)
    return ""


# Run the application
if __name__ == "__main__":
    serve()
