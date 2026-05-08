import os

print("aaa" \
      "bbb" \
        "ccc")

print(os.environ)


import math
def mask(text:str) -> str:
    # 8文字までは全文字をマスクかつ8桁固定
    if len(text) <= 8:
        return "*" * 8

    # それ以上の場合は、文字数の15%または3文字の少ないほうを上限として
    # 先頭のみオープン。文字数は30文字を上限にする。
    gen_len:int = min(math.floor(len(text)*0.15), 3)
    max_len:int = min(len(text), 30)
    ret = (text[0:gen_len] + ("*" * max_len))[:max_len]
    return ret


print(mask("a"))
print(mask("abcdef"))
print(mask("fgawui2"))
print(mask("fgawui21"))
print(mask("fgawui21s"))
print(mask("fgawui234;"))
print(mask("fgawui234;gwer"))
print(mask("fgawui234;oghbws.j"))
print(mask("fgawui234;oghbjljnews.j3hu5"))
print(mask("fgawui234;oghbjljnews.j3hbj43oiihygu5123134546461456"))



