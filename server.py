#!/usr/bin/env python

import smtplib
from email.mime.text import MIMEText
from validate_email import validate_email

import braintree,json
from flask import Flask,request
from flask.ext.cors import CORS

import sys

if len(sys.argv) < 2:
    print 'usage: %s <config> [debug]' % sys.argv[0]
    sys.exit(1)

conf = json.loads(open(sys.argv[1],'r').read())

origin = None
emailapp = None

if conf['environment'] == 'sandbox':
    debug = True
    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      merchant_id=conf['sandbox-merchant-id'],
                                      public_key=conf['sandbox-pubkey'],
                                      private_key=conf['sandbox-privkey'],
                                      )
    origin = conf['sandbox-origin']

else:
    braintree.Configuration.configure(braintree.Environment.Production,
                                      merchant_id=conf['merchant-id'],
                                      public_key=conf['pubkey'],
                                      private_key=conf['privkey'],
                                      )
    origin = conf['origin']


app = Flask(__name__, static_url_path='')

CORS(app, resources = {r'*':{'origins':origin}})

def connect_to_email():
    s = smtplib.SMTP('smtp.gmail.com',587)
    s.ehlo()
    s.starttls()
    s.login(conf['gmail-username'], conf['gmail-password'])
    return s


def send_receipt(to, name, amount,):
    global emailapp
    body = """%s,

Thank you for your participation.  You have been charged $%s.

If you are receiving this in error or you have regrets, please send an email to conorpp94@gmail.com for a refund.

Best,
Conor
https://conorpp.com
""" % (name, amount)
    msg = MIMEText(body)
    msg['Subject'] = 'Thanks for your participation on conorpp.com'
    msg['From'] = 'noreply@conorpp.com'
    msg['To'] = to
    if not app.debug: 
        try:
            emailapp.sendmail('noreply@conorpp.com', to, msg.as_string())
        except:
            emailapp = connect_to_email()
            emailapp.sendmail('noreply@conorpp.com', to, msg.as_string())



@app.route('/')
def root():
    index = open('index.html').read()
    return index


@app.route('/b/client_token', methods=['GET'])
def client_token():
    return braintree.ClientToken.generate();


@app.route('/b/checkout_10c', methods=['POST'])
def checkout_top():
    return create_purchase(request, '0.10')

def create_purchase(req, amount):
    trans = req.json
    nonce = trans.get('nonce','asdfghjkl')
    name = trans.get('name', None)

    if name is None:
        return json.dumps({'status':'fail', 'errors':['No name supplied']})
    name = name[0:50]
    
    email = trans.get('email', '')
    is_valid = validate_email(email)

    if not is_valid:
        return json.dumps({'status':'fail', 'errors':['Email is invalid']})

    result = braintree.Transaction.sale({
        'amount':amount,
        'payment_method_nonce': nonce,
        'options': {
                'submit_for_settlement':True
            }
        })

    if result.is_success:
        send_receipt(email,name,amount)
        return json.dumps({'status':'success', 'name':name})
    else:
        if len(result.errors.deep_errors) == 0:
            return json.dumps({'status':'fail', 'errors': ['Payment method was not successful']})

        return json.dumps({'status':'fail', 'errors': [x.message for x in result.errors.deep_errors]})


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'debug':
        app.debug = True
        print 'debug running'
        app.run(host='0.0.0.0')
    else:
        emailapp = connect_to_email()
        app.run(host='127.0.0.1')
