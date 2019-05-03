import os
from flask import Flask, abort, redirect

app = Flask(__name__)

REDIRECTS = {
    'hed': 'https://install.salesforce.org/products/eda/install',
    'npsp': 'https://install.salesforce.org/products/npsp/install',
    'npsp_reports': 'https://install.salesforce.org/products/npsp/reports',
    'sfal': 'https://install.salesforce.org/products/sal/install',
}

@app.route('/mpinstaller/<project>/')
@app.route('/mpinstaller/<project>/<version>/')
def redirect_view(project, version=None):
    target = REDIRECTS.get(project)
    if target:
        return redirect(target, code=301)
    return abort(404)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
