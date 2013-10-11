from django.http import HttpResponse
import django_rq

@django_rq.job
def run_sauce_job():
    print 'EXECUTED!'

def dev_new(request):
    return HttpResponse(run_sauce_job.delay())

