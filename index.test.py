async def python_home_page():
    kvml = """
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
    <:response = fetch("http://httpx.com"); write.append(await response.text()):>
</body>
</html>
    """
    user_name="jack"
    html = await tpl.parse(kvml, context=globals())
    return html

#===========cloudflare request and response================
from js import Response, fetch
import asyncio
async def on_fetch(request):
    res = Response.new(await python_home_page())
    res.headers.set("Content-Type", "text/html; charset=utf-8")
    return res

#===========python micro template:=================================
import re
import collections.abc
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
        wrapped_code = f"""
async def _temp_func(write):
    response = await fetch("http://httpx.com")
    write.append(await response.text())
    write.append('hello')
        """
        
        # Execute in a local scope
        exec_env['write'] = []
        exec(wrapped_code, exec_env)
        
        # Await for the async function
        await exec_env['_temp_func'](exec_env['write'])
        kvml = ''.join([str(x) for x in exec_env['write']])
        return kvml
