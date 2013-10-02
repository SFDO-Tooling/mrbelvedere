from django.http import HttpResponse
import json

GITHUB_WHITELIST = [
    '204.232.175.',
    '192.30.252.',
]

def github_webhook(request):
    is_github = False
    for subnet in GITHUB_WHITELIST:
        if subnet in request.META['REMOTE_ADDR']:
            is_github = True
            break
    if not is_github:
        # FIXME: raise unauthorized
        return HttpResponse('You are not Github, go away!')
    
    data = json.loads(request.POST['payload'])

    from jenkinsapi.jenkins import Jenkins
    J = Jenkins('http://23.20.64.21')
    J['Cumulus_feature']
    branch = data['ref'].replace('refs/heads','origin')
        
    # Only invoke build if the branch is not dev (i.e. it is a feature branch)
    if branch != 'origin/dev':
        J['Cumulus_feature'].invoke(securitytoken='l8fOdDKfSb7c', build_params={'branch': branch})

    return HttpResponse('OK')
    
    
