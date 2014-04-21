from hirefire.procs.rq import RQProc

class WorkerProc(RQProc):
    name = 'worker'
    queues = ['default',]
