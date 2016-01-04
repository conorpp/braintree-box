#!/usr/bin/env python

import braintree,json
from flask import Flask,request

conf = json.loads(open('config.json','r').read())



if conf['environment'] == 'sandbox':
    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      merchant_id=conf['sandbox-merchant-id'],
                                      public_key=conf['sandbox-pubkey'],
                                      private_key=conf['sandbox-privkey'],
                                      )
else:
    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      merchant_id=conf['merchant-id'],
                                      public_key=conf['pubkey'],
                                      private_key=conf['privkey'],
                                      )

app = Flask(__name__)



@app.route('/')
def hello():
    return 'Hello World!'



@app.route('/client_token', methods=['GET'])
def client_token():
    return request.args.get('callback')+'("' +braintree.ClientToken.generate() + '")';



@app.route('/checkout', methods=['POST'])
def create_purchase():
    nonce = request.form['payment_method_nonce']
    result = braintree.Transaction.sale({
            'amount':'10.00',
            'payment_method_nonce': nonce
        })
    print 'got result' , result



if __name__ == '__main__':
    app.run(host='127.0.0.1')
