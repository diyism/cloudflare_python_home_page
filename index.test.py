async def python_home_page():
    kvml1 = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<body>
    <h1>Hello, <:for i in range(2):#{#:><:=user_name:>,<:#}#:>!</h1>
    <p>Welcome to my cloudflare python home page.</p>
    <:response = await fetch("http://httpx.com") #;#write.append(await response.text()):>
</body>
</html>
    """
    kvml="""hello a<:response = await fetch("http://httpx.com")#;#write.append(await response.text())#;#write.append('hello'):>"""
    user_name="jack"
    html = await tpl.parse(kvml, context=globals())
    return html

#===========cloudflare request and response================
from js import Response, fetch, console
import asyncio
async def on_fetch(request):
    res = Response.new(await python_home_page())
    res.headers.set("Content-Type", "text/html; charset=utf-8")
    return res

#===========python micro template:=================================
import re, collections.abc, textwrap
class tpl:
    @staticmethod
    def re_sub_call(m):
        rtn = re.sub(r"\\", r"\\\\", m.group(0))
        rtn = re.sub("'", r"\'", rtn)
        return rtn

    @staticmethod
    def recursive_indent(arr, level):
        for i in range(len(arr)):
            if isinstance(arr[i], list):
                arr[i] = tpl.recursive_indent(arr[i], level + 1)
            else:
                arr[i] = re.sub("#;#", "\n" + '    ' * level, arr[i])
        return arr

    @staticmethod
    def flatten(l):
        for el in l:
            if isinstance(el, collections.abc.Iterable) and not isinstance(el, str):
                for sub in tpl.flatten(el):
                    yield sub
            else:
                yield el

    @staticmethod
    async def parse(kvml, context=None):
        kvml = re.sub(r'<:', '\r', kvml)
        kvml = re.sub(r'(?:^|:>)[^\r]*', tpl.re_sub_call, kvml)
        kvml = re.sub(r'(?:\r)=(.*?)(?::>)', r"\rwrite.append(\1):>", kvml)
        kvml = re.sub(r'\r', "''')#;#", kvml)
        kvml = re.sub(r':>', "#;#write.append('''", kvml)
        kvml = "write=[]\nwrite.append('''" + kvml + "''')"
        kvml = re.sub(r"\\", r"\\\\", kvml)
        kvml = re.sub("'", r"\'", kvml)
        kvml = re.sub(r"#{#", "''',['''", kvml)
        kvml = re.sub(r"#}#", "'''],'''", kvml)
        kvml = eval("['''" + kvml + "''']")
        kvml = tpl.recursive_indent(kvml, 0)
        kvml = list(tpl.flatten(kvml))
        kvml = ''.join(kvml)

        # Define exec environment and handle await as a string
        exec_env = context if context else {}
        kvml = textwrap.indent(kvml, ' ' * 4)
        kvml = f"""
#async def _temp_func(write):
#{kvml}"""

        kvml=f"""
async def _temp_func():
    write=[]
    write.append('''hello a''')
    response = await fetch("http://httpx.com")
    write.append(await response.text())
    write.append('hello')
    write.append('''''')
    return write"""

        exec(kvml, exec_env)
        write=await exec_env['_temp_func']()
        kvml = ''.join([str(x) for x in write])
        return kvml
