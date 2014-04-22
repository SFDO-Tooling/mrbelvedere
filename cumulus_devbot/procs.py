import django_rq
from hirefire.procs.rq import RQProc

class WorkerProc(RQProc):
    name = 'worker'
    queues = ['default',]

    def __init__(self, *args, **kwargs):
        self.connection = django_rq.get_connection('default')
        super(WorkerProc, self).__init__(*args, **kwargs)
