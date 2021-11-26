import base64
import tempfile
import threading
import time
import webbrowser
import zlib
import os
import re
# noinspection PyCompatibility
from tkinter import *

import requests
import urllib3
from retrying import retry

'''
軟體名: BaiduPanFilesTransfers
版本: 1.9
更新時間: 2021.05.09
打包命令: pyinstaller -F -w -i bpftUI.ico bpftUI.py
'''

# 實例化TK
root = Tk()

# 執行時替換圖示
ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBysAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))
_, ICON_PATH = tempfile.mkstemp()
with open(ICON_PATH, 'wb') as icon_file:
    icon_file.write(ICON)
root.iconbitmap(default=ICON_PATH)

# 主視窗配置
root.wm_title("度盤轉存 2.0 by Alice & Asu & Roger")
root.wm_geometry('350x473+240+240')
root.wm_attributes("-alpha", 0.91)
root.resizable(width=False, height=False)

# 定義標籤和文字框
Label(root, text='1.下面填入百度Cookies,不帶引號').grid(row=1, column=0, sticky=W)
entry_cookie = Entry(root, width=48, )
entry_cookie.grid(row=2, column=0, sticky=W, padx=4)
Label(root, text='2.下面填入瀏覽器User-Agent').grid(row=3, column=0, sticky=W)
entry_ua = Entry(root, width=48, )
entry_ua.grid(row=4, column=0, sticky=W, padx=4)
Label(root, text='3.下面填入檔案儲存位置(預設根目錄),不能包含<,>,|,*,?,,/').grid(row=5, column=0, sticky=W)
entry_folder_name = Entry(root, width=48, )
entry_folder_name.grid(row=6, column=0, sticky=W, padx=4)
Label(root, text='4.下面貼上鏈接,每行一個,格式為:鏈接 提取碼.支援秒傳格式.').grid(row=7, sticky=W)

# 鏈接輸入框
text_links = Text(root, width=48, height=10, wrap=NONE)
text_links.grid(row=8, column=0, sticky=W, padx=4, )
scrollbar_links = Scrollbar(root, width=5)
scrollbar_links.grid(row=8, column=0, sticky=S + N + E, )
scrollbar_links.configure(command=text_links.yview)
text_links.configure(yscrollcommand=scrollbar_links.set)

# 日誌輸出框
text_logs = Text(root, width=48, height=10, wrap=NONE)
text_logs.grid(row=10, column=0, sticky=W, padx=4, )
scrollbar_logs = Scrollbar(root, width=5)
scrollbar_logs.grid(row=10, column=0, sticky=S + N + E, )
scrollbar_logs.configure(command=text_logs.yview)
text_logs.configure(yscrollcommand=scrollbar_logs.set)

# 定義按鈕和狀態標籤
bottom_run = Button(root, text='4.點選執行', command=lambda: thread_it(main, ), width=10, height=1, relief='solid')
bottom_run.grid(row=9, pady=6, sticky=W, padx=4)
label_state = Label(root, text='檢查新版', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
label_state.grid(row=9, sticky=E, padx=4)
label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers", new=0))

# 讀取配置
if os.path.exists('config.ini'):
    with open('config.ini') as config_read:
        [config_cookie, config_user_agent] = config_read.readlines()
    entry_cookie.insert(0, config_cookie)
    entry_ua.insert(0, config_user_agent)

# 公共請求頭
request_header = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
urllib3.disable_warnings()
s = requests.session()


# 獲取bdstoken函式
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_bdstoken():
    url = 'https://pan.baidu.com/disk/home'
    response = s.get(url=url, headers=request_header, timeout=20, allow_redirects=True, verify=False)
    # bdstoken_list = re.findall("'bdstoken',\\s'(\\S+?)'", response.text)
    bdstoken_list = re.findall('"bdstoken":"(\\S+?)"', response.text)
    return bdstoken_list[0] if bdstoken_list else 1


# 獲取目錄列表函式
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_dir_list(bdstoken):
    url = 'https://pan.baidu.com/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken=' + bdstoken
    response = s.get(url=url, headers=request_header, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']


# 新建目錄函式
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def create_dir(dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/create?a=commit&bdstoken=' + bdstoken
    post_data = {'path': dir_name, 'isdir': '1', 'block_list': '[]', }
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno']


# 檢測鏈接種類
def check_link_type(link_list_line):
    if link_list_line.find('https://pan.baidu.com/s/') >= 0:
        link_type = '/s/'
    elif bool(re.search('(bdlink=|bdpan://|BaiduPCS-Go)', link_list_line, re.IGNORECASE)):
        link_type = 'rapid'
    elif link_list_line.count('#') > 2:
        link_type = 'rapid'
    else:
        link_type = 'unknown'
    return link_type


# 驗證鏈接函式
@retry(stop_max_attempt_number=20, wait_fixed=2000)
def check_links(link_url, pass_code, bdstoken):
    # 驗證提取碼
    if pass_code:
        # 產生時間戳
        t_str = str(int(round(time.time() * 1000)))
        check_url = 'https://pan.baidu.com/share/verify?surl=' + link_url[25:48] + '&bdstoken=' + bdstoken + '&t=' + t_str + '&channel=chunlei&web=1&clienttype=0'
        post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
        response_post = s.post(url=check_url, headers=request_header, data=post_data, timeout=10, allow_redirects=False,
                               verify=False)
        # 在cookie中加入bdclnd參數
        if response_post.json()['errno'] == 0:
            bdclnd = response_post.json()['randsk']
        else:
            return response_post.json()['errno']
        if bool(re.search('BDCLND=', request_header['Cookie'], re.IGNORECASE)):
            request_header['Cookie'] = re.sub(r'BDCLND=(\S+?);', r'BDCLND=' + bdclnd + ';', request_header['Cookie'])
        else:
            request_header['Cookie'] += '; BDCLND=' + bdclnd
    # 獲取檔案資訊
    response = s.get(url=link_url, headers=request_header, timeout=15, allow_redirects=True,
                     verify=False).content.decode("utf-8")
    shareid_list = re.findall('"shareid":(\\d+?),"', response)
    user_id_list = re.findall('"share_uk":"(\\d+?)","', response)
    fs_id_list = re.findall('"fs_id":(\\d+?),"', response)
    if not shareid_list:
        return 1
    elif not user_id_list:
        return 2
    elif not fs_id_list:
        return 3
    else:
        return [shareid_list[0], user_id_list[0], fs_id_list]


# 轉存檔案函式
@retry(stop_max_attempt_number=200, wait_fixed=2000)
def transfer_files(check_links_reason, dir_name, bdstoken):
    url = 'https://pan.baidu.com/share/transfer?shareid=' + check_links_reason[0] + '&from=' + check_links_reason[
        1] + '&bdstoken=' + bdstoken + '&channel=chunlei&web=1&clienttype=0'
    fs_id = ','.join(i for i in check_links_reason[2])
    post_data = {'fsidlist': '[' + fs_id + ']', 'path': '/' + dir_name, }
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False,
                      verify=False)
    return response.json()


# 轉存秒傳鏈接函式
@retry(stop_max_attempt_number=100, wait_fixed=1000)
def transfer_files_rapid(rapid_data, dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/rapidupload?bdstoken=' + bdstoken
    post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0],
                 'slice-md5': rapid_data[1], 'content-length': rapid_data[2]}
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    if response.json()['errno'] == 404:
        post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0].lower(),
                     'slice-md5': rapid_data[1].lower(), 'content-length': rapid_data[2]}
        response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False,
                          verify=False)
    return response.json()['errno']


# 狀態標籤變化函式
def label_state_change(state, task_count=0, task_total_count=0):
    label_state.unbind("<Button-1>")
    label_state['font'] = ('Arial', 9)
    label_state['foreground'] = "#000000"
    label_state['cursor'] = "arrow"
    if state == 'error':
        label_state['text'] = '發生錯誤,錯誤日誌如下:'
    elif state == 'running':
        label_state['text'] = '下面為轉存結果,進度:' + str(task_count) + '/' + str(task_total_count)


# 多執行緒
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
    # t.join()

# modified main
def main():
    # modify text_input
    text_logs.insert(END, '=== 轉存開始 ===' + '\n')
    text_input = text_links.get(1.0, END).split('\n')
    link_list = [link for link in text_input if link]
    link_list = [link + ' ' for link in link_list]
    task_count = 0
    task_total_count = len(link_list)
    for i, link in enumerate(link_list):
        text_logs.insert(END, f'({i+1}/{len(link_list)})' + '\n')
        _main([link])
        task_count = task_count + 1
        label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)


# 主程式
def _main(link_list):
    # 獲取和初始化數據
    dir_name = "".join(entry_folder_name.get().split())
    cookie = "".join(entry_cookie.get().split())
    request_header['Cookie'] = cookie
    user_agent = entry_ua.get()
    request_header['User-Agent'] = user_agent
    with open('config.ini', 'w') as config_write:
        config_write.write(cookie + '\n' + user_agent)

    bottom_run['state'] = 'disabled'
    bottom_run['relief'] = 'groove'
    bottom_run['text'] = '執行中...'

    # 開始執行函式
    try:
        # 檢查cookie輸入是否正確
        if cookie.find('BAIDUID=') == -1:
            label_state_change(state='error')
            text_logs.insert(END, '百度網盤cookie輸入不正確,請檢查cookie後重試.' + '\n')
            sys.exit()
        
        if any([ord(word) not in range(256) for word in cookie]):
            label_state_change(state='error')
            text_logs.insert(END, '百度網盤cookie中帶非法字元,請檢查cookie後重試.' + '\n')
            sys.exit()

        # 執行獲取bdstoken
        bdstoken = get_bdstoken()
        if bdstoken == 1:
            label_state_change(state='error')
            text_logs.insert(END, '沒獲取到bdstoken,請檢查cookie和網路後重試.' + '\n')
            sys.exit()

        # 執行獲取目錄列表
        dir_list_json = get_dir_list(bdstoken)
        if type(dir_list_json) != list:
            label_state_change(state='error')
            text_logs.insert(END, '沒獲取到網盤目錄列表,請檢查cookie和網路後重試.' + '\n')
            sys.exit()

        # 執行新建目錄
        dir_list = [dir_json['server_filename'] for dir_json in dir_list_json]
        if dir_name and dir_name not in dir_list:
            create_dir_reason = create_dir(dir_name, bdstoken)
            if create_dir_reason != 0:
                label_state_change(state='error')
                text_logs.insert(END, '資料夾名帶非法字元,請改正資料夾名稱後重試.' + '\n')
                sys.exit()

        # 執行轉存
        for url_code in link_list:
            # 處理舊格式鏈接
            url_code = url_code.replace("https://pan.baidu.com/share/init?surl=", "https://pan.baidu.com/s/1")
            # 判斷連線型別
            link_type = check_link_type(url_code)
            # 處理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg lice)格式鏈接
            if link_type == '/s/':
                link_url, pass_code = re.sub(r'提取碼*[：:](.*)', r'\1', url_code.lstrip()).split(' ', maxsplit=1)
                pass_code = pass_code.strip()[:4]
                # 執行檢查鏈接有效性
                check_links_reason = check_links(link_url, pass_code, bdstoken)
                if check_links_reason == 1:
                    text_logs.insert(END, '鏈接失效,沒獲取到shareid:' + url_code + '\n')
                elif check_links_reason == 2:
                    text_logs.insert(END, '鏈接失效,沒獲取到user_id:' + url_code + '\n')
                elif check_links_reason == 3 or check_links_reason == -9:
                    text_logs.insert(END, '鏈接失效,檔案已經被刪除或取消分享:' + url_code + '\n')
                elif check_links_reason == -12:
                    text_logs.insert(END, '提取碼錯誤:' + url_code + '\n')
                elif check_links_reason == -62:
                    text_logs.insert(END, '錯誤嘗試次數過多,請稍後再試:' + url_code + '\n')
                elif isinstance(check_links_reason, list):
                    # 執行轉存檔案
                    transfer_files_reason = transfer_files(check_links_reason, dir_name, bdstoken)
                    if transfer_files_reason['errno'] == 0:
                        text_logs.insert(END, '轉存成功:' + url_code + '\n')
                    elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == -30:
                        text_logs.insert(END, '轉存失敗,目錄中已有同名檔案存在:' + url_code + '\n')
                    elif transfer_files_reason['errno'] == 12 and transfer_files_reason['info'][0]['errno'] == 120:
                        text_logs.insert(END, '轉存失敗,轉存檔案數超過限制:' + url_code + '\n')
                    else:
                        text_logs.insert(END,
                                         '轉存失敗,錯誤程式碼(' + str(transfer_files_reason['errno']) + '):' + url_code + '\n')
                else:
                    text_logs.insert(END, '訪問鏈接返回錯誤程式碼(' + str(check_links_reason) + '):' + url_code + '\n')
            # 處理秒傳格式鏈接
            elif link_type == 'rapid':
                # 處理夢姬標準(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒傳.rar)
                if url_code.count('#') > 2:
                    rapid_data = url_code.split('#', maxsplit=3)
                # 處理遊俠 v1標準(bdlink=)
                elif bool(re.search('bdlink=', url_code, re.IGNORECASE)):
                    rapid_data = base64.b64decode(re.findall(r'bdlink=(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('#', maxsplit=3)
                # 處理PanDL標準(bdpan://)
                elif bool(re.search('bdpan://', url_code, re.IGNORECASE)):
                    bdpan_data = base64.b64decode(re.findall(r'bdpan://(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('|')
                    rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
                # 處理PCS-Go標準(BaiduPCS-Go)
                elif bool(re.search('BaiduPCS-Go', url_code, re.IGNORECASE)):
                    go_md5 = re.findall(r'-md5=(\S+)', url_code)[0]
                    go_md5s = re.findall(r'-slicemd5=(\S+)', url_code)[0]
                    go_len = re.findall(r'-length=(\S+)', url_code)[0]
                    go_name = re.findall(r'-crc32=\d+\s(.+)', url_code)[0].replace('"', '').replace('/', '\\').strip()
                    rapid_data = [go_md5, go_md5s, go_len, go_name]
                else:
                    rapid_data = []
                transfer_files_reason = transfer_files_rapid(rapid_data, dir_name, bdstoken)
                if transfer_files_reason == 0:
                    text_logs.insert(END, '轉存成功:' + url_code + '\n')
                elif transfer_files_reason == -8:
                    text_logs.insert(END, '轉存失敗,目錄中已有同名檔案存在:' + url_code + '\n')
                elif transfer_files_reason == 404:
                    text_logs.insert(END, '轉存失敗,秒傳無效:' + url_code + '\n')
                elif transfer_files_reason == 2:
                    text_logs.insert(END, '轉存失敗,非法路徑:' + url_code + '\n')
                elif transfer_files_reason == -7:
                    text_logs.insert(END, '轉存失敗,非法檔名:' + url_code + '\n')
                elif transfer_files_reason == -10:
                    text_logs.insert(END, '轉存失敗,容量不足:' + url_code + '\n')
                elif transfer_files_reason == 114514:
                    text_logs.insert(END, '轉存失敗,介面呼叫失敗:' + url_code + '\n')
                else:
                    text_logs.insert(END, '轉存失敗,錯誤程式碼(' + str(transfer_files_reason) + '):' + url_code + '\n')
            elif link_type == 'unknown':
                text_logs.insert(END, '不支援鏈接:' + url_code + '\n')
    except Exception as e:
        text_logs.insert(END, '執行出錯,請重新執行本程式.錯誤資訊如下:' + '\n')
        text_logs.insert(END, str(e) + '\n\n')
        text_logs.insert(END, '使用者輸入內容:' + '\n')
        text_logs.insert(END, '百度Cookies:' + cookie + '\n')
        text_logs.insert(END, '資料夾名:' + dir_name + '\n')
        text_logs.insert(END, '鏈接輸入:' + '\n' + str(text_input))
    # 恢復按鈕狀態
    finally:
        bottom_run['state'] = 'normal'
        bottom_run['relief'] = 'solid'
        bottom_run['text'] = '4.點選執行'


root.mainloop()
