from pathlib import Path
import numpy as np
from logcommon import Database
import logging
import sys
import itertools


ACT_ALLOC = 'allocation'
ACT_DONE = 'done'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Dev:
    '''object to display information in animation'''
    def __init__(self, name: str = 'Dev', id: int = 0):
        '''name of the device'''
        self.name = name
        # device id
        self.id = id
        # list of direct Database instance
        self.res = []
        self.res_map = {}
        # list of Dev instance
        self.dev = []
        # number of Dev inside this Dev
        self.dev_num = 0
        # list of indrect Database instance (resource summary of devices in
        # the device)
        self.sum = []
        logger.debug(f'init {self.name}')

    def res_alloc(self, act: dict):
        '''allocate resource'''
        if int(act['action'][self.name.split('.')[-2]+'_id'], 16) == self.id:
            logger.info(f'run {act["type"]} on {self.get_dn()}')
            if act['type'] == ACT_ALLOC:
                for db in itertools.chain(self.res, self.sum):
                    logger.info(f'alloc {db.get_rn()} in {self.get_dn()}')
                    act = self.act_pre(act)
                    db.dec_res(act['time'],
                               int(act['action'][db.get_rn()], 16))
                    act = self.act_post(act)
            elif act['type'] == ACT_DONE:
                for db in itertools.chain(self.res, self.sum):
                    logger.info(f'done {db.get_rn()} in {self.get_dn()}')
                    act = self.act_pre(act)
                    db.inc_res(act['time'],
                               int(act['action'][db.get_rn()], 16))
                    act = self.act_post(act)
            else:
                logger.critical(f'action *{act["type"]}* not supported')
                sys.exit(-1)

            for idx in range(self.dev_num):
                # TODO: may need to modify act accordingly
                self.get_dev_list()[idx].res_alloc(act)

    def res_mgr(self, act: dict):
        '''manage resource'''
        if int(act['action'][self.name.split('.')[-2]+'_id'], 16) == self.id:
            # update device resource from bottom up
            for idx in range(self.dev_num):
                dev = self.get_dev_list()[idx]
                dev.res_mgr(act)

            tick = act['time']
            # sum up resource in the device
            for idx in range(len(self.sum)):
                db = self.sum[idx]
                res_name = db.get_rn()
                res_usage = 0
                res_update = False
                # loop through all dev
                for devidx in range(self.dev_num):
                    dev = self.get_dev_list()[devidx]
                    if res_name in dev.get_res_map():
                        res_db = dev.get_res_map()[res_name][1]
                        res_usage = res_usage + res_db.get_last_sample()[1]
                        # TODO: check res_db tick
                        res_update = True
                if res_update:
                    db.add_sample(tick, res_usage, act['action']['dbg_id'])
                else:
                    db.ext_last_sample(tick)

            logger.info(f'run {act["type"]} on {self.get_dn()}')
            for res_name, val in self.get_res_map().items():
                # logger.info(f'res name: {res_name}, val: {val}')
                if val[0] is not None:
                    funcAction = val[0]
                    argDb = val[1]
                    funcAction(act, argDb)

    def add_res(self, res_name: str, func_action: callable,
                max_res: int, data=None, color='b'):
        '''add resource item to res_map'''
        db = Database(f'{self.name}.{res_name}', [0,], [0,], ['dbg_id',],
                      ymax=max_res, data=data, color=color)
        self.res_map[res_name] = (func_action, db)
        if func_action is not None:
            self.res.append(db)
        else:
            self.sum.append(db)

    def act_pre(self, act: dict):
        '''action preprocessing before res_alloc'''
        return act

    def act_post(self, act: dict):
        '''action postprocessing after res_alloc'''
        return act

    def get_res_map(self,) -> dict:
        '''return resource map'''
        return self.res_map

    def get_res_list(self,) -> list:
        '''return database in the Dev'''
        return self.res

    def get_res(self, idx):
        '''return resource database'''
        return self.res[idx]

    def get_dev_list(self,) -> list:
        '''return devices in the Dev'''
        return self.dev

    def get_sum_list(self,) -> list:
        '''return indirect database'''
        return self.sum

    def get_dev(self, idx):
        '''return device specified by idx'''
        if len(self.dev) == 0:
            logger.critical(f'No device contained in {self.name}')
            sys.exit(-1)
        return self.dev[idx]

    def get_dn(self,):
        '''return device name'''
        return self.name


class Wave:
    '''object to display information of a wave job'''
    def __init__(self, debug_id: str = 'Wave'):
        '''name of the wave'''
        self.name = f'id_{debug_id}'


class Simd32(Dev):
    '''simd32 device'''
    def __init__(self, id: int = 0, dn_pre='',):
        # construct device name from id
        if dn_pre:
            dn_pre = f'{dn_pre}.'
        dn = f'{dn_pre}simd32.{str(id)}'
        super().__init__(dn, id)
        # resource_name: (funcAction, database,)
        wv_num = 16
        wv_data = [False] * wv_num
        self.add_res('wv_id', self.wvAction, wv_num, wv_data, color='r')
        # TODO: add resource data
        self.add_res('vgpr_size', self.vgprAction, 64, color='g')
        self.add_res('useer_accum_cntrb', self.useraccumAction, 100, color='b')

    def wvAction(self, act: dict, db: Database):
        '''command parsing function for wv_id resource'''
        act_type = act['type']
        act_time = act['time']
        act_action = act['action']
        wv_data = db.get_data()
        # convert hex string to decimal
        wv_id = int(act_action['wv_id'], 16)
        if act_type == ACT_ALLOC:
            if wv_data[wv_id]:
                logger.error(f'Error detected. Double allocation.'
                             f'alloc wv_id {wv_id} in {self.name} '
                             f'at {act_time}')
            else:
                wv_data[wv_id] = True
                logger.info(f'act time: {act_time}')
                db.inc_usage(act_time, 1, txt=act_action['dbg_id'])
        elif act_type == ACT_DONE:
            logger.debug('done')
            if not wv_data[wv_id]:
                logger.error(f'Error detected. Double release.'
                             f'release wv_id {wv_id} in {self.name} '
                             f'at {act_time}')
            else:
                wv_data[wv_id] = False
                logger.info(f'act time: {act_time}')
                db.dec_usage(act_time, 1, txt=act_action['dbg_id'])
        else:
            logger.critical(f'action *{act["type"]}* not supported')
            sys.exit(-1)

    def vgprAction(self, act: dict, db: Database):
        '''command parsing function for vgpr_size resource'''
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)

    def useraccumAction(self, act: dict, db: Database):
        '''command parsing function for user_accum_cntrb resource'''
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)


class Cu(Dev):
    '''cu device'''
    def __init__(self, id: int = 0, Simd_num: int = 2, dn_pre=''):
        # construct device name from id
        if dn_pre:
            dn_pre = f'{dn_pre}.'
        dn = f'{dn_pre}cu.{str(id)}'
        super().__init__(dn, id)
        # specific resource
        self.dev_num = Simd_num
        self.add_res('lds_size', self.ldsAction, 400)
        self.add_res('barrier_id', self.barrierAction, 32)
        self.add_res('bulky', self.bulkyAction, 1)
        # indirect resource
        self.add_res('wv_id', None, 16*Simd_num,)
        self.add_res('vgpr_size', None, 64*Simd_num,)
        self.add_res('user_accum_cntrb', None, 100*Simd_num,)
        # devices in the device
        for idx in range(Simd_num):
            self.get_dev_list().append(Simd32(idx, dn))

    def ldsAction(self, act: dict, db: Database):
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)

    def barrierAction(self, act: dict, db: Database):
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)

    def bulkyAction(self, act: dict, db: Database):
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)

    def act_pre(self, act: dict):
        '''preprocessing cu action'''
        # release bulky if bulky_deaclloc_en
        if act['type'] == ACT_DONE:
            if act['action']['bulky_dealloc_en'] == '1':
                act['action'].update({'bulky': '1'})
            else:
                act['action'].update({'bulky': '0'})
            logger.debug(f"update bulky: {act}")
        return act


class Wgp(Dev):
    '''Wgp device'''
    def __init__(self, id: int = 0, Cu_num: int = 2,
                 Simd_num: int = 2, dn_pre='',):
        # construct device name from id
        if dn_pre:
            dn_pre = f'{dn_pre}.'
        dn = f'{dn_pre}wgp.{str(id)}'
        super().__init__(dn, id)
        # specific resource
        self.dev_num = Cu_num
        self.add_res('tmprng_id', self.tmprngAction, 32*self.dev_num)
        # indirect resource
        self.add_res('lds_size', None, 2*self.dev_num)
        self.add_res('barrier_id', None, 32*self.dev_num)
        self.add_res('bulky', None, 1*self.dev_num)
        self.add_res('wv_id', None, 16*Cu_num*Simd_num,)
        self.add_res('vgpr_size', None, 64*Cu_num*Simd_num,)
        self.add_res('user_accum_cntrb', None, 100*Cu_num*Simd_num,)
        # devices in the device
        for idx in range(self.dev_num):
            self.get_dev_list().append(Cu(idx, Simd_num, dn))

    def tmprngAction(self, act: dict, db: Database):
        # TODO: add function
        act_time = act['time']
        db.ext_last_sample(act_time)


class Sa(Dev):
    '''Sa device'''
    def __init__(self, id: int = 0, Wgp_num: int = 3,
                 Cu_num: int = 2, Simd_num: int = 2, dn_pre='',):
        # construct device name from id
        if dn_pre:
            dn_pre = f'{dn_pre}.'
        dn = f'{dn_pre}sa.{str(id)}'
        super().__init__(dn, id)
        # specific resource
        self.dev_num = Wgp_num
        # No specific resource
        # indirect resource
        self.add_res('tmprng_id', None, 32*Cu_num*self.dev_num)
        self.add_res('lds_size', None, 2*Cu_num*self.dev_num)
        self.add_res('barrier_id', None, 32*Cu_num*self.dev_num)
        self.add_res('bulky', None, 1*Cu_num*self.dev_num)
        self.add_res('wv_id', None, 16*Cu_num*Simd_num*self.dev_num,)
        self.add_res('vgpr_size', None, 64*Cu_num*Simd_num*self.dev_num,)
        self.add_res('user_accum_cntrb', None,
                     100*Cu_num*Simd_num*self.dev_num,)
        # devices in the device
        for idx in range(self.dev_num):
            self.get_dev_list().append(Wgp(idx, Cu_num, Simd_num, dn))


class LogDevice:
    '''object to simulate the Shadder Engine'''
    def __init__(self, n_sa: int = 2, n_wgp: int = 3,
                 n_cu: int = 2, n_simd: int = 2):
        # instantiate a list of Sa
        self.dev = []
        logger.debug(f'sa: {n_sa}, wgp: {n_wgp}, cu: {n_cu}, simd: {n_simd}')
        self.config(n_sa, n_wgp, n_cu, n_simd)

    def run(self, action):
        # - run command from LogParser
        # - update resource status
        logger.info('run cmd')
        for inst in self.dev:
            logger.info(f'run time:{action["time"]} in {inst.get_dn()}')
            #inst.res_alloc(action)
            inst.res_mgr(action)

    def config(self, n_sa: int = 2, n_wgp: int = 3,
               n_cu: int = 2, n_simd: int = 2):
        # config resource in shadder engine
        self.dev = []
        logger.debug(f'sa: {n_sa}, wgp: {n_wgp}, cu: {n_cu}, simd: {n_simd}')
        for idx in range(n_sa):
            self.dev.append(Sa(idx, n_wgp, n_cu, n_simd))

    def get_sa(self, sa):
        '''get SA'''
        # TODO: check illegal index
        return self.dev[sa]

    def get_wgp(self, sa, wgp):
        '''get wgp'''
        # TODO: check illegal index
        return self.dev[sa].get_dev(wgp)

    def get_cu(self, sa, wgp, cu):
        '''get cu'''
        # TODO: check illegal index
        return self.dev[sa].get_dev(wgp).get_dev(cu)

    def get_simd(self, sa, wgp, cu, simd):
        '''get simd'''
        # TODO: check illegal index
        return self.dev[sa].get_dev(wgp).get_dev(cu).get_dev(simd)
