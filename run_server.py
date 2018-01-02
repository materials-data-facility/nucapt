from nucapt import app
import os

if os.path.isdir('ssl'):
    context = ('./ssl/nucaptdms.ms.northwestern.edu.cer',
               './ssl/nucaptdms.ms.northwestern.edu.key')
else:
    context = 'ad_hoc'

if __name__ == '__main__':
    app.run(host='0.0.0.0', ssl_context=context)
