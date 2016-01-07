#!/usr/bin/env python

import smtplib
from email.mime.text import MIMEText

import braintree,json
from flask import Flask,request
from flask.ext.cors import CORS

conf = json.loads(open('config.json','r').read())

origin = None

if conf['environment'] == 'sandbox':
    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      merchant_id=conf['sandbox-merchant-id'],
                                      public_key=conf['sandbox-pubkey'],
                                      private_key=conf['sandbox-privkey'],
                                      )
    origin = conf['sandbox-origin']

else:
    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      merchant_id=conf['merchant-id'],
                                      public_key=conf['pubkey'],
                                      private_key=conf['privkey'],
                                      )
    origin = conf['origin']


app = Flask(__name__, static_url_path='')

CORS(app, resources = {r'*':{'origins':origin}})

index = open('index.html').read()

@app.route('/')
def root():
    return index


@app.route('/client_token', methods=['GET'])
def client_token():
    return braintree.ClientToken.generate();


@app.route('/checkout', methods=['POST'])
def create_purchase():
    trans = request.json
    nonce = trans.get('nonce','asdfghjkl')
    name = trans.get('name', None)
    if name is None:
        return json.dumps({'status':'fail', 'errors':['No name supplied']})
    name = name[0:50]
    result = braintree.Transaction.sale({
        'amount':'5.00',
        'payment_method_nonce': nonce
        })
    if result.is_success:
        return json.dumps({'status':'success', 'name':name})
    else:
        return json.dumps({'status':'fail', 'errors': [x.message for x in result.errors.deep_errors]})

if __name__ == '__main__':
    """
    msg = MIMEText('\ntest email\n')
    msg['Subject'] = 'thanks for your purchase'
    msg['From'] = 'noreply@conorpp.com'
    msg['To'] = 'conorpp@vt.edu'

    s = smtplib.SMTP('localhost')
    s.sendmail('noreply@conorpp.com', 'conorpp@vt.edu', msg.as_string())

    print 'send mail?'
    """

    app.run(host='127.0.0.1')
