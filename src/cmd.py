import os
import shlex
import functools as ft
import subprocess as sp

from typing import (Union,
                    List,
                    Tuple,
                    Callable,
                    Set,
                    Optional,
                    Dict)
from pathlib import Path


def env_dict_to_str(env):
    return ' '.join([f'{k}={v}' for k, v in env])


class Cmd:

    def __init__(self,
                 cmd: List[str],
                 hooks: Optional[Tuple[Callable[['Cmd'],
                                                None],
                                       Callable[['Cmd', sp.CompletedProcess],
                                                None]]] = None,
                 name: str = '',
                 desc: str = '',
                 blocking: bool = True,
                 critical: bool = True,
                 keywords: Optional[Set[str]] = None,
                 env: Optional[Dict[str, str]] = None,
                 *args,
                 **kwargs):
        self.cmd = cmd
        self.desc = desc
        self.name = name or self.cmd
        self.blocking = blocking
        self.critical = critical
        self.env = env or {}
        self.keywords = keywords or set()
        self.process = ft.partial(
            sp.Popen,
            args=self.cmd,
            *args,
            **kwargs
        )

        self.before = lambda: None
        self.after = lambda: None
        if self.hooks:
            self.before, self.after = hooks

    def __call__(self, *args, **kwargs) -> sp.CompletedProcess:
        self.env: dict = kwargs.get('env', self.env)

        self.before(self)
        proc: sp.CompletedProcess = self.process(*args, **kwargs)
        if self.blocking:
            proc.wait()
        self.after(self, proc)
        return proc

    def __repr__(self) -> str:
        return f'{env_dict_to_str(self.env)} {self.cmd.join(" ")}'

    def __str__(self) -> str:
        return f'{self.name}: {self.desc}'


class ShellCmd(Cmd):

    def __init__(self, cmd: str, *args, **kwargs):
        super().__init__(shlex.split(cmd), *args, shell=True, **kwargs)


class Package(ShellCmd):

    package_use_dir = Path('/etc/portage/package.use')
    package_env_dir = Path('/etc/portage/package.env')
    package_mask_dir = Path('/etc/portage/package.use')
    package_accept_kwd = Path('/etc/portage/package.accept_keywords')

    def __init__(self,
                 package: str,
                 binary_alternative: str = '',
                 emerge_override: str = '',
                 use_flags: Union[List[str], str] = '',
                 extra_use_flags: Union[List[str], str] = '',
                 prefetch: bool = True,
                 *args,
                 **kwargs):
        self.emerge_override = emerge_override

        self.use_flags = use_flags
        if type(use_flags) == list:
            self.use_flags = ' '.join(use_flags)

        if not os.getenv('minimal'):
            if type(extra_use_flags) == list:
                self.use_flags = ' '.join([self.use_flags] + extra_use_flags)
            else:
                self.use_flags = f'{self.use_flags} {extra_use_flags}'

        self.package = package
        self.binary = False
        if os.getenv('binary') and binary_alternative:
            self.package = binary_alternative
            self.binary = True

        self.fs_friendly_name = self.package.replace('/', '.')
        self.cmd = f'emerge {self.emerge_override} {self.package}'

        if prefetch:
            self.hooks = [Package(package,
                                  '--fetchonly --deep',
                                  blocking=True,
                                  env={'USE': use_flags}),
                          lambda *args, **kwargs: None]

        super().__init__(
            self.cmd,
            name=package,
            critical=False,
            *args,
            **kwargs
        )

    def __call__(self, *args, **kwargs):
        if not self.binary:
            with open(self.package_use_dir / self.fs_friendly_name, 'a') as use:
                use.write(f'{self.package} {self.use_flags}')

        super().__call__(*args, **kwargs)


class IfKeyword:

    def __init__(self, keyword: str, if_true: Cmd, if_false: Optional[Cmd]):
        self.keyword = keyword
        self.if_true = if_true
        self.if_false = if_false

    def __call__(self, *args, **kwargs):
        if os.getenv(self.keyword):
            self.if_true(*args, **kwargs)
        elif self.if_false:
            self.if_false(*args, **kwargs)


class IfNotKeyword(IfKeyword):

    def __call__(self, *args, **kwargs):
        if not os.getenv(self.keyword):
            self.if_true(*args, **kwargs)
        elif self.if_false:
            self.if_false(*args, **kwargs)


class OptionalCommands:

    def __init__(self, clause: IfKeyword, keyword: str, commands: List[Cmd]):
        self.exec_list = [clause(keyword, cmd, None) for cmd in commands]

    def __call__(self, *args, **kwargs):
        for e in self.exec_list:
            e(*args, **kwargs)
