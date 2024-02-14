import os
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
    return ' '.join([f'{k}="{v}"' for k, v in env.items()])


class PythonCall:

    def __init__(self,
                 callback,
                 *args,
                 equivalent: str = '',
                 blocking: bool = True,
                 critical: bool = True,
                 **kwargs):
        self.callback = ft.partial(callback, *args, **kwargs)
        self.equivalent = equivalent

    def __call__(self, *args, pretend: bool = False, **kwargs):
        if pretend:
            return sp.CompletedProcess(self.equivalent, returncode=0)
        return self.callback(*args, **kwargs)

    def __repr__(self):
        return self.equivalent

    def __str__(self):
        if self.desc:
            return f'{self.name}: {self.desc}'
        return self.name


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
                 ignore_change: bool = False,
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
        self.ignore_change = ignore_change
        self.process = ft.partial(
            sp.Popen,
            *args,
            **kwargs
        )

        self.hooks = hooks
        self.before = lambda *args, **kwargs: None
        self.after = lambda *args, **kwargs: None
        if self.hooks:
            self.before, self.after = hooks

    def append(self, *args):
        if self.ignore_change:
            return
        self.cmd += args

    def insert(self, index, *args):
        if self.ignore_change:
            return
        for i in enumerate(args):
            self.cmd.insert(index + i, args[i])

    def __call__(self,
                 *args,
                 pretend: bool = False,
                 **kwargs) -> sp.CompletedProcess:
        self.env: dict = kwargs.get('env', self.env)

        if pretend:
            return sp.CompletedProcess(self.cmd, returncode=0)

        self.before(self)
        proc: sp.CompletedProcess = self.process(*args, args=self.cmd, **kwargs)
        if self.blocking:
            proc.wait()
        self.after(self, proc)
        return proc

    def __repr__(self) -> str:
        if not self.env:
            return " ".join(self.cmd)
        return f'{env_dict_to_str(self.env)} {" ".join(self.cmd)}'

    def __str__(self) -> str:
        if self.desc:
            return f'{self.name}: {self.desc}'
        return self.name


class ShellCmd(Cmd):

    def __init__(self, cmd: str, *args, **kwargs):
        super().__init__([cmd], *args, shell=True, **kwargs)

    def append(self, *args):
        if self.ignore_change:
            return
        self.cmd = [' '.join(self.cmd + list(args))]

    def insert(self, cmd_part: str):
        if self.ignore_change:
            return
        self.cmd = [self.cmd[0].replace('%placeholder%', cmd_part)]


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
        self.useflags_file = self.package_use_dir / self.fs_friendly_name
        self.cmd = f'emerge {self.emerge_override} {self.package}'

        hooks = []
        if prefetch:
            hooks = [Package(self.package,
                             emerge_override='--fetchonly --deep',
                             blocking=True,
                             prefetch=False,
                             env={'USE': self.use_flags}),
                     lambda *args, **kwargs: None]

            self.cmd = f'echo "{self.package}" >> /var/lib/portage/world'

        super().__init__(
            self.cmd,
            name=package,
            desc=self.use_flags,
            critical=False,
            hooks=hooks,
            *args,
            **kwargs
        )

    def __call__(self, *args, pretend: bool = False, **kwargs) -> Union[List[sp.CompletedProcess],
                                                                        sp.CompletedProcess]:
        if pretend:
            return [self.before(pretend=True),
                    super().__call__(*args, pretend=pretend, **kwargs),
                    self.after(pretend=True)]

        if not self.binary:
            with open(self.useflags_file, 'a') as use:
                use.write(f'{self.package} {self.use_flags}')

        if self.blocking:
            return super().__call__(*args, **kwargs)

    def __repr__(self):
        commands = []
        if not self.emerge_override:
            commands.append(f'echo "{self.package} {self.use_flags}" >> {self.useflags_file.absolute()}')
        commands.append(super().__repr__())
        if self.hooks:
            commands = [f'{repr(self.before)}'] + commands
        return '\n'.join(commands)


class IfKeyword:

    def __init__(self, keyword: str, if_true: Cmd, if_false: Optional[Cmd]):
        self.keyword = keyword
        if os.getenv(self.keyword) is not None:
            self.exec = if_true
        else:
            self.exec = if_false

    def __call__(self, *args, **kwargs) -> Optional[sp.CompletedProcess]:
        if self.exec:
            return self.exec(*args, **kwargs)

    def __repr__(self) -> str:
        return repr(self.exec)

    def __str__(self) -> str:
        if self.exec:
            return f'{self.exec} (choosen by "{self.keyword}")'
        return f'(excluded by absence of "{self.keyword}")'


class IfNotKeyword(IfKeyword):

    def __init__(self, keyword: str, if_true: Cmd, if_false: Optional[Cmd]):
        self.keyword = keyword
        if os.getenv(self.keyword) is None:
            self.exec = if_true
        else:
            self.exec = if_false

    def __str__(self) -> str:
        if self.exec:
            return f'{self.exec} (choosen by absence of "{self.keyword}")'
        return f'(excluded because of "{self.keyword}")'


class OptionalCommands:

    def __init__(self, clause: IfKeyword, keyword: str, commands: List[Cmd]):
        self.exec_list = [clause(keyword, cmd, None) for cmd in commands]

    def __call__(self, *args, **kwargs) -> List[sp.CompletedProcess]:
        return [e(*args, **kwargs) for e in self.exec_list]

    def __repr__(self) -> str:
        return '\n'.join([repr(e) for e in self.exec_list])

    def __str__(self) -> str:
        return '\n'.join([str(e) for e in self.exec_list])
