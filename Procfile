web: newrelic-admin run-program gunicorn cumulus_devbot.wsgi
worker: python manage.py rqworker default --worker-class mpinstaller.worker.RequeueingWorker
