from js import Response

def on_fetch(request):
    res=Response.new(my_tpl())
    res.headers.set("Content-Type", "text/html; charset=utf-8")
    return res

def my_tpl():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hello World</title>
    </head>
    <body>
        <h1>Hello, World!</h1>
        <p>Welcome to my Cloudflare Worker.</p>
    </body>
    </html>
    """
    return html_content
