pyml = """
<:
data={}
if "form" in (request.headers.get("Content-Type") or ""):
    form = await request.formData()
    data = dict(form.entries())

async def send_message(user_message):
    url = "https://api.x.ai/v1/chat/completions"
    #url = "https://httpbin.org/anything"
    # get the xai grok key from: https://console.x.ai/
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer xai-...."
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": user_message}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }

    response = await fetch(url, py_to_js({
        "method": "POST",
        "headers": headers,
        "body": json.dumps(payload)
    }))
    #result = await response.text()
    #return result+"hello"
    result = await response.json()
    result=result.to_py()
    return result["choices"][0]["message"]["content"]

result=""
user_input=""
if "user_input" in data:
    user_input=data.get("user_input")
    result=await send_message(user_input)
:>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xAI Grok Chat</title>
</head>
<body>
    <h1>xAI Grok Chatbot</h1>

    <form method="post">
        <textarea name="user_input"  rows="10" cols="100" placeholder="Enter your question here" required></textarea>
        <button type="submit">Send</button>
    </form>
    <div id="chat_thread">
        <p>Chat conversation will appear here...</p>
        <p><strong>User:</strong> <:=user_input:></p>
        <p><strong>xAI Grok:</strong> <textarea readonly rows="20" cols="100"><:=result:></textarea></p>
    </div>
</body>
</html>
"""

#===========cloudflare request and response================
from js import Object, Response, fetch, console
import asyncio, json
async def on_fetch(request):
    context = globals()
    context['request'] = request
    res = Response.new(await tpl.parse(context))
    res.headers.set("Content-Type", "text/html; charset=utf-8")
    return res

from pyodide.ffi import to_js
def py_to_js(obj):
    return to_js(obj, dict_converter=Object.fromEntries)

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
