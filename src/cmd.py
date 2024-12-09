import os
import logging
import threading
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

    created_count = 0

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
                 **kwargs):
        self.id = Cmd.created_count
        Cmd.created_count += 1
        self.counter = 0

        self.cmd = cmd
        self.desc = desc
        self.name = name or ' '.join(self.cmd)
        if not hasattr(self, 'fs_friendly_name'):
            self.fs_friendly_name = self.name.replace('/', '.') \
                                             .replace('_', '.') \
                                             .replace('>', '') \
                                             .replace('<', '')
        self.blocking = blocking
        self.critical = critical
        self.env = {**os.environ}
        if env:
            self.env = {**self.env, **env}
        self.keywords = keywords or set()
        self.ignore_change = ignore_change
        self.process = ft.partial(
            sp.Popen,
            env=self.env,
            **kwargs
        )

        self.hooks = hooks
        self.before = lambda *args, **kwargs: None
        self.after = lambda *args, **kwargs: None
        if self.hooks:
            if len(self.hooks) == 1:
                self.before = hooks[0]
            else:
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
                 pretend: bool = False,
                 **kwargs) -> sp.CompletedProcess:
        logger = logging.getLogger()
        process_started_msg = str(self)
        self.counter += 1
        self.env.update(kwargs.get('env', {}))

        if pretend:
            logger.info(process_started_msg)
            logger.debug(f'Launching {self.id}-{self.counter} **{self.env} {self.cmd} **{kwargs}')
            return sp.CompletedProcess(self.cmd, returncode=0)

        self.before(self)
        if 'stdout' not in kwargs:
            kwargs['stdout'] = open(f'{self.fs_friendly_name}-{self.id}-{self.counter}.stdout', 'wb')
        if 'stderr' not in kwargs:
            kwargs['stderr'] = open(f'{self.fs_friendly_name}-{self.id}-{self.counter}.stderr', 'wb')

        logger.debug(f'Launching in {Path.cwd()} {self.id}-{self.counter} **{self.env} {self.cmd} **{kwargs}')
        proc: sp.CompletedProcess = self.process(
            args=self.cmd,
            **kwargs)
        logger.info(f'{process_started_msg} (pid: {proc.pid})')
        if self.blocking:
            logger.debug(f'Waiting for "{self}" (pid: {proc.pid})')
            proc.wait()
        if self.critical:
            if not self.blocking:
                logger.debug(f'Waiting for "{self}" (pid: {proc.pid})')
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f'Critical process returned non-zero code ({proc.returncode}): {repr(self)}')
        self.after(self, proc)

        # reap the zombies
        if not pretend:
            threading.Thread(target=proc.wait).start()
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

    prefetch_procs = []
    package_use_dir = Path('/etc/portage/package.use')
    package_env_dir = Path('/etc/portage/package.env')
    package_mask_dir = Path('/etc/portage/package.mask')
    package_accept_kwd = Path('/etc/portage/package.accept_keywords')

    def __init__(self,
                 package: str,
                 binary_alternative: str = '',
                 emerge_override: str = '',
                 use_flags: Union[List[str], str] = '',
                 extra_use_flags: Union[List[str], str] = '',
                 prefetch: bool = True,
                 mask: bool = False,
                 **kwargs):
        self.emerge_override = emerge_override
        self.is_prefetch_proc = '--fetchonly' in self.emerge_override
        self.mask = mask

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

        # Copy-pasted here, because Cmd class initialization
        # should happen later
        self.fs_friendly_name = self.package.replace('/', '.') \
                                            .replace('_', '.') \
                                            .replace('>', '') \
                                            .replace('<', '')
        if self.is_prefetch_proc:
            self.fs_friendly_name = f'prefetch-{self.fs_friendly_name}'
        self.useflags_file = self.package_use_dir / self.fs_friendly_name
        self.cmd = f'emerge {self.emerge_override} --autounmask-write {self.package}'

        description = self.use_flags
        if 'desc' in kwargs:
            description = kwargs['desc']
            kwargs.pop('desc')
        if 'critical' not in kwargs:
            kwargs['critical'] = False
        if 'blocking' not in kwargs:
            kwargs['blocking'] = False

        if self.package.startswith('@'):
            prefetch = False

        # maybe this class is overworked already
        if self.mask:
            # masking can't be non-blocking
            kwargs['blocking'] = True
            self.cmd = f'echo "{self.package}" > {self.package_mask_dir}/{self.fs_friendly_name}'

        if prefetch and not (kwargs['critical'] or kwargs['blocking']):
            kwargs['hooks'] = [Package(self.package,
                                       emerge_override='--fetchonly --deep',
                                       desc='package prefetch started',
                                       blocking=False,
                                       prefetch=False,
                                       env={'USE': self.use_flags}),
                               lambda *args, **kwargs: None]

            self.cmd = f'echo "{self.package}" >> /var/lib/portage/world'

        super().__init__(
            self.cmd,
            name=package + ('-prefetch' if self.is_prefetch_proc else ''),
            desc=description,
            **kwargs
        )

    def __call__(self,
                 *args,
                 pretend: bool = False,
                 **kwargs) -> Union[List[sp.CompletedProcess],
                                    sp.CompletedProcess]:
        if pretend:
            return [self.before(pretend=pretend),
                    super().__call__(pretend=pretend, **kwargs),
                    self.after(pretend=pretend)]

        if self.mask:
            self.package_mask_dir.mkdir(exist_ok=True)
            return super().__call__(**kwargs)

        if not self.is_prefetch_proc and not self.binary and '@' not in str(self.useflags_file):
            with open(self.useflags_file, 'a') as use:
                use.write(f'{self.package} {self.use_flags}')

        proc = None
        max_retries = 3
        for i in range(max_retries + 1):
            try:
                proc = super().__call__(**kwargs)
                ETC_UPDATE(pretend=pretend)
            except RuntimeError:
                if i == max_retries:
                    raise
            else:
                break
        if self.is_prefetch_proc:
            self.prefetch_procs.append(proc)
        return proc

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
        if bool(self):
            self.exec = if_true
        else:
            self.exec = if_false

    def __call__(self, *args, **kwargs) -> Optional[sp.CompletedProcess]:
        if self.exec:
            return self.exec(*args, **kwargs)

    def __bool__(self):
        return os.getenv(self.keyword) is not None

    def __repr__(self) -> str:
        return repr(self.exec)

    def __str__(self) -> str:
        if self.exec:
            return f'{self.exec} (choosen by "{self.keyword}")'
        return f'(excluded by absence of "{self.keyword}")'


class IfNotKeyword(IfKeyword):

    def __init__(self, keyword: str, if_true: Cmd, if_false: Optional[Cmd]):
        self.keyword = keyword
        if bool(self):
            self.exec = if_true
        else:
            self.exec = if_false

    def __bool__(self):
        return os.getenv(self.keyword) is None

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
        return '\n'.join([repr(e) for e in self.exec_list if e])

    def __str__(self) -> str:
        return '\n'.join([str(e) for e in self.exec_list if e])


ETC_UPDATE = ShellCmd('echo -5 | etc-update')
