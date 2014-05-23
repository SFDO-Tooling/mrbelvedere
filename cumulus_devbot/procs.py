import django_rq
from rq.worker import Worker
from hirefire.procs.rq import RQProc

class WorkerProc(RQProc):
    name = 'worker'
    queues = ['default',]

    def __init__(self, *args, **kwargs):
        self.connection = django_rq.get_connection('default')
        super(WorkerProc, self).__init__(*args, **kwargs)

    def quantity(self):
        """
        Returns the aggregated number of tasks of the proc queues.
        """
        count = sum([client.count for client in self.clients])

        # Add any workers which are currently working jobs
        all_workers = Worker.all(connection=self.connection)
        for worker in all_workers:
            if worker.get_current_job():
                count += 1
        
        return count
