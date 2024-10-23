from urllib import request
from electrum.transaction import Transaction
from electrum.transaction import tx_from_str
import ssl
import json
import sys
import codecs
import pprint
import os
from base64 import b64encode
import config

multisig = config.MULTISIGS['ns']

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

gcontext = ssl.SSLContext()
gcontext.verify_mode = ssl.CERT_NONE

def req(server, method, args):
    data=json.dumps({
      "jsonrpc":"1.0",
      "id":"txid",
      "method":method,
      "params":args
    })
    #eprint(data)
    req = request.Request(server['url'],
        data=data.encode(),
        headers={
            'Authorization': 'Basic ' + server['userPass']
        }
    )
    f = request.urlopen(req, context=gcontext)
    page = f.read()
    obj = json.loads(page)
    if obj['error'] != None:
        eprint(obj['error'])
        #raise TypeError
    return obj['result']

def mk_tx(amount, payTo, lockName):
    # createtransaction "toaddress" amount (["fromaddress",...] electrumformat "changeaddress" inputminheight minconf=1 vote)
    return req(config.WALLET, "createtransaction", [
        payTo,
        amount,
        [multisig['address']], # from address
        True,
        multisig['address'], # change address
        1, # inputminheight, passing >0 makes it prefer oldest
        0, # minconf
        False, # vote
        500, # maxinputs
        lockName, # autolock
        True, # nosign
    ])

def passwd():
    req(config.WALLET, "walletpassphrase", [ config.WALLET['decrypt_pass'], 30000000 ])

def mk_transactions(amount, payTo):
    lockName = 'pay-' + str(amount) + '-to-' + payTo + '-' + str(os.getpid())
    eprint("Lock name: " + lockName)
    i = 0
    while amount > 0:
        tx = mk_tx(amount, payTo, lockName)
        etx = Transaction(tx_from_str(tx))
        v = int(etx.output_value()) / 0x40000000
        amount -= v
        eprint("Transaction " + str(i) + ' ' + str(v) + ' - ' + str(amount) + ' remains')
        print(codecs.encode(codecs.decode(tx, 'hex'), 'base64').decode().replace("\n", ""))
        i += 1

def post_tx(filename):
    with open(filename, 'r') as file:
        lines = file.read().splitlines()
        for l in lines:
            txhex = codecs.encode(codecs.decode(l.encode(), 'base64'), 'hex').decode()
            elecTx = Transaction(tx_from_str(txhex))
            txid = elecTx.txid()
            eprint(txid)
#            continue
            res = req(config.PKTD, "sendrawtransaction", [ txhex ])
            if res != txid:
                eprint('mismatch, got: ' + str(res))

# post_tx("transaction_example_combined.b64")

passwd()
mk_transactions(16000000, 'pkt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqjqwgj3')
