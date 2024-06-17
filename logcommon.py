import logging


logger = logging.getLogger(__name__)


class Database:
    '''object to save line infor'''
    def __init__(self, name: str, xs: list = [],
                 ys: list = [], yann: list = [],
                 ymax=100, data=None):
        # label
        self.lab = name
        self.xs = xs
        self.ys = ys
        self.ymax = ymax
        self.ys_norm = []
        # annotation
        self.ys_anno = yann
        self.data = data
        for y in self.ys:
            self.ys_norm.append(y / self.ymax)
        logger.debug(f'x: {self.xs}')
        logger.debug(f'y: {self.ys}')

    def add_sample(self, x: int, y: int = -1, txt: str = ''):
        '''add sample to the line'''
        self.xs.append(x)
        if y <= -1 and len(self.ys) != 0:
            self.ys.append(self.ys[-1])
            self.ys_norm.append(self.ys_norm[-1])
            self.ys_anno.append(txt)
        elif y <= -1:
            raise ValueError('Error, "y" should be positive.'
                             'Check you input')
        else:
            self.ys.append(y)
            self.ys_norm.append(y / self.ymax)
            self.ys_anno.append(txt)

    def inc_res(self, at_x: int, by_delta: int, txt: str = ''):
        '''increase resource'''
        x = at_x
        y = self.ys[-1] + by_delta
        if y > self.ymax:
            raise ValueError(f'Error, illegal operation.'
                             f'{self.lab} resource overflow')
        self.add_sample(x, y, txt)

    def inc_usage(self, at_x: int, by_delta: int, txt: str = ''):
        self.inc_res(at_x, by_delta, txt)

    def dec_res(self, at_x: int, by_delta: int, txt: str = ''):
        '''decrease resource'''
        x = at_x
        y = self.ys[-1] - by_delta
        if y < 0:
            raise ValueError(f'Error, illegal operation.'
                             f'{self.lab} resource underflow')
        self.add_sample(x, y, txt)

    def dec_usage(self, at_x: int, by_delta: int, txt: str = ''):
        self.dec_res(at_x, by_delta, txt)

    def ext_last_sample(self, at_x: int):
        '''extend resource'''
        x = at_x
        y = self.ys[-1]
        self.add_sample(x, y,)

    def get_rn(self,):
        '''get resource name of the database'''
        return self.lab.split('.')[-1]

    def get_data(self,):
        return self.data

    def get_label(self,):
        '''get name of the database'''
        return self.lab

    def get_samples(self,):
        '''get line data.'''
        return (self.xs, self.ys, self.ys_anno, self.lab)

    def get_last_sample(self,):
        '''get the last data'''
        return (self.xs[-1], self.ys[-1])
