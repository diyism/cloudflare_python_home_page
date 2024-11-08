from js import Response

def on_fetch(request):
    res=Response.new(my_tpl())
    res.headers.set("Content-Type", "text/html; charset=utf-8")
    return res

def my_tpl():
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
    <p>Welcome to my python cloudflare worker.</p>
</body>
</html>
    """
    html = tpl.parse(kvml, context={"user_name": "jack"})
    return html

#================================python micro template:=================================
# Copyright (c) DIYism (email/msn/gtalk:kexianbin@diyism.com web:http://diyism.com)
# Licensed under GPL (http://www.opensource.org/licenses/gpl-license.php) license.
# Version: ke1r
# Document: https://github.com/diyism/python-micro-template/
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
    def parse(kvml, context=None):
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
        exec_env = context if context else {}
        exec(''.join(kvml), exec_env)
        kvml = ''.join([str(x) for x in exec_env['write']])
        return kvml
