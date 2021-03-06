#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController
from mininet.cli import CLI
import time
import os

myBandwidth = 50    # bandwidth of link ink Mbps
myDelay = ['10ms', '10ms']    # latency of each bottleneck link
# myQueueSize = 1000  # buffer size in packets
myLossPercentage = 0   # random loss on bottleneck links

#
#           h2      h4       h6
#           |       |        |
#           |       |        |
#           |       |        |
#   h1 ---- S1 ---- S2 ----- S3 ---- h8
#           |   0ms |   5ms  |
#           |       |        |
#           |       |        |
#           h3      h5       h7
#
#

class ParkingLotTopo( Topo ):
    "Three switches connected to hosts. n is number of hosts connected to switch 1 and 3"
    def build( self, n=3,queue_size=1000 ):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')
        print("queue_size"+str(queue_size))

        # Setting the bottleneck link parameters (htb -> Hierarchical token bucket rate limiting)
        self.addLink( switch1, switch2, 
            bw=myBandwidth, 
            delay=myDelay[0], 
            loss=myLossPercentage, 
            use_htb=True,
            max_queue_size=queue_size,
            )
        self.addLink( switch2, switch3, 
            bw=myBandwidth, 
            delay=myDelay[1], 
            loss=myLossPercentage, 
            use_htb=True,
            max_queue_size=queue_size, 
            )

        for h in range(3*n - 1):
            host = self.addHost('h%s' % (h + 1))
            if h < n:
                self.addLink(host, switch1) # one host to switch 1 (h1, h2, h3)
            elif h < 2*n - 1:
                self.addLink(host, switch2) # n hosts to switch 2 (h4, h5)
            else:
                self.addLink(host, switch3) # n hosts to switch 3 (h6, h7, h8)


def perfTest(mode="cubic",queue_size=1000):
    "Create network and run simple performance test"
    topo = ParkingLotTopo(n=3,queue_size=queue_size)
    net = Mininet( topo=topo,
                   host=CPULimitedHost, link=TCLink, controller = OVSController)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections( net.hosts )
    print("Testing network connectivity")
    net.pingAll()

    h1, h2, h3, h4, h5, h6, h7, h8 = net.get('h1','h2','h3','h4','h5','h6','h7','h8')

    # listen on h8
    h8.cmd("iperf3 -s -i 1 > " + mode + "_" + str(queue_size) + "_h8 &")
    time.sleep(2)
    # start test on h1
    h1.cmd("iperf3 -c 10.0.0.8 -t 300 -C " + mode + " > " + mode + "_" + str(queue_size) + "_h1 &")
    h3.cmd("ping -c 300 10.0.0.7 > " + mode + "_" + str(queue_size) + "_h3 &")


    # CLI( net ) # start mininet interface

    time.sleep(310)
    net.stop() # exit mininet

if __name__ == '__main__':
    os.system("sudo mn -c")
    os.system("killall /usr/bin/ovs-testcontroller")
    setLogLevel( 'info' )
    print("\n\n\n ------Start Mininet ----- \n\n")

    for size in range(50,6000,50):
        for mode in ['bbr','cubic']:
            print("queue_size:" + str(size) + " Mode:" + mode)
            perfTest(mode=mode, queue_size=size)
    

    print("\n\n\n ------End Mininet ----- \n\n")


