import codecs

# 读取原文件内容
try:
    with open('installer_utf8.nsi', 'r', encoding='utf-8-sig') as f:
        content = f.read()
except UnicodeDecodeError:
    try:
        with open('installer_utf8.nsi', 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open('installer_utf8.nsi', 'r') as f:
            content = f.read()

# 去掉可能存在的 Unicode true 之前的 BOM 或空白
content = content.strip()
if not content.startswith('Unicode true'):
    # 确保 Unicode true 在第一行
    lines = content.splitlines()
    if 'Unicode true' in lines[0]:
        pass # 已经在第一行
    else:
        # 如果第一行不是 Unicode true，检查是否有这一行，有则移到第一行，没有则添加
        pass # 暂时假设内容是正确的

# 以 utf-8 (无 BOM) 写入
with open('installer_utf8.nsi', 'w', encoding='utf-8') as f:
    f.write(content)

print("File converted to UTF-8 without BOM")