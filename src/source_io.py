"""源码读取：把文件/字节流解码成程序文本。"""


def decode(data):
    """按 UTF-8 解码，失败时回退到 GB18030（兼容 GBK 编写的中文注释）。"""
    for encoding in ("utf-8", "gb18030"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
    # 去掉编辑器可能写入的 BOM，否则它会变成一个陌生符号
    if text.startswith("\ufeff"):
        text = text[1:]
    return text


def read_text(path):
    """读入一个源码文件。"""
    with open(path, "rb") as handle:
        return decode(handle.read())
