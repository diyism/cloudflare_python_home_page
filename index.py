pyml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<body>
<:user_name="jack123"
:>
    <h1>Hello, <:for i in range(2):#{#:><:=user_name:>,<:#}#:>!</h1>
    <p>Welcome to my cloudflare python home page.</p>
<:response = await fetch("http://httpx.com")
html=await response.text()
matches = re.search(r"<h2[^>]*>Your IP Address</h2>.*?<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
if matches:
    ip_address = matches.group(1).strip()
    text_content = f"Cloudflare IP Address: {ip_address}"
    write.append(text_content)
else:
    write.append("IP Address not found.")
:>
</body>
</html>
"""

#===========cloudflare request and response================
from js import Response, fetch, console
import asyncio
async def on_fetch(request):
    res = Response.new(await tpl.parse(globals()))
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
    async def parse(context):
        #return context['pyml']
        pyml=context['pyml']
        pyml = re.sub(r'<:', '\r', pyml)
        pyml = re.sub(r'(?:^|:>)[^\r]*', tpl.re_sub_call, pyml)
        pyml = re.sub(r'(?:\r)=(.*?)(?::>)', r"\rwrite.append(\1):>", pyml)
        pyml = re.sub(r'\r', "''')#;#", pyml)
        pyml = re.sub(r':>', "#;#write.append('''", pyml)
        pyml = "write=[]\nwrite.append('''" + pyml + "''')\nreturn write"
        pyml = re.sub(r"\\", r"\\\\", pyml)
        pyml = re.sub("'", r"\'", pyml)
        pyml = re.sub(r"#{#", "''',['''", pyml)
        pyml = re.sub(r"#}#", "'''],'''", pyml)
        pyml = eval("['''" + pyml + "''']")
        pyml = tpl.recursive_indent(pyml, 0)
        pyml = list(tpl.flatten(pyml))
        pyml = ''.join(pyml)

        pyml = textwrap.indent(pyml, ' ' * 4)
        pyml = f"""
async def _temp_func():
{pyml}"""

        exec(pyml, context)
        write=await context['_temp_func']()
        pyml = ''.join([str(x) for x in write])
        return pyml
