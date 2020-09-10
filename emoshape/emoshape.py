import os
import socket
import subprocess
import time
import sys


class Emoshape:
    def __init__(self, host, port, secret, epuId=0):
        self.host = host
        self.port = port
        self.secret = secret
        self.epuId = epuId
        self.s = self._startConnetion()

    def _startConnetion(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, self.port))
            reply = ''
            while 'EPU_ON' not in reply:
                print(f' [x] Connect {self.epuId}')
                cmd = f'[EPUID]@>EPUInit cloud {self.secret}\r\n'
                s.send(str.encode(cmd))
                reply = str(s.recv(2048), 'utf-8')
                time.sleep(2)
            return s
        except socket.error as e:
            print("Unable to connect to EPU. " + str(e))
            sys.exit(-1)



    def closeConnection(self):
        cmd = '[EPUID]@>EPUClose\r\n'
        self.s.send(str.encode(cmd))
        reply = str(self.s.recv(2048), 'utf-8').strip()

    def sendMessage(self, msg):
        cmd = f'[EPUID]@>user ' + msg + '\r\n'
        self.s.send(str.encode(cmd))

    def toneOn(self, url, virtualMic):
        cmd = '@>tov_on\r\n'
        self.s.send(str.encode(cmd))
        reply = str(self.s.recv(2048), 'utf-8')

        cmd = f"ffmpeg -re -i /home/ngdust/Музыка/1.mp3 -f s16le -ar 8000 -ac 1 - > /home/ngdust/virtmic"
        os.system(cmd)

    def getChannels(self):
        buffer = []
        while len(buffer) < 2:
            cmd = f'[EPUID]@>buffer\r\n'
            self.s.send(str.encode(cmd))
            buffer = str(self.s.recv(2048), 'utf-8').split(',')
        channelEXCITED = int(buffer[4])
        channelCONFIDENT = int(buffer[14])
        channelHAPPY = int(buffer[24])
        channelTRUST = int(buffer[34])
        channelDESIRE = int(buffer[44])
        channelFEAR = int(buffer[54])
        channelSURPRISE = int(buffer[64])
        channelINATTENTION = int(buffer[74])
        channelSAD = int(buffer[84])
        channelREGRET = int(buffer[94])
        channelDISGUST = int(buffer[104])
        channelANGER = int(buffer[114])


        channel_dict = {
            'channelEXCITED': channelEXCITED,
            'channelCONFIDENT': channelCONFIDENT,
            'channelHAPPY': channelHAPPY,
            'channelTRUST': channelTRUST,
            'channelDESIRE': channelDESIRE,
            'channelFEAR': channelFEAR,
            'channelSURPRISE': channelSURPRISE,
            'channelINATTENTION': channelINATTENTION,
            'channelSAD': channelSAD,
            'channelREGRET': channelREGRET,
            'channelDISGUST': channelDISGUST,
            'channelANGER': channelANGER
        }
        return channel_dict


if __name__ == '__main__':
    em = Emoshape(host='127.0.0.1', port=2424, secret='xGyrpOpB/X+zpKtTgspeluOfE3TOmWV6', epuId='2003311368000000a500001055e506f4')
    # em2 = Emoshape(host='127.0.0.1', port=2424, secret='xGyrpOpB/X+zpKtTgspeluOfE3TOmWV6', epuId='2004026368000000dd000092f50a5c42')


    # em.toneOn('/home/ngdust/Музыка/1.mp3', '/home/ngdust/virtmic')
    em.sendMessage('I love you')
    # em2.sendMessage('I kill you')
    # time.sleep(2)
    # print(em.getChannels())
    time.sleep(2)
    em.closeConnection()