import os
import re
import smtplib
import urllib.parse
import urllib.request
import zipfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from urllib.error import HTTPError

from lxml import etree


# 抓取 wallhaven 图片,压缩为 zip 文件,发送到邮箱\
#
# 安装 lxml
# pip3 install lxml
#
# 后台运行脚本并输出打印信息到指定日志
# nohup 不显示输出 -u 立即刷新日志缓冲 > ?.log 输出日志 2>&1 将打印信息输出到日志 & 后台运行
# nohup python3 -u wallHavenPicture.py > wallHavenPicture.py.log 2>&1 &

# 指定页数下载 wallhaven 图片
def download_picture(end_page):
    dir_path = None
    # 因为网页起始索引为 2, 所以加 2
    for page in range(2, end_page + 2):
        # 请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/72.0.3626.119 Safari/537.36 '
        }
        # 访问地址
        url = 'https://wallhaven.cc/search?categories=010&purity=100&sorting=date_added&order=desc&page={}'.format(page)
        print(url + ' downloading')
        # 发送请求
        request = urllib.request.Request(url=url, headers=headers)
        # 获取响应
        response = urllib.request.build_opener().open(request)
        # 获取相应 HTML 文档
        html = etree.HTML(response.read().decode())
        # 获取图片缩略图链接
        data_src = html.xpath('//img//@data-src')

        # 保存路径为域名
        dir_path = re.compile(r'[^a-zA-Z:/]?\w+.[a-zA-Z]*').findall(url)[1]
        # 如果文件夹不存在则创建
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        # 遍历图片链接数组
        for i in range(len(data_src)):
            # 匹配获取图片链接
            re_picture = '{}/wallhaven-{}.{}'.format(re.compile(r'\w+').findall(data_src[i])[5],
                                                     re.compile(r'\w+').findall(data_src[i])[6],
                                                     re.compile(r'\w+').findall(data_src[i])[7])
            # 拼接下载图片路径
            data_src[i] = 'https://w.wallhaven.cc/full/' + re_picture

            # 默认图片 jpg 格式
            try:
                # 根据 xpath 匹配到的链接发送请求
                request = urllib.request.Request(url=data_src[i], headers=headers)
                response = urllib.request.build_opener().open(request)
                print(data_src[i] + ' downloading')
            # 发生错误则为 png 格式
            except HTTPError:
                # 拼接下载图片路径
                data_src[i] = 'https://w.wallhaven.cc/full/' + re_picture.replace('jpg', 'png')
                # 根据 xpath 匹配到的链接发送请求
                request = urllib.request.Request(url=data_src[i], headers=headers)
                # 获取响应
                response = urllib.request.build_opener().open(request)
                print(data_src[i] + ' downloading')

            # 根据链接设置文件名
            base_name = os.path.basename(data_src[i])
            # 根据当前 python 文件路径设置下载路径
            path = os.path.join(dir_path, base_name)
            # 向指定路径写入文件
            with open(path, 'wb') as fp:
                fp.write(response.read())
    print("download finish.")

    # 下载完压缩图片文件夹
    zip_file(dir_path)

    # 发送压缩文件到邮箱
    send_mail(dir_path + '.zip')


# 向 qq 邮箱发送下载好的图片
def send_mail(zip_path):
    # 发件人
    sender = '1223684476@qq.com'
    # 接收人
    receiver = ['1223684476@qq.com']
    # 设置发送 MIME 多媒体文件格式为 MIMEMultipart
    message = MIMEMultipart()
    message['From'] = Header(sender, 'utf-8')
    message['To'] = Header(receiver[0], 'utf-8')
    message['Subject'] = Header('WallHaven picture', 'utf-8')

    # 发送 html 代码
    mail_html = '''
     <h1>WallHaven picture download finish</h1>
     '''
    # 附加 html 代码到发送消息中
    message.attach(MIMEText(mail_html, 'html', 'utf-8'))

    # 发送附件(文件)
    mail_file = MIMEText(open(zip_path, 'rb').read(), 'base64', 'utf-8')
    # 设置内容类型为八进制字节流
    mail_file["Content-Type"] = 'application/octet-stream'
    # 附件描述
    mail_file["Content-Disposition"] = 'filename="{}"'.format(zip_path)
    # 附加文件到发送消息中
    message.attach(mail_file)

    try:
        # 设置 smtp 服务器与端口
        smtp = smtplib.SMTP('smtp.qq.com', 587)
        # 使用发件人邮箱名与授权码登录邮件服务器
        # 授权码在 qq邮箱 -> 设置 -> 账户 -> POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
        # -> 生成授权码同时开启 POP3/SMTP 服务与 IMAP/SMTP 服务
        smtp.login(sender, 'bjtscqbownxcjdbc')
        # 发送邮件
        smtp.sendmail(sender, receiver, message.as_string())
        # 发送成功提示
        print("Successfully sent email")
    except smtplib.SMTPException as e:
        # 当 ip 发送过多时, qq 邮箱服务器会拒绝接收,可以重连下宽带,更改 ip
        # 发送失败提示
        print(e)


# 压缩指定文件夹为 zip 压缩文件到当前目录
def zip_file(folders):
    # 压缩文件名
    zip_name = folders + '.zip'
    # 设置压缩文件名,访问模式,压缩类型为 ZIP_DEFLATED 无损数据压缩
    zip_files = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    # 遍历指定文件夹目录
    for path, name, file in os.walk(folders):
        # 遍历文件夹目录内文件名
        for i in file:
            # 获取当前路径与文件名并创建压缩文件
            zip_files.write(os.path.join(path, i), i)
    # 关闭文件流
    zip_files.close()
    print('zip done')


# 执行函数
def run():
    download_picture(100)


if __name__ == '__main__':
    run()
