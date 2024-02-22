import atexit
import curses
import logging
import functools as ft

from datetime import datetime


class CursesHandler(logging.StreamHandler):

    def __init__(self, *args, **kwargs):
        self.start_date = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        self.records = []
        self.main_scr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        def cleanup():
            curses.nocbreak()
            self.main_scr.keypad(False)
            curses.echo()
            curses.endwin()

        atexit.register(cleanup)
        self.main_scr.clear()

        # info
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.info_color = curses.color_pair(1)
        # warning
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_YELLOW)
        self.warning_color = curses.color_pair(2)
        # error
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
        self.error_color = curses.color_pair(3)
        # debug
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_WHITE)
        self.debug_color = curses.color_pair(4)

        self.colormap = {
            logging.INFO: self.info_color,
            logging.WARNING: self.warning_color,
            logging.ERROR: self.error_color,
            logging.DEBUG: self.debug_color}

        self.sys_info = curses.newwin(3, curses.COLS, 0, 0)
        self.log = curses.newwin(curses.LINES - 3, curses.COLS, 3, 0)

        self.sys_info.border()
        self.log.border()

        self.sys_info.bkgd(' ', self.info_color)
        self.log.bkgd(' ', self.info_color)

        super().__init__(*args, **kwargs)

    def emit(self, record):
        current_date = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        info_msg = f'Started {self.start_date}; Now {current_date}'
        self.sys_info.addstr(
            1, (curses.COLS - len(info_msg)) // 2,
            info_msg,
            curses.color_pair(1)
        )
        self.sys_info.refresh()

        log_height, _ = self.log.getmaxyx()
        if len(self.records) == log_height - 2:
            self.records.pop(0)
        self.records.append(record)

        self.log.clear()
        for i, record in enumerate(self.records):
            msg = self.format(record)
            msg = msg[:curses.COLS - 3]
            self.log.addstr(1+i, 2, msg, self.colormap[record.levelno])
        self.log.refresh()
