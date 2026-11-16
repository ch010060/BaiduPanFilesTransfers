#!/usr/bin/env python3
"""BaiduPanFilesTransfers CLI 版本.

支持两种模式：
- save：批量转存链接。
- share：批量分享指定目录下的文件/文件夹。
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import List

from src.constants import EXP_MAP
from src.operations import Operations
from src.utils import read_config

DEFAULT_COOKIE_FILE = "cookies.txt"
DEFAULT_DOWNLOAD_FOLDER = "待下載/"


class _TextValue:
    """模拟 ttk.Entry 类似的字符串读取对象。"""

    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value


class _BoolValue:
    """模拟 ttk.BooleanVar 的 get 接口。"""

    def __init__(self, value: bool):
        self._value = bool(value)

    def get(self) -> bool:
        return self._value


class _TextBox:
    """极简文本框行为（仅保留逻辑需要的方法）。"""

    def __init__(self, initial: str = ''):
        self._value = initial

    def get(self, *_args, **_kwargs) -> str:
        return self._value

    def insert(self, index, text: str) -> None:
        del index  # 统一使用追加语义
        if text:
            self._value += text

    def delete(self, *_args, **_kwargs) -> None:
        self._value = ''

    def see(self, *_args, **_kwargs) -> None:
        return None

    def config(self, **_kwargs) -> None:
        return None


class _Button:
    """极简按钮占位对象，避免 GUI 层调用报错。"""

    def __init__(self):
        self.state = 'normal'
        self.command = None

    def config(self, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs['state']
        if 'command' in kwargs:
            self.command = kwargs['command']


class _Label:
    """极简状态标签占位对象。"""

    def __init__(self):
        self.text = ''

    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']

    def bind(self, *_args, **_kwargs) -> None:
        return None

    def unbind(self, *_args, **_kwargs) -> None:
        return None


class _CliContext:
    """提供与 UI 对象兼容的最小接口。"""

    def __init__(
        self,
        cookie: str,
        folder: str,
        trust_env: bool,
        custom_mode: bool,
        check_mode: bool,
        links: List[str],
    ):
        self.entry_cookie = _TextValue(cookie)
        self.entry_folder_name = _TextValue(folder)
        self.var_trust_env = _BoolValue(trust_env)
        self.var_custom_mode = _BoolValue(custom_mode)
        self.var_check_mode = _BoolValue(check_mode)

        self.text_links = _TextBox('\n'.join(links))
        self.text_logs = _TextBox('')

        self.bottom_share = _Button()
        self.bottom_save = _Button()
        self.label_status = _Label()


class CliOperations(Operations):
    """复用核心业务逻辑的 CLI 运行器。"""

    def __init__(self, root: _CliContext, expiry: str, password: str, random_password: bool):
        super().__init__(root)
        self.cli_expiry = expiry
        self.cli_password = password
        self.cli_random_password = random_password

    def insert_logs(self, message: str, alt: bool = False) -> None:
        """在 CLI 中同步输出日志，保持与 GUI 一致的文本记录。"""
        super().insert_logs(message, alt=alt)
        print(message)

    def share(self) -> None:
        """复用共享逻辑的分享流程，不再弹出 GUI 设置窗口。"""
        try:
            self.prepare_run()
            self.handle_input(task_count_check=False)
            self.handle_bdstoken()
            self.handle_list_dir()

            self.expiry = self.cli_expiry
            self.password = self.cli_password
            self.random_password = self.cli_random_password
            self.total_task_count = len(self.dir_list_all)
            self.change_status('sharing')

            self.handle_process_share()
        except Exception as e:
            self.insert_logs(f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}')
        finally:
            self.network.s.close()
            self.change_status('stopped')


def _collect_links(args) -> List[str]:
    links: List[str] = []

    if args.links_file:
        links_file = Path(args.links_file)
        if not links_file.exists():
            raise FileNotFoundError(f'链接文件不存在：{links_file}')
        links.extend(links_file.read_text(encoding='utf-8').splitlines())

    if args.links:
        links.extend(args.links)

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            links.extend(stdin_data.splitlines())

    normalized: List[str] = []
    for item in links:
        item = item.strip()
        if not item:
            continue

        # 支援使用者有時候複製時將 ?, =, & 以反斜線逃脫的情況（例如在 Markdown/聊天訊息中）
        item = item.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&').replace('\\%', '%')
        normalized.append(item)

    return [item for item in normalized if item]


def _load_config_defaults() -> tuple[str, str]:
    config = read_config()
    if not config:
        return '', DEFAULT_DOWNLOAD_FOLDER

    cookie = config[0] if len(config) > 0 else ''
    folder = config[1] if len(config) > 1 else DEFAULT_DOWNLOAD_FOLDER

    return cookie, folder


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    expiry_choices = list(EXP_MAP.keys())
    default_cookie, default_folder = _load_config_defaults()
    parser = argparse.ArgumentParser(
        description='BaiduPanFilesTransfers 命令行版本',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='''
用法示例：
  python BaiduPanFilesTransfersCLI.py save --links-file links.txt
  python BaiduPanFilesTransfersCLI.py share --folder 待下載/ --expiry 永久 --password 1234
        ''',
        prog='BaiduPanFilesTransfersCLI.py'
    )
    parser.add_argument('command', choices=['save', 'share'], help='运行模式：save(批量转存), share(批量分享)')

    parser.add_argument('--cookie', '-c', default='', help='可选：直接传入百度网盘 Cookie（优先级高于 cookies.txt）')
    parser.add_argument('--cookie-file', default=DEFAULT_COOKIE_FILE,
                        help=f'当未传 --cookie 时，读取该文件中的 cookie。默认：{DEFAULT_COOKIE_FILE}')
    parser.add_argument('--folder', '-f', default=default_folder, help=f'转存/分享目标目录（默认：{DEFAULT_DOWNLOAD_FOLDER}）')

    parser.add_argument('--trust-env', action='store_true', help='是否使用系统代理')
    parser.add_argument('--custom', action='store_true', help='是否开启指定目录模式')
    parser.add_argument('--check', action='store_true', help='转存时仅检测链接有效性，不执行转存')

    parser.add_argument('--expiry', choices=expiry_choices, default=expiry_choices[-1],
                        help='分享时的链接有效期，默认：永久')
    parser.add_argument('--password', default='1234', help='分享密码')
    parser.add_argument('--random-password', action='store_true', help='分享时自动生成随机4位密码')

    parser.add_argument('--links-file', help='链接文件路径（每行一个链接）')
    parser.add_argument('--links', action='append', default=[], help='逐条指定链接，可重复使用')

    return parser.parse_args(argv)


def _load_cookie_from_file(path: str) -> str:
    cookie_file = Path(path)
    if not cookie_file.exists():
        return ''

    raw_lines = cookie_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    lines = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith('#')]
    return next((line for line in lines if line), '')


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    default_cookie, _ = _load_config_defaults()

    cookie = args.cookie.strip()
    if not cookie:
        cookie = _load_cookie_from_file(args.cookie_file)
    if not cookie:
        cookie = default_cookie.strip()

    if not cookie:
        print('错误：--cookie 未提供，且 config.ini 也未记录 cookie。', file=sys.stderr)
        return 1

    links = _collect_links(args)

    if args.command == 'save' and not links:
        print('错误：save 模式至少需要输入一个链接（可用 --links、--links-file，或通过 stdin）。', file=sys.stderr)
        return 1

    root = _CliContext(
        cookie=cookie,
        folder=args.folder,
        trust_env=args.trust_env,
        custom_mode=args.custom,
        check_mode=args.check,
        links=links,
    )

    op = CliOperations(root=root, expiry=args.expiry, password=args.password, random_password=args.random_password)

    try:
        if args.command == 'save':
            op.save()
        else:
            op.share()
    except SystemExit:
        print(f'执行摘要：成功 {op.success_count} / 失败 {op.fail_count}')
        raise

    print(f'执行摘要：成功 {op.success_count} / 失败 {op.fail_count}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
