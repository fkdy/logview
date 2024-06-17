import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QAction, QStatusBar,
    QFileDialog, qApp, QComboBox,
    QVBoxLayout, QDialog, QWidget,
    QFormLayout, QLineEdit, QPushButton,
)


logging.basicConfig(format='%(filename)s:%(lineno)d: %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LogUi(QWidget):

    def __init__(self, *args, n_sa=2, n_wgp=4, n_cu=2, n_simd=2, **kwargs):
        super().__init__(*args, **kwargs)
        # lineedit
        self.allocLineEdit = QLineEdit()
        self.doneLineEdit = QLineEdit()
        self.simLineEdit = QLineEdit()
        # combobox
        self.saComboBox = QComboBox()
        self.wgpComboBox = QComboBox()
        self.cuComboBox = QComboBox()
        self.simdComboBox = QComboBox()
        # push button
        self.confPushButton = QPushButton('draw')
        self.exitPushButton = QPushButton('exit')

        self.initUI()
        logger.debug(f'n_wgp: {n_wgp}')
        self.confUI(n_sa, n_wgp, n_cu, n_simd)

    def initUI(self,):
        '''init UI'''
        self.setWindowTitle("LogView")

        layout = QFormLayout()
        layout.addRow(QLabel('allocation log:'), self.allocLineEdit)
        layout.addRow(QLabel('done log:'), self.doneLineEdit)
        layout.addRow(QLabel('sim log:'), self.simLineEdit)
        # may add a separator
        layout.addRow(QLabel('Sa index:'), self.saComboBox)
        layout.addRow(QLabel('Wgp index:'), self.wgpComboBox)
        layout.addRow(QLabel('Cu index:'), self.cuComboBox)
        layout.addRow(QLabel('Simd32 index:'), self.simdComboBox)
        layout.addRow(self.confPushButton)
        layout.addRow(self.exitPushButton)
        self.setLayout(layout)

        self.show()

    def confUI(self, n_sa=2, n_wgp=3, n_cu=2, n_simd=2):
        '''config ui'''
        # config default log path
        self.confDefPath('../3.bench/alloc.log', '../3.bench/done.log',
                         '../3.bench/sim.log')

        # create sa selection tool
        self.confComboBox(self.saComboBox, n_sa, False, self.toolSaIdxChange)
        # create wgp selection tool
        self.confComboBox(self.wgpComboBox, n_wgp, True, self.toolWgpIdxChange)
        # create cu selection tool
        self.confComboBox(self.cuComboBox, n_cu, True, self.toolCuIdxChange)
        # create simd selection tool
        self.confComboBox(self.simdComboBox, n_simd, True, self.toolSimdIdxChange)

        # push button
        self.confPushButton.clicked.connect(self.confPushAct)
        # exit button
        self.exitPushButton.clicked.connect(self.confExitAct)

    def confDefPath(self, alloc_log, done_log, sim_log):
        self.allocLineEdit.setText(alloc_log)
        self.doneLineEdit.setText(done_log)
        self.simLineEdit.setText(sim_log)

    def confComboBox(self, combo_box: QComboBox, item_num: int,
                     may_empty: bool, slotFunc: callable):
        if may_empty:
            combo_box.addItem('--')
        for i in range(item_num):
            combo_box.addItem(str(i))
        combo_box.adjustSize()
        combo_box.currentIndexChanged.connect(slotFunc)

    def toolSaIdxChange(self, i):
        '''Sa index changed'''
        # start from 0
        logger.debug(f'sa index: {i}')

    def toolWgpIdxChange(self, i):
        '''Wgp index changed'''
        # start from 1
        logger.debug(f'wgp index: {i}')

    def toolCuIdxChange(self, i):
        '''cu index changed'''
        # start from 1
        logger.debug(f'cu index: {i}')

    def toolSimdIdxChange(self, i):
        '''simd index changed'''
        # start from 1
        logger.debug(f'simd index: {i}')

    def confPushAct(self,):
        '''draw figures'''
        pass

    def confExitAct(self,):
        '''exit the program'''
        qApp.quit()

    def setLineEditRdOnly(self, lock_input):
        '''lock/unlock input'''
        self.allocLineEdit.setReadOnly(lock_input)
        self.doneLineEdit.setReadOnly(lock_input)
        self.simLineEdit.setReadOnly(lock_input)

    def getAllocLine(self,) -> str:
        '''get allocation log path'''
        return self.allocLineEdit.text()

    def getDoneLine(self,) -> str:
        '''get done log path'''
        return self.doneLineEdit.text()

    def getSimLine(self,) -> str:
        '''get done log path'''
        return self.simLineEdit.text()

    def getSaIdx(self,) -> int:
        '''get index of SA device'''
        return self.saComboBox.currentIndex()

    def getWgpIdx(self,) -> int:
        '''get index of WGP device'''
        return self.wgpComboBox.currentIndex()

    def getCuIdx(self,) -> int:
        '''get index of CU device'''
        return self.cuComboBox.currentIndex()

    def getSimdIdx(self,) -> int:
        '''get index of WGP device'''
        return self.simdComboBox.currentIndex()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = LogUi()
    sys.exit(app.exec_())
