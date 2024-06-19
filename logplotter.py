import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.ticker import FixedLocator
from matplotlib.widgets import Button
import numpy as np
from logcommon import Database
from logdevice import Dev
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Line:
    '''object to display information in animation'''
    # def __init__(self, fig: Figure, ax: Axes, db: Database,):
    #     '''register to ax in fig'''
    #     self.fig = fig
    #     self.ax = ax
    #     self.db = db
    #     self.ani = animation.FuncAnimation(
    #         self.fig, self.update, interval=1000)
    def __init__(self, ax: Axes, db: Database,):
        '''register to ax in fig'''
        self.ax = ax
        self.db = db
        self.major_locator = FixedLocator(
            [self.db.get_ymax()/4, self.db.get_ymax()/2,
             self.db.get_ymax()/4*3, self.db.get_ymax(),])
        self.ax.xaxis.set_major_locator(self.major_locator)

    def update(self, i):
        '''using device data to update axes'''
        # TODO: add line segment
        xs, ys, ys_anno, lab = self.db.get_samples()
        logger.debug(self.db.get_samples())
        self.ax.clear()
        # self.ax.set_title(f'{self.db.get_rn()}')
        self.ax.grid(True, linestyle='-.')
        self.ax.yaxis.set_major_locator(self.major_locator)
        self.ax.plot(
            xs, ys, 'o-', label=self.db.get_rn(), color=self.db.get_color())
        self.ax.fill_between(np.array(xs), 0, np.array(ys),
                             label=self.db.get_rn(),
                             hatch='o',  # animated=True,
                             color=self.db.get_color())
        for x, y, t in zip(xs, ys, ys_anno):
            anno = self.ax.annotate(t, xy=(x, y), xycoords='data',
                                    xytext=(1.5, 1.5),
                                    textcoords='offset points')
            anno.set_visible(False)
        self.ax.legend(loc='upper left',)


class LogPlotter:
    '''object to display simulation result'''
    def __init__(self,):
        '''create a config button'''
        self.lines = []

    def config(self,):
        '''setup user configuration'''
        # get user input
        #
        # create figure and axes
        # bind axes with Database
        pass


class LogDevPlotter:
    '''object to display simulation result'''
    def __init__(self, dev: Dev, update_intvl=300):
        '''create a config button'''
        # number of direct resource
        self.res_num = len(dev.get_res_list())
        # number of indirect resource
        self.in_num = len(dev.get_sum_list())
        # db number is the number of subplot
        self.sub_num = self.res_num + self.in_num
        # create a figure for the device
        # self.fig = Figure()
        self.fig = plt.figure()
        self.fig.suptitle(f'{dev.get_dn()}')
        # connect axes with db
        self.lines = []
        self.axes = []
        for idx in range(self.sub_num):
            # create new axes. stick to the x axis of the first ax
            if idx == 0:
                ax = self.fig.add_subplot(self.sub_num, 1, idx + 1)
            else:
                ax = self.fig.add_subplot(self.sub_num, 1, idx + 1,
                                          sharex=self.axes[0])
            # only show 'outer' labels and tick labels
            ax.label_outer()
            self.axes.append(ax)
            in_idx = idx - self.in_num
            if idx < self.res_num:
                db = dev.get_res_list()[idx]
            else:
                db = dev.get_sum_list()[in_idx]
            # ax.set_title(f'{db.get_rn()}')
            # if idx != self.sub_num - 1:
            #     ax.tick_params(labelbottom=False)
            self.lines.append(Line(ax, db))
        self.ax_resume = self.fig.add_axes([0.7, 0.9, 0.1, 0.075])
        self.ax_pause = self.fig.add_axes([0.81, 0.9, 0.1, 0.075])
        self.b_resume = Button(self.ax_resume, 'Resume')
        self.b_paues = Button(self.ax_pause, 'Pause')
        self.b_resume.on_clicked(self.resumeAnimation)
        self.b_paues.on_clicked(self.pauseAnimation)
        self.paused = False

        self.ani = animation.FuncAnimation(
            self.fig, self.update, interval=update_intvl)

    def update(self, i):
        '''update axes of this device'''
        for idx in range(self.sub_num):
            self.lines[idx].update(i)

    def config(self,):
        '''setup user configuration'''
        # get user input
        #
        # create figure and axes
        # bind axes with Database
        pass

    def show(self,):
        '''show figure'''
        self.fig.show()

    def close(self,):
        '''close figure'''
        plt.close(self.fig)

    def pauseAnimation(self, event):
        '''pause animation'''
        if not self.paused:
            self.ani.pause()
            self.paused = True

    def resumeAnimation(self, event):
        '''resume animation'''
        if self.paused:
            self.ani.resume()
            self.paused = False
