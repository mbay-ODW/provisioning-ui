#!/usr/bin/python3
# coding=utf-8
from flask import Flask, flash, request, redirect, render_template, send_file
import logging
import subprocess
import time


#logFile = './Logs/registration.log'
logger = logging.getLogger('Upload Server Logging')
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.info('Logger for registration UI was initialized')

app = Flask(__name__,static_url_path='/static')
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super-secret-key'


def configuration(deviceID,tenantURL,username,password):
    try:
        logging.debug('Starting certification creation via subprocess')
        createCertification = subprocess.Popen(["tedge", "cert", "create", "--device-id", deviceID],stdout=subprocess.PIPE)
        createCertification.wait()
        logging.debug('Received the following feedback from certification create: %s' % (createCertification.stdout.read()))
        logging.debug('Starting config set of tenant url creation via subprocess')
        tenantConfig = subprocess.Popen(["tedge", "config", "set", "c8y.url", tenantURL],stdout=subprocess.PIPE)
        tenantConfig.wait()
        logging.debug('Received the following feedback from tenant configuration: %s' % (tenantConfig.stdout.read()))
        sessionCreate = subprocess.Popen(["c8y","session", "create", "--username", username, "--host", tenantURL, "--password", password, "--name", "lokal"],stdout=subprocess.PIPE)
        sessionCreate.wait()
        logging.debug('Received the following feedback from creating the session file: %s' % (sessionCreate.stdout.read()))
        sessionSet = subprocess.Popen(["set-session","lokal"],stdout=subprocess.PIPE)
        sessionSet.wait()
        logging.debug('Received the following feedback from setting the session file: %s' % (sessionSet.stdout.read()))
        upload = subprocess.Popen(["c8y","devicemanagement", "certificates", "create", "--file", "/etc/tedge/cert/...", "--force"],stdout=subprocess.PIPE)
        upload.wait()
        logging.debug('Received the following feedback from upload cert: %s' % (upload.stdout.read()))
        start = subprocess.Popen(["tedge", "connect", "c8y"],stdout=subprocess.PIPE)
        start.wait()
        logging.debug('Received the following feedback from starting: %s' % (start.stdout.read()))
    except Exception as e:
       logging.error("The following error occured: %s" % (e))

def reset():
    try:
        stop = subprocess.Popen(["tedge", "disconnect", "c8y"],stdout=subprocess.PIPE)
        stop.wait()
        logging.debug('Received the following feedback from stopping: %s' % (stop.stdout.read()))
        cert = subprocess.Popen(["tedge", "cert", "remove"],stdout=subprocess.PIPE)
        cert.wait()
        logging.debug('Received the following feedback from deleting cert: %s' % (cert.stdout.read()))
        sessionDelete = subprocess.Popen(["rm", "~/.cumulocity/*"],stdout=subprocess.PIPE)
        sessionDelete.wait()
        logging.debug('Received the following feedback from deleting the session: %s' % (sessionDelete.stdout.read()))
    except Exception as e:
       logging.error("The following error occured: %s" % (e))


@app.route('/home', methods=['GET', 'POST'])
def home():
   try: 
        logging.debug('Received the following request: %s'%(request))
        logging.debug('Received the following request method: %s'%(request.method))
        if request.method == 'GET':
            logging.info('GET received, returning home.html')
        if request.method == 'POST':
            logging.info('POST received')
            if request.form.get('reset'):
                reset()
            elif request.form.get('connect'):
                logger.debug("Starting connect")
                tenantURL = request.values['Tenant-URL']
                logging.debug('Tenant URL is: %s'%(tenantURL))
                if len(tenantURL) == 0:
                    flash('Tenant URL not allowed to be empty.')
                deviceID = request.values['Device-ID']
                logging.debug('Device ID is: %s'%(deviceID))
                if len(deviceID) == 0:
                    flash('Device ID not allowed to be empty.')
                username = request.values['Username']
                logging.debug('Username is: %s'%(username))
                if len(username) == 0:
                    flash('Username not allowed to be empty.')
                password = request.values['Password']
                logging.debug('Password is: %s'%(password))
                if len(password) == 0:
                    flash('Password not allowed to be empty.')
                logging.info('Starting configuration')
                configuration(deviceID,tenantURL,username,password)
                logging.info('Done, returning download.html')
            else:
                logger.error("Unkown Post request")
   except Exception as e:
       logging.error("The following error occured: %s" % (e))
   finally:
       return render_template('./home.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)