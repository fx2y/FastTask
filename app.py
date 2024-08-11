from fasthtml.common import *

# Initialize the FastHTML application
app, rt = fast_app('data/todo.db')


# Serve static files
@rt("/{fname:path}.{ext:static}")
async def static(fname: str, ext: str):
    return FileResponse(f'{fname}.{ext}')


# Define the home route with GET method
@rt("/")
def get():
    return Titled("Todo App",
                  H1("Welcome to the FastHTML Todo App!"),
                  Link(rel="stylesheet", href="/static/css/style.css"))


# Run the application
if __name__ == "__main__":
    serve()
