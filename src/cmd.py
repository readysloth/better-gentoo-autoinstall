import shlex
import functools as ft
import subprocess as sp

from typing import Union, List, Tuple, Callable
from pathlib import Path


def env_dict_to_str(env):
    return ' '.join([f'{k}={v}' for k, v in env])


class Cmd:
    def __init__(self,
                 cmd: List[str],
                 hooks: Tuple[Callable[['Cmd'], None],
                              Callable['Cmd', sp.CompletedProcess], None] = None,
                 name: str = '',
                 desc: str = '',
                 blocking: bool = True,
                 critical: bool = True,
                 *args,
                 **kwargs):
        self.cmd = cmd
        self.name = name
        self.desc = desc
        self.blocking = blocking
        self.critical = critical
        self.env = kwargs.get('env', {})
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


class EmergeCmd(ShellCmd):

    package_use_dir = Path('/etc/portage/package.use')
    package_env_dir = Path('/etc/portage/package.env')
    package_mask_dir = Path('/etc/portage/package.use')
    package_accept_kwd = Path('/etc/portage/package.accept_keywords')

    def __init__(self,
                 package: str,
                 emerge_override: str = '',
                 use_flags: Union[List[str], str] = '',
                 prefetch: bool = True,
                 *args,
                 **kwargs):
        self.emerge_override = emerge_override
        self.use_flags = use_flags
        self.fs_friendly_name = self.package.replace('/', '.')
        if type(use_flags) == list:
            self.use_flags = ' '.join(use_flags)

        if prefetch:
            self.hooks = [EmergeCmd(package,
                                    '--fetchonly --deep',
                                    blocking=True,
                                    env={'USE': use_flags}),
                          lambda *args, **kwargs: None]

        super().__init__(
            name=package,
            critical=False,
            *args,
            **kwargs
        )

    def __call__(self, *args, **kwargs):
        with open(self.package_use_dir / self.fs_friendly_name, 'a') as use:
            use.write(f'{self.package} {self.use_flags}')

        super().__call__(*args, **kwargs)
