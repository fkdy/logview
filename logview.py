from logdevice import LogDevice
from logparser import LogParser
from logplotter import LogDevPlotter
from logui import LogUi
from PyQt5.QtWidgets import (QApplication, qApp)
from pathlib import Path
from time import sleep
import logging
import sys
import threading


logging.basicConfig(format='%(filename)s:%(lineno)d: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
PLAYING_DELAY = 800  # ms


class LogView(LogUi):
    '''draw utilization info by parsing log in realtime.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dev = LogDevice(kwargs['n_sa'], kwargs['n_wgp'],
                             kwargs['n_cu'], kwargs['n_simd'],)
        # log file
        self.allocLog = ''
        self.doneLog = ''
        self.simLog = ''
        self.stop_parser = False
        self.run_thread = None
        #self.plt_thread = []

    def confExitAct(self,):
        '''exit application'''
        self.stop_parser = True
        if self.run_thread is not None and self.run_thread.is_alive():
            self.run_thread.join()
        # if len(self.plt_thread) != 0:
        #     for idx, plt in enumerate(self.plt_thread):
        #         if plt.is_alive():
        #             self.plotter[idx].close()
        #         plt.join()
        qApp.quit()

    def confPushAct(self,):
        '''draw figures'''
        allocLog = self.getAllocLine()
        doneLog = self.getDoneLine()
        simLog = self.getSimLine()

        # assume log file not changed
        # TODO: using new log if log file path changed.
        if self.allocLog and self.doneLog and self.simLog:
            self.updatePlotter()
        else:
            self.allocLog = Path(allocLog)
            self.doneLog = Path(doneLog)
            self.simLog = Path(simLog)
            if self.allocLog.exists() and self.doneLog.exists() and self.simLog.exists():
                # disable path editting
                self.setLineEditRdOnly(True)
                self.parser = LogParser(
                    [self.allocLog, self.doneLog, self.simLog])
                self.plotter = []
                logger.debug(f'parsing file: '
                             f'{self.allocLog}, {self.doneLog}, {self.simLog}')
                logger.debug(f'plot sa: {self.saComboBox.currentText()}, '
                             f'wgp: {self.wgpComboBox.currentText()}, '
                             f'cu: {self.cuComboBox.currentText()}, '
                             f'simd: {self.simdComboBox.currentText()}.')
                # create parsing thread
                self.run_thread = threading.Thread(
                    target=self.run, args=(lambda: self.stop_parser,))
                self.run_thread.start()
                self.updatePlotter()
            else:
                logger.debug('Oops, needs more log files')

    def updatePlotter(self,):
        saIdx = self.getSaIdx()
        wgpIdx = self.getWgpIdx()
        cuIdx = self.getCuIdx()
        simdIdx = self.getSimdIdx()
        if wgpIdx == 0:
            self.plotter.append(
                LogDevPlotter(self.dev.get_sa(saIdx),))
        elif cuIdx == 0:
            self.plotter.append(
                LogDevPlotter(self.dev.get_wgp(saIdx, wgpIdx-1),))
        elif simdIdx == 0:
            self.plotter.append(
                LogDevPlotter(self.dev.get_cu(saIdx, wgpIdx-1, cuIdx-1),))
        else:
            self.plotter.append(
                LogDevPlotter(
                    self.dev.get_simd(saIdx, wgpIdx-1, cuIdx-1, simdIdx-1),))
        #self.plt_thread.append(threading.Thread(
        #    target=self.plot, args=(len(self.plotter)-1,)))
        #self.plt_thread[-1].start()
        # display figures
        self.plotter[-1].show()

    def plot(self, idx):
        '''display figures'''
        logger.debug(f'show plot {idx}')
        self.plotter[idx].show()

    def run(self, stop):
        '''run logparser'''
        while self.parser.busy():
            # connect parser <-> device
            cmd_list = self.parser.run()
            for c in cmd_list:
                logger.debug(c)
                self.dev.run(c)
                # pause by PLAYING_DELAY ms
                #sleep(PLAYING_DELAY/1000)
            # stop the loop
            if stop():
                logger.debug('stop running parser')
                break


class LogView1:
    '''draw utilization info by parsing log in realtime.'''

    def __init__(self, logs: list, n_sa: int = 2,
                 n_wpg: int = 3, n_cu: int = 2, n_simd: int = 2):
        '''instantiate LogView'''
        # config parser
        self.log_path = logs
        for lpath in logs:
            logger.debug(lpath)
        self.parser = LogParser(logs)
        self.dev = LogDevice(n_sa, n_wpg, n_cu, n_simd)
        # plotter is instantiated at self.config()
        self.plotter = []

    def config(self,):
        '''config device'''
        # - config device
        # - connect parser <-> dev, dev <-> plotter
        # - config plotter
        # - create a thread to config & display plotter
        self.plotter.append(LogDevPlotter(self.dev.get_simd(0, 0, 0, 0), 500))
        self.plotter.append(LogDevPlotter(self.dev.get_simd(0, 0, 0, 1), 500))
        self.plotter.append(LogDevPlotter(self.dev.get_sa(0), 500))

    def run(self,):
        '''run logview'''
        while self.parser.busy():
            # connect parser <-> device
            cmd_list = self.parser.run()
            for c in cmd_list:
                logger.debug(c)
                self.dev.run(c)
            # pause 100 ms
            sleep(600/1000)

        # simd0 = self.dev.get_simd(0, 0, 0, 0)
        # logger.debug(simd0.get_res(0).get_samples())
        # logger.debug(simd0.get_res(1).get_samples())
        # logger.debug(simd0.get_res(2).get_samples())


if __name__ == '__main__':
    # sim_log = Path('../3.bench/sim.log')
    # alloc_log = Path('../3.bench/alloc.log')
    # done_log = Path('../3.bench/done.log')
    # logs = [sim_log, alloc_log, done_log]
    # view = LogView(logs)
    # view.config()
    # view.run()
    # plt.show()
    app = QApplication(sys.argv)
    w = LogView(n_sa=2, n_wgp=3, n_cu=5, n_simd=2)
    sys.exit(app.exec_())
