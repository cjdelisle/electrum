#!/usr/bin/env python3
import sys
import hashlib
import getpass
import json
import os
import logging
import codecs
from electrum.logging import console_stderr_handler
from electrum.transaction import Transaction
from electrum.transaction import tx_from_str
from electrum import keystore
from electrum.storage import WalletStorage
from electrum.wallet import Multisig_Wallet
import pkt_constants
pkt_constants.load()

CONFIG_FILE = "./config.json"


## Testing seed:
## kick mouse drill book wagon sudden ship rifle corn patch announce leisure
## Zpub6yv5s7ac6bDbCrMxaugzYMX66jDRnxvXgxYrWucUk6L4dc9UUv9RWb581MpfaUE5Bdy9rbUFWsnGVNWFKPLYRyt4weHfTjdEs6Xfm3nCvnQ

## Zpub6yhuP7EAUvHMD93Ceu4PGDE86zAzPGz3ZgWizgV3anasihU2qPPs9ec1U2WntBxuSmEdj42LWrHvB2RX1nFNdfaBJUb5vWgysvFuFkDoLsn

m = 3
NS_KEYS = [
    'Zpub6yhuP7EAUvHMD93Ceu4PGDE86zAzPGz3ZgWizgV3anasihU2qPPs9ec1U2WntBxuSmEdj42LWrHvB2RX1nFNdfaBJUb5vWgysvFuFkDoLsn',
    'Zpub6yt9oJkcseap5mLKarQ7hAK1ULGGAqRuYBgqY198MBmQ2mYpc6w4U9fyCFyniaQbgQcRRGKbbQhcn93dEXZn79dRtxkcB1henE4xAJGAyuh',
    'Zpub6xjHZeTc5PcMdcwj6rriBAajcGgZ2M9qi9yTcaR9CeM4yUTi7N7xji6sKRyohABmFtMN6KkAhBQheRKQBWawTAXCMBWVGGMiKXj1ku6wZga',
    'Zpub6ytA3HwmyULpysGgM5bMkCQcVzxxrLBXvGqJdR7VQFGSqDoBNvJFJW5M3ppF3a5xgTU1A3A4mZMXoc7PHtLQaZgLAwfiLJzL6goSJuwLodP',
    'Zpub6xvbH2BzG22zeXEEBb7kmQtrxPvAFjw7DNKgoVWh1jbPiEtuwV6Y8XaSiSdSh2eAJKBaPA4qgaYzrhtP7nEVemBQk644zu671DyyiL79bvv',
]
NS_ADDRESS = "bc1q6hqsqhqdgqfd8t3xwgceulu7k9d9w5t2amath0qxyfjlvl3s3u4st4nj3u"
def wallet(ks0):
    ws = WalletStorage("/tmp/fakewallet")
    ws.put('wallet_type', "%dof%d" % (m, len(NS_KEYS)))
    ksmp = ks0.get_master_public_key()
    ok = False
    for i, k in enumerate(NS_KEYS):
        if ksmp == k:
            ks = ks0
            ok = True
        else:
            ks = keystore.from_master_key(k)
        ws.put('x%d/' % (i + 1), ks.dump())
    if not ok:
        print("WARNING: Your pubkey does not appear in the multisig group")
    return Multisig_Wallet(ws)

def password_stretch(password, config):
    if 'password_stretch' in config:
        if config['password_stretch'] == 'pbkdf2':
            return hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                b'pass',
                100000
            ).hex()
        raise TypeError("unknown password hash type " + str(config['password_stretch']))
    return hashlib.scrypt(
        password.encode('utf-8'),
        salt=b'pass',
        n=2**17, r=8,
        p=1,
        dklen=32,
        maxmem=2**28
    ).hex()

def outfile_exists(file):
    if os.path.exists(file):
        print(file + " already exists, I'm not confident enough to overwrite it")
        return True

def combiner(txcount, transactions_bin, cnum, numCombiners, f):
    for txnum in range(0,txcount):
        if txnum % numCombiners != cnum:
          continue
        logheader = "[" + str(cnum) + "] Merging " + str(txnum) + "/" + str(txcount)
        print(logheader)
        transactions = []
        for i in range(0,len(transactions_bin)):
            print(logheader + " Parsing transaction " + str(i+1) + "/" + str(len(transactions_bin)))
            txb64 = transactions_bin[i][txnum]
            txhex = codecs.encode(codecs.decode(txb64.encode(), 'base64'), 'hex').decode()
            tx = Transaction(tx_from_str(txhex))
            tx.inputs()
            transactions.append(tx)
        tx0 = transactions[0]
        print(logheader + " Deserializing transaction")
        tx0.deserialize(True)
        txn = 0
        for tx in transactions[1:]:
            i = 0
            print(logheader + " Copying signatures from from transaction " + str(txn))
            txn += 1
            for txin in tx.inputs():
                #print("      From input " + str(i))
                signingPos = 0
                for sig in txin['signatures']:
                    if sig != None:
                        tx0.add_signature_to_txin(i, signingPos, sig)
                    signingPos += 1
                i += 1
        res = tx0.serialize_to_network()
        f.write(codecs.encode(codecs.decode(res, 'hex'), 'base64').decode().replace("\n", "") + '\n')

def multi_combine(transactions_bin, outfile, config):
    if outfile_exists(outfile): return
    f = open(outfile, 'w')
    print("Parsing transactions")
    txcount = None
    for i in range(0,len(transactions_bin)):
        if txcount != None and txcount != len(transactions_bin[i]):
            print("WARNING: file " + str(i) + " has " + str(len(transactions_bin[i])) +
                " transactions but " + str(i-1) + " has " + str(txcount))
        txcount = len(transactions_bin[i])
        transactions_bin[i].sort()
    numsigners = 10
    if 'numsigners' in config:
        numsigners = config['numsigners']
    pids = []
    for x in range(0,numsigners):
        print("Forking combiner number " + str(x))
        newpid = os.fork()
        if newpid == 0:
              combiner(txcount, transactions_bin, x, numsigners, f)
              print("[" + str(x) + "] Done")
              sys.exit(0)
        pids.append(newpid)
    for pid in pids:
        os.waitpid(pid, 0)
    f.close()
    print("Result written to " + outfile)

def combine_transactions(transactions_bin, outfile):
    if outfile_exists(outfile): return
    f = open(outfile, 'w')
    print("Parsing transactions")
    txcount = None
    for i in range(0,len(transactions_bin)):
        if txcount != None and txcount != len(transactions_bin[i]):
            print("WARNING: file " + str(i) + " has " + str(len(transactions_bin[i])) +
                " transactions but " + str(i-1) + " has " + str(txcount))
        txcount = len(transactions_bin[i])
        transactions_bin[i].sort()
    for txnum in range(0,txcount):
        print("Merging " + str(txnum) + "/" + str(txcount))
        transactions = []
        for i in range(0,len(transactions_bin)):
            print("  Parsing transaction " + str(i) + "/" + str(len(transactions_bin)))
            txb64 = transactions_bin[i][txnum]
            txhex = codecs.encode(codecs.decode(txb64.encode(), 'base64'), 'hex').decode()
            tx = Transaction(tx_from_str(txhex))
            tx.inputs()
            transactions.append(tx)
        tx0 = transactions[0]
        print("  Deserializing transaction 0")
        tx0.deserialize(True)
        print("  Copying signatures")
        txn = 0
        for tx in transactions[1:]:
            i = 0
            print("    From transaction " + str(txn))
            txn += 1
            for txin in tx.inputs():
                #print("      From input " + str(i))
                signingPos = 0
                for sig in txin['signatures']:
                    if sig != None:
                        tx0.add_signature_to_txin(i, signingPos, sig)
                    signingPos += 1
                i += 1
        res = tx0.serialize_to_network()
        f.write(codecs.encode(codecs.decode(res, 'hex'), 'base64').decode().replace("\n", "") + '\n')
    f.close()
    print("Result written to " + outfile)

#console_stderr_handler.setLevel(logging.DEBUG)

def signer(w, ks, key, txns, signum, numsigners, f):
    i = 0
    for tx in txns:
        if i % numsigners != signum:
            i += 1
            continue
        print("[" + str(signum) + "] Signing transaction " + str(i) + "/" + str(len(txns)))
        i += 1
        for txin in tx.inputs():
            w.add_input_info(txin)
        ks.sign_transaction(tx, key)
        f.write(codecs.encode(codecs.decode(tx.serialize(), 'hex'), 'base64').decode().replace("\n", "") + '\n')

def sign_txns(config, txns, outfile):
    f = open(config['seedpath'], 'r')
    ks = keystore.BIP32_KeyStore( json.loads(f.read()) )
    f.close()
    passwd = getpass.getpass("Enter your signing password: ")
    print("You can now safely remove your external storage containing the seed file")
    print("Creating wallet")
    w = wallet(ks)
    key = password_stretch(passwd, config)
    f = open(outfile, 'w')
    numsigners = 10
    if 'numsigners' in config:
        numsigners = config['numsigners']
    pids = []
    for x in range(0,numsigners):
        print("Forking signer number " + str(x))
        newpid = os.fork()
        if newpid == 0:
              signer(w, ks, key, txns, x, numsigners, f)
              print("[" + str(x) + "] Done")
              sys.exit(0)
        pids.append(newpid)
    for pid in pids:
        os.waitpid(pid, 0)
    f.close()
    print("Signed transactions written to " + outfile)

def prompt_to_sign(config, lines, filename):
    outfile = filename.replace('.b64', '') + "_signed_" + config['name'] + '.b64'
    if outfile_exists(outfile): return
    txns = []
    i = 0
    for l in lines:
        print("Parsing transaction " + str(i) + "/" + str(len(lines)))
        i += 1
        hexl = codecs.encode(codecs.decode(l.encode(), 'base64'), 'hex').decode()
        tx = Transaction(tx_from_str(hexl))
        tx.outputs()
        txns.append(tx)
    print("these transactions will:")
    outputs = {}
    for tx in txns:
        for o in tx.outputs():
            if not o.address in outputs:
                outputs[o.address] = 0
            outputs[o.address] += o.value / 0x40000000
    for k in outputs:
        print("  * pay " + k + " " + str(outputs[k]) + " PKT")
    while True:
        yn = input("Do you want to sign? [y/n] ")
        if yn == 'n':
            print("Ok, bye")
            return
        if yn == 'y':
            sign_txns(config, txns, outfile)
            return
        print("Your choices are 'y' or 'n'")

def configure_seed(config):
    if outfile_exists(config['seedpath']): return
    seed = input("Type your seed words: ")
    passwd = ''
    while True:
        passwd = getpass.getpass("Enter your signing password: ")
        passwd2 = getpass.getpass("Confirm your signing password: ")
        if passwd != passwd2:
            print("passwords do not match")
            continue
        break
    ks0 = keystore.from_seed(seed, '', True)
    ks0.update_password(None, password_stretch(passwd, config))
    f = open(config['seedpath'], 'w')
    f.write(json.dumps(ks0.dump()))
    f.close()
    print(config['seedpath'] + " written")
    print("Your master public key is " + ks0.get_master_public_key())

def usage():
    print("Usage: ./sign_tx.py seed                                  # configure your seed")
    print("       ./sign_tx.py sign /path/to/transaction/file.hex    # sign a transaction")
    print("       ./sign_tx.py combine /path/to/tx1 /path/to/tx2 /path/to/output")
    print("                                                          # combine partial signed transactions")

def mk_config():
    print("There is now a config.json file")
    print("It will contain the path to your seed file and a name which will be appended")
    print("to the signed output in order to simplify merging.")
    print()
    print("Since you don't currently have a config.json, I will make one for you.")
    name = input("Please type your name (this will be appended to your signed outputs): ")
    seedpath = ""
    try:
        seedpath = os.environ['SEED_FILE']
    except:
        pass
    while seedpath != "":
        yn = input("Is [" + seedpath + "] the correct path to your seed file? [y/n] ")
        if yn == 'y':
            break
        if yn == 'n':
            seedpath = ""
            break
        print("I don't understand your reply, it should be y or n")
    if seedpath == "":
        seedpath = input("Please type the path to your seed file: ")
    f = open(CONFIG_FILE, 'w')
    f.write(json.dumps({ 'name': name, 'seedpath': seedpath, 'password_stretch': 'pbkdf2' }))
    f.close()
    print("Thanks, now I will now continue as normal")
    print()

def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'redeemscript':
       w = wallet()
       print(w.get_redeem_script(NS_ADDRESS))
       return
    if not os.path.exists(CONFIG_FILE):
        mk_config()
    f = open(CONFIG_FILE, 'r')
    config = json.loads(f.read())
    f.close()
    if len(sys.argv) > 4 and sys.argv[1] == 'combine':
        txs = []
        for i in range(2,len(sys.argv)-1):
            with open(sys.argv[i], 'r') as file:
                print("Reading transactions from " + sys.argv[i])
                lines = file.read().splitlines()
                txs.append(lines)
        #combine_transactions(txs, sys.argv[len(sys.argv)-1])
        multi_combine(txs, sys.argv[len(sys.argv)-1], config)
        return
    if len(sys.argv) == 3 and sys.argv[1] == 'sign':
        if len(sys.argv) < 3:
            usage()
            return
        if not os.path.exists(config['seedpath']):
            print(config['seedpath'] + " does not exist, perhaps it's on external storage ?")
            return
        filename = sys.argv[2]
        with open(filename, 'r') as file:
            lines = file.read().splitlines()
            prompt_to_sign(config, lines, filename)
            return
    if len(sys.argv) == 2 and sys.argv[1] == 'seed':
        configure_seed(config)
        return
    usage()
main()
