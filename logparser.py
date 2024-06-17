from pathlib import Path
import re
import logging
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#FAST = False
MAX_RD_LINES = 5


class LogFiles:
    # TODO: close log file
    '''log file generator'''
    def __init__(self, log: list):
        if len(log) < 3:
            logging.critical('log file should contains: simulation log,'
                             'allocate log and done log.')
            sys.exit(-1)
        self.log_alloc = open(log[0], 'r')
        self.log_done = open(log[1], 'r')
        self.log_sim = open(log[2], 'r')
        self.log_busy = True

    def get_lines(self, log_file):
        '''generate lines in log_file. yield None when we reach the end of
 the file'''
        while self.log_busy:
            line = ''
            tmp = log_file.readline()
            rd_len = 0
            while tmp:
                line = line + tmp
                if rd_len >= MAX_RD_LINES:
                    break
                tmp = log_file.readline()
                rd_len = rd_len + 1
            yield line

    def get_alloc_lines(self,):
        '''generate lines in log_alloc'''
        return self.get_lines(self.log_alloc)

    def get_done_lines(self,):
        '''generate lines in log_done'''
        return self.get_lines(self.log_done)

    def get_sim_lines(self,):
        '''generate lines in log_sim'''
        return self.get_lines(self.log_sim)

    def set_log_status(self, busy=False):
        '''set log file status'''
        self.log_busy = busy

    def search(self, lines, regexp: re.Pattern) -> re.Match:
        '''search regexp in lines'''
        return regexp.search(lines)

    def finditer(self, lines: str, regexp: re.Pattern):
        '''find all matches in lines.
        return the match as a callable_iterator'''
        return regexp.finditer(lines)


class LogParser(LogFiles):
    '''parse log. generate command for device'''
    def __init__(self, log: list):
        super().__init__(log)
        self.time_exp = r'^UVM.INFO.*?@ (?P<time>\d+)ns:'
        self.type_exp = r'.*?\[wave (?P<type>\w+)\]'
        self.act_exp = r' the trans is.*?{(?P<action>.*?)}'
        self.end_exp = r'^.*?V\s+C\s+S\s+S\s+i\s+m\s+.*?Time:\s+(?P<time>\d+)\s+ps'
        self.hdr = self.time_exp + self.type_exp
        self.exp = self.hdr + self.act_exp
        # self.exp = (r'^.*?@ (?P<time>\d+)ns:.*?\[wave (?P<type>\w+)\]'
        #                   r' the trans is.*?{(?P<action>.*?)}')
        self.probe_re = re.compile(self.hdr, flags=re.M)
        self.act_re = re.compile(self.exp, flags=re.S | re.M)
        self.end_re = re.compile(self.end_exp, re.S)
        self.item_exp = r'^\s*(?P<key>\w+):\s*\'h(?P<val>[a-fxA-FX0-9_]+)\s*$'
        self.item_re = re.compile(self.item_exp, re.M)
        self.alloc_lines = super().get_alloc_lines()
        self.done_lines = super().get_done_lines()
        self.sim_lines = super().get_sim_lines()
        self.alloc_str = ''
        self.done_str = ''
        self.sim_str = ''
        self.end_str = 'EOS' # end of simulation

    def busy(self,):
        '''reach to the end of the log'''
        return self.log_busy

    def run(self,):
        '''get info from log. save command to queue.'''
        # using regexp to parse info from log
        #
        # implemented as a generator. destroy the generator at the end of
        # the simulation
        #
        # when we get to the end of the simulation log, we enqueue a end of
        # command string to indicate the end of simulation

        # update log strings
        #
        # update simulation log first. we need to check simulation status.
        self._append_sim()
        self._append_alloc()
        self._append_done()

        cmd_list = []
        self.alloc_str, cmd = self._parse_act(self.alloc_str)
        # logger.debug(f'alloc str: {repr(self.alloc_str)},\ncmd: {cmd}')
        cmd_list.extend(cmd)
        self.done_str, cmd = self._parse_act(self.done_str)
        # logger.debug(f'done str: {repr(self.done_str)},\ncmd: {cmd}')
        cmd_list.extend(cmd)
        self.sim_str, cmd = self._parse_end(self.sim_str)
        # logger.debug(f'end str: {repr(self.sim_str)},\ncmd: {cmd}')
        if cmd == self.end_str:
            self.log_busy = False
        # return time sorted list
        #logger.debug(f'{cmd_list}')
        cmd_list.sort(key=lambda act: int(act['time']),)
        #logger.debug(f'{cmd_list}')
        return cmd_list

    def _get_str(self, line, gen):
        '''get strings from log. save it to lines'''
        for tmp in gen:
            if not tmp:
                break
            else:
                line = line + tmp
        #for tmp in gen:
        #    if FAST:
        #        if not tmp:
        #            break
        #        else:
        #            line = line + tmp
        #    else:
        #        line = line + tmp
        #        break
        return line

    def _append_alloc(self,):
        '''append log to alloc_lines'''
        self.alloc_str = self._get_str(self.alloc_str, self.alloc_lines)
        # logger.debug(f'get alloc str. {self.alloc_str}')

    def _append_done(self,):
        '''append log to done_lines'''
        self.done_str = self._get_str(self.done_str, self.done_lines)
        # logger.debug(f'get done str. {self.done_str}')

    def _append_sim(self,):
        '''append log to sim_lines'''
        self.sim_str = self._get_str(self.sim_str, self.sim_lines)
        # logger.debug(f'get sim str. {self.sim_str}')

    def _parse_act(self, log_str: str) -> (str, list):
        '''parse actions from log strings'''
        # get lines from log file
        #
        # searching for self.hdr.
        # put lines behind hdr into buffer until we get all the action.
        # parsing the action. write the action to dict.
        cmd = []
        probe = self.search(log_str, self.probe_re)
        #logger.debug(f'log str: {log_str}, re: {self.probe_re}, probe: {probe}')
        if probe is None:
            return ('', cmd)

        # truncate log string
        #logger.debug(f'probe start: {probe.start()}')
        log_str = log_str[probe.start():]
        str_start_pos = 0
        # search for all actions
        actions = self.finditer(log_str, self.act_re)
        # parsing resource
        for act in actions:
            # parse action. insert the action into the dict
            str_start_pos = act.end()
            act_d = act.groupdict()
            act_d.update({'action': self._parse_item(act_d['action'])})
            cmd.append(act_d)
        return (log_str[str_start_pos:], cmd)

    def _parse_end(self, log_str: str):
        probe = self.search(log_str, self.end_re)
        if probe is None:
            return ('', '')
        else:
            return ('', self.end_str)

    def _parse_item(self, log_str: str):
        '''parse action items from log strings'''
        items = {}
        samples = self.finditer(log_str, self.item_re)
        for item in samples:
            item_d = item.groupdict()
            items = items | {item_d['key']: item_d['val']}
        return items
