#!/usr/bin/env python

import smtplib
from email.mime.text import MIMEText
from validate_email import validate_email

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

emailapp = smtplib.SMTP('smtp.gmail.com',587)
emailapp.ehlo()
emailapp.starttls()
emailapp.login(conf['gmail-username'], conf['gmail-password'])

def send_receipt(to, name, amount,):
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

    emailapp.sendmail('noreply@conorpp.com', to, msg.as_string())


@app.route('/')
def root():
    return index


@app.route('/b/client_token', methods=['GET'])
def client_token():
    return braintree.ClientToken.generate();


@app.route('/b/checkout', methods=['POST'])
def create_purchase():
    try:
        amount = '0.50'
        trans = request.json
        nonce = trans.get('nonce','asdfghjkl')
        name = trans.get('name', None)

        if name is None:
            return json.dumps({'status':'fail', 'errors':['No name supplied']})
        name = name[0:50]
        
        email = trans.get('email', '')
        is_valid = validate_email(email)

        if not is_valid:
            return json.dumps({'status':'fail', 'errors':['Email is invalid']})
        print 'valid'

        result = braintree.Transaction.sale({
            'amount':amount,
            'payment_method_nonce': nonce
            })

        if result.is_success:
            send_receipt(email,name,amount)
            return json.dumps({'status':'success', 'name':name})
        else:
            return json.dumps({'status':'fail', 'errors': [x.message for x in result.errors.deep_errors]})
    except Exception as e:
        print 'exception: ',e



if __name__ == '__main__':

    app.run(host='127.0.0.1')
