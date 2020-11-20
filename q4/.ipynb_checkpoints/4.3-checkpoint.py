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
# myDelay = ['10ms', '10ms']    # latency of each bottleneck link
myQueueSize = 1000  # buffer size in packets
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

# class ParkingLotTopo( Topo ):
#     "Three switches connected to hosts. n is number of hosts connected to switch 1 and 3"
#     def build( self, n=3,delay=10 ):
#         switch1 = self.addSwitch('s1')
#         switch2 = self.addSwitch('s2')
#         switch3 = self.addSwitch('s3')
#         print(delay)
        

#         # Setting the bottleneck link parameters (htb -> Hierarchical token bucket rate limiting)
#         self.addLink( switch1, switch2, 
#             bw=myBandwidth, 
#             delay=str(delay)+'ms', 
#             loss=myLossPercentage, 
#             use_htb=True,
#             max_queue_size=myQueueSize,
#             )
#         self.addLink( switch2, switch3, 
#             bw=myBandwidth, 
#             delay='10ms', 
#             loss=myLossPercentage, 
#             use_htb=True,
#             max_queue_size=myQueueSize, 
#             )

#         for h in range(3*n - 1):
#             host = self.addHost('h%s' % (h + 1))
#             if h < n:
#                 self.addLink(host, switch1) # one host to switch 1 (h1, h2, h3)
#             elif h < 2*n - 1:
#                 self.addLink(host, switch2) # n hosts to switch 2 (h4, h5)
#             else:
#                 self.addLink(host, switch3) # n hosts to switch 3 (h6, h7, h8)



class TreeTopo( Topo ):
    "Topology for a tree network with a given depth and fanout."

    def build( self, depth=1, fanout=2,delay=10 ):
        # Numbering:  h1..N, s1..M
        self.hostNum = 1
        self.switchNum = 1
        # Build topology
        self.addTree( depth, fanout )

    def addTree( self, depth, fanout ):
        """Add a subtree starting with node n.
           returns: last node added"""
        isSwitch = depth > 0
        if isSwitch:
            node = self.addSwitch( 's%s' % self.switchNum )
            self.switchNum += 1
            for _ in range( fanout ):
                child = self.addTree( depth - 1, fanout )
                if depth>3:
                    self.addLink( node, 
                    child,bw=50, 
                    delay='10ms', 
                    loss=delay, 
                    use_htb=True,
                    max_queue_size=1000)
                else:
                    self.addLink( node, 
                    child,bw=50, 
                    delay='10ms', 
                    loss=0, 
                    use_htb=True,
                    max_queue_size=1000)
            
        else:
            node = self.addHost( 'h%s' % self.hostNum )
            self.hostNum += 1
        return node



def perfTest(delay=10):
    "Create network and run simple performance test"
    # topo = ParkingLotTopo(n=3,delay=delay)
    topo = TreeTopo(depth=4,fanout=2,delay=delay)
    net = Mininet( topo=topo,
                   host=CPULimitedHost, link=TCLink, controller = OVSController)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections( net.hosts )
    print("Testing network connectivity")
    # net.pingAll()
    print("Quedelayue Size"+str(delay))

    h1, h2, h3, h4, h5, h6, h7, h8 = net.get('h1','h2','h3','h4','h5','h6','h7','h8')
    h9, h10, h11, h12, h13, h14, h15, h16 = net.get('h9','h10','h11','h12','h13','h14','h15','h16')

    # listen on h8
    h1.cmd("iperf3 -s -i 1 > " + "delay_" + str(delay) + "_cubic &")
    h2.cmd("iperf3 -s -i 1 > " + "delay_" + str(delay) + "_bbr &")
    time.sleep(2)
    # start test on h1
    h15.cmd("iperf3 -c 10.0.0.1 -i 1 -t 300 -C cubic > " + "delay_" + str(delay) + "_cubic_sender &")
    time.sleep(50)
    h16.cmd("iperf3 -c 10.0.0.2 -i 1 -t 200 -C bbr > " + "delay_" + str(delay) + "_bbr_sender &")
    # h3.cmd("ping -c 100 10.0.0.7 > " + mode + "_" + str(delay) + "_h3 &")


    # CLI( net ) # start mininet interface

    time.sleep(320)
    net.stop() # exit mininet

if __name__ == '__main__':
    os.system("sudo mn -c")
    os.system("killall /usr/bin/ovs-testcontroller")
    setLogLevel( 'info' )
    print("\n\n\n ------Start Mininet ----- \n\n")

    # for delay in range(2,104,2):
    #     for mode in ['bbr','cubic']:
    #         print("delay:" + str(delay) +"ms mode:" +  mode)
    #         perfTest(mode=mode, delay=delay)
    for delay in range(0,11,1):
        perfTest(delay=delay)

    print("\n\n\n ------End Mininet ----- \n\n")


