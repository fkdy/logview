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
        self.l2d = self.ax.plot(
            xs, ys, 'o-', label=self.db.get_rn(), color=self.db.get_color())
        self.ax.fill_between(np.array(xs), 0, np.array(ys),
                             label=self.db.get_rn(),
                             hatch='o',  # animated=True,
                             color=self.db.get_color())
        self.anno = self.ax.annotate(text='',
                                     xy=(0, 0),
                                     xycoords='data',
                                     xytext=(10, 10),
                                     textcoords='offset points',
                                     #bbox={'boxstyle': 'round', 'fc': 'w'},
                                     arrowprops={'arrowstyle': '->'},)
        self.anno.set_visible(False)
        self.ax.legend(loc='upper left',)

    def get_line(self,):
        '''get line'''
        return self.l2d

    def get_sample(self, i):
        '''get sample value in the line'''
        xs, ys, ys_anno, lab = self.db.get_samples()
        return (xs[i], ys[i])

    def get_anno(self,):
        '''get ax annotation'''
        return self.anno


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
            self.fig, self.update, interval=update_intvl, frames=5000000)
        self.fig.canvas.mpl_connect('motion_notify_event', self.mhover)

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

    def mhover(self, event):
        '''hover function for mpl_connect'''
        # get axes index
        #
        # get line
        if event.inaxes is not None:
            for idx, ax in enumerate(self.axes):
                if event.inaxes == ax:
                    break
            logger.info(f'{idx}: {ax}')
            # logger.info(self.lines[idx].get_line()[-1])
            l2d = self.lines[idx].get_line()[-1]
            l2d.set_pickradius(3)
            anno = self.lines[idx].get_anno()
            # l2d.contains returns (contains, pointlist)
            ctd, pl = l2d.contains(event)
            if ctd and anno.get_visible() is False:
                logger.info(f"pl: {pl['ind'][0]}")
                x, y = self.lines[idx].get_sample(pl['ind'][0])
                logger.info(f"pl: {pl['ind'][0]}, data: ({x}, {y})")
                anno.xy = (x, y)
                anno.set_text(f'val: {y} @ {x}ps')
                anno.set_visible(True)
                self.fig.canvas.draw_idle()
            elif anno.get_visible():
                anno.set_visible(False)
                self.fig.canvas.draw_idle()
