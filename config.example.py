from base64 import b64encode

WALLET = {
    'url': 'http://localhost:64763',
    'userPass': b64encode(b"TODO WALLET USER : PASSWORD GOES HERE").decode("ascii"),
    'decrypt_pass': 'password',
}
PKTD = {
    'url': 'http://192.168.2.51:64765',
    'userPass': b64encode(b"TODO PKTD USER : PASSWORD GOES HERE").decode("ascii"),
}
MULTISIGS = {
    'ns': {
        'm': 3,
        'keys': [
            'Zpub6yhuP7EAUvHMD93Ceu4PGDE86zAzPGz3ZgWizgV3anasihU2qPPs9ec1U2WntBxuSmEdj42LWrHvB2RX1nFNdfaBJUb5vWgysvFuFkDoLsn',
            'Zpub6yt9oJkcseap5mLKarQ7hAK1ULGGAqRuYBgqY198MBmQ2mYpc6w4U9fyCFyniaQbgQcRRGKbbQhcn93dEXZn79dRtxkcB1henE4xAJGAyuh',
            'Zpub6xjHZeTc5PcMdcwj6rriBAajcGgZ2M9qi9yTcaR9CeM4yUTi7N7xji6sKRyohABmFtMN6KkAhBQheRKQBWawTAXCMBWVGGMiKXj1ku6wZga',
            'Zpub6ytA3HwmyULpysGgM5bMkCQcVzxxrLBXvGqJdR7VQFGSqDoBNvJFJW5M3ppF3a5xgTU1A3A4mZMXoc7PHtLQaZgLAwfiLJzL6goSJuwLodP',
            'Zpub6xvbH2BzG22zeXEEBb7kmQtrxPvAFjw7DNKgoVWh1jbPiEtuwV6Y8XaSiSdSh2eAJKBaPA4qgaYzrhtP7nEVemBQk644zu671DyyiL79bvv',
        ],
        'address': "pkt1q6hqsqhqdgqfd8t3xwgceulu7k9d9w5t2amath0qxyfjlvl3s3u4sjza2g2"
    }
}
