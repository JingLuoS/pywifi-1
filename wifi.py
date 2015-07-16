__author__ = "Mohit Sharma"
__credits__= "Charlie Mydlarz, Justin Salamon, Mohit Sharma"
__version__ = "0.1"
__status__ = "Development"

import dbus
import dbus.service
import sys
from wicd import misc
from wicd.translations import _
from blessings import Terminal
from tabulate import tabulate

class Wifi(object):
    '''
    Make sure that you have Wicd installed or a Wicd network manager running. 
    Without the Wicd network manager, you will be able to use most of the 
    methods except for connecting to a AP.**
    '''
    def __init__(self):
        self.table = []
        self._term = Terminal()
        self._this = self._term.yellow_bold('[WIFI]:\t')
        self.bus = dbus.SystemBus()
        try:
            self.daemon = dbus.Interface(
                self.bus.get_object('org.wicd.daemon', 
                               '/org/wicd/daemon'),
                'org.wicd.daemon'
            )
            self.wireless = dbus.Interface(
                self.bus.get_object('org.wicd.daemon', 
                               '/org/wicd/daemon/wireless'),
                'org.wicd.daemon.wireless'
            )
            self.config = dbus.Interface(
                self.bus.get_object('org.wicd.daemon', 
                                '/org/wicd/daemon/config'),
                'org.wicd.daemon.config'
            )
        except dbus.DBusException, e:
            print self._this,'Error connecting to wicd daemon: ',e
            sys.exit()
            
        if not self.daemon:
            print self._this,'Error connecting to wicd via D-BUS,' \
            ' this means wicd is not running.'
            sys.exit()
                
    def get_current_info(self):
        ''' Prints current AP info
        '''
        self.status, self.info = self.daemon.GetConnectionStatus()
        # Check if connected to any Wireless
        if(self.status == misc.WIRELESS):
            # Print AP name, IP info and Sig Strength
            print (self._this+'Connected to $AP as $IP'+
                   ' at $S Quality') \
                .replace('$AP', self.info[1]) \
                .replace('$IP', self.info[0]) \
                .replace('$S', self.info[2])

        else:
            print self._this,'Not connected to any network'
        return self.info
        
    def scan_wifi(self):
        ''' Scan all the Wifi APs and print name, quality strength and
        encryption methods supported by each
        '''
        print self._this,'Starting New Scan'
        # Set Scan (once) Mode ON
        if(self.wireless.Scan(True)):
            for network in range(self.wireless.GetNumberOfNetworks()):
                # Append to a table
                self.table.append(
                    [network,
                     self.wireless.GetWirelessProperty(
                        network, 'essid'), 
                     self.wireless.GetWirelessProperty(
                         network, 'bssid'),
                     self.wireless.GetWirelessProperty(
                         network, 'quality'), 
                     self.wireless.GetWirelessProperty(
                         network, 'strength'),
                    self.wireless.GetWirelessProperty(
                        network, "encryption_method")]
                )
            # Fancy View of all networks in tabular format
            print tabulate(self.table, 
                           headers=['#','AP', 'BSSID', 'Link Quality', 
                                    'Sig Strength', 'encryption'], 
                           tablefmt='pipe')
            return self.table
            # Clear the table (DO NOT PROCESS ANY DATA FROM TABLE!)
            #self.table = []


    def enc_type(self, ap_id):
        ''' Detailed encryption type supported by ap_id 
        '''
        if self.wireless.GetWirelessProperty(ap_id, 'encryption'):
            for i in range(len(misc.LoadEncryptionMethods())):
                if str(self.wireless.GetWirelessProperty(
                        ap_id, 'encryption_method'
                )).lower() in misc.LoadEncryptionMethods()[i]['type']:
                    return (misc.LoadEncryptionMethods()[i]['name'],
                            misc.LoadEncryptionMethods()[i]['required'])
        else:
            return ('No Encryption','')
            
    def enc_supported(self, ap_id):
        ''' List encryption type supported by all/ particular AP.
        parameters:
            ap_id: 'all' will list supported Encryption of all APs
            ap_id: x will give supported Encryption for AP x
        '''
        self.ap_id = ap_id
        if self.ap_id == 'all':
            for i in range(self.wireless.GetNumberOfNetworks()):
                self._x = self.enc_type(i)
                self.table.append(
                    [self.wireless.GetWirelessProperty(
                        i, 'essid'), 
                     self._x[0], 
                     self._x[1]]
                )
            print tabulate(self.table, headers=['AP', 'Enc Method', 
                                                'Auth req'],
                           tablefmt='pipe' )
            self.table = []
        elif self.ap_id in range(self.wireless.GetNumberOfNetworks()):
            a = self.wireless.GetWirelessProperty(
                self.ap_id, 'essid')
            self._x = self.enc_type(self.ap_id)
            
            return str(a),str(self._x[0]),str(self._x[1])
    
    def sig_strength(self, ap_id = 'all'):
        ''' Get Signal Strength for all/ particular AP.
        parameters: 
            ap_id: 'all' will list Signal Strength of all APs
            ap_id: x will give Signal Strength for AP x
        '''
        self.ap_id = ap_id
        if self.ap_id == 'all':
            for i in range(self.wireless.GetNumberOfNetworks()):
                self.table.append(
                    [self.wireless.GetWirelessProperty(
                        i, 'essid'),
                     self.wireless.GetWirelessProperty(
                         i, 'strength')]
                )
            print tabulate(self.table, headers=['AP', 'Sig Strength'],
                           tablefmt='pipe' )
            self.table = []
        elif self.ap_id in range(self.wireless.GetNumberOfNetworks()):
            a = self.wireless.GetWirelessProperty(
                self.ap_id, 'essid')
            b = self.wireless.GetWirelessProperty(
                self.ap_id, 'strength')
            #print '|%s|\t%s|'%(a,b)
            return str(a),str(b)

    def wpa_setup(self,ap_id=None, ver=None, username=None, 
                    domain=None, password=None):
        '''Set up WPA (personal and Enterprise)
        parameters:
            ap_id: access point id
            ver: 'enterprise' or 'personal'
            username: 'username'
            domain: 'domain name'
            password: 'password'
        * Some parameters might not be applicable to 
        personal/ enterprise wpa's. Default value is None
        '''
        self.ap_id = ap_id
        self.username = username
        self.domain = domain
        self.password = password
        if(ver == 'enterprise'):
            print 'Only for NYU network..'
            try:
                self.wireless.SetWirelessProperty(self.ap_id, 
                                                  'enctype', 
                                                  'peap-tkip')
                self.wireless.SetWirelessProperty(self.ap_id, 
                                                  'identity', 
                                                  self.username)
                #self.wireless.SetWirelessProperty(self.ap_id,
                #                                  'domain',
                #                                  self.domain)
                
                self.wireless.SetWirelessProperty(self.ap_id,
                                                  'phase2',
                                                  'auth=MSCHAPv2')
                self.wireless.SetWirelessProperty(self.ap_id, 
                                                  'password',
                                                  self.password)
            except _,e:
                print 'Error connecting to wpa_E: ',str(e)
        elif(ver == 'personal'):
            print ver
            try:
                self.wireless.SetWirelessProperty(self.ap_id,
                                                  'enctype',
                                                  'wpa')
                self.wireless.SetWirelessProperty(self.ap_id,
                                                  'key',
                                                  self.password)
            except _,e:
                print 'Error connectiong to wpa_P', str(e)

    def connect(self, ap_id):
        print self._this, 'Connecting to %s'%(
            self.wireless.GetWirelessProperty(ap_id,'essid'))
        last=None
        print 'Using: %s'%(self.wireless.GetWirelessProperty(ap_id, 'key'))
        self.wireless.ConnectWireless(ap_id)
        check = self.wireless.CheckIfWirelessConnecting
        status = self.wireless.CheckWirelessConnectingStatus
        message = self.wireless.CheckWirelessConnectingMessage
        if check:
            while check():
                next_ = status()
                if next_ != last:
                    # avoid a race condition where status 
                    #is updated to "done" after the loop check                                  
                    if next_ == "done":
                        break
                    print message()
                    last = next_
            print "done!"
            if status() != u'done':
                exit_status = 6
                
        self.status, self.info = self.daemon.GetConnectionStatus()
        '''assert self.info[0].count(".") == 3
        ip_parts = self.info[0].split(".")
        ip_parts = [int(part) for part in ip_parts]
        first, second, third, fourth = ip_parts
        '''
        print (self._this+
               'Connected to: $AP'+
               '\nIP Address: $IP '+
               '\n') \
            .replace('$AP', self.info[1]) \
            .replace('$IP', self.info[0])
        return self.info

    def disconnect(self):
        self.daemon.Disconnect()
        print self._this, 'Disconnecting from %s'%(
            self.wireless.GetCurrentNetwork(0))
