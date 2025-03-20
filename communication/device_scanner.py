import socket
import threading
import time
from typing import List, Dict, Any, Callable, Optional
import netifaces
import zeroconf

class DeviceScanner:
    """
    Class to scan for network devices that might be LED controllers
    """
    
    def __init__(self, port_range: List[int] = [7700, 7701, 7702], scan_timeout: float = 0.1):
        """
        Initialize the device scanner
        
        Args:
            port_range: List of ports to scan
            scan_timeout: Timeout for each connection attempt in seconds
        """
        self.port_range = port_range
        self.scan_timeout = scan_timeout
        self.discovered_devices = {}
        self.scanning = False
        self.scan_thread = None
        self.zeroconf = zeroconf.Zeroconf()
        
    def get_local_ip_addresses(self) -> List[str]:
        """
        Get all local IP addresses
        
        Returns:
            List of local IP addresses
        """
        ip_list = []
        
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for link in addrs[netifaces.AF_INET]:
                    ip = link['addr']
                    if not ip.startswith('127.'): 
                        ip_list.append(ip)
        
        return ip_list
    
    def get_network_prefix(self, ip: str) -> str:
        """
        Extract network prefix from IP address
        
        Args:
            ip: IP address to process
            
        Returns:
            Network prefix (first three octets)
        """
        parts = ip.split('.')
        if len(parts) == 4:
            return '.'.join(parts[:3])
        return None
    
    def scan_network(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Scan the network for devices
        
        Args:
            callback: Function to call when devices are discovered
        """
        if self.scanning:
            return
        
        self.scanning = True
        self.discovered_devices = {}
        
        def scan_worker():
            local_ips = self.get_local_ip_addresses()

            browser = zeroconf.ServiceBrowser(self.zeroconf, "_osc._udp.local.", handlers=[self._on_service_state_change])

            for local_ip in local_ips:
                network_prefix = self.get_network_prefix(local_ip)
                
                if not network_prefix:
                    continue

                for i in range(1, 255):
                    if not self.scanning:
                        break
                    
                    target_ip = f"{network_prefix}.{i}"
                    
                    if target_ip in local_ips:
                        continue

                    for port in self.port_range:
                        if not self.scanning:
                            break
                        
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(self.scan_timeout)

                            result = sock.connect_ex((target_ip, port))
                            
                            if result == 0:
                                device_id = f"{target_ip}:{port}"
                                
                                if device_id not in self.discovered_devices:
                                    device_info = {
                                        'ip': target_ip,
                                        'port': port,
                                        'id': device_id,
                                        'type': 'unknown',
                                        'name': f"Device at {target_ip}:{port}"
                                    }
                                    
                                    self.discovered_devices[device_id] = device_info

                                    if callback:
                                        callback(device_info)
                            
                            sock.close()
                            
                        except socket.error:
                            pass
                        
                        time.sleep(0.01)

            time.sleep(2)

            browser.cancel()
            
            self.scanning = False
        
        self.scan_thread = threading.Thread(target=scan_worker)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        return self.scan_thread
    
    def stop_scan(self):
        """
        Stop the network scan
        """
        self.scanning = False
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=1.0)
    
    def _on_service_state_change(self, zeroconf_obj, service_type, name, state_change):
        """
        Handle Zeroconf service state changes
        
        Args:
            zeroconf_obj: Zeroconf instance
            service_type: Type of service
            name: Service name
            state_change: Type of state change
        """
        if state_change == zeroconf.ServiceStateChange.Added:
            info = zeroconf_obj.get_service_info(service_type, name)
            
            if info:
                addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                
                for address in addresses:
                    device_id = f"{address}:{info.port}"
                    
                    if device_id not in self.discovered_devices:
                        device_info = {
                            'ip': address,
                            'port': info.port,
                            'id': device_id,
                            'type': 'osc_led_controller',
                            'name': name.replace('._osc._udp.local.', '')
                        }
                        
                        self.discovered_devices[device_id] = device_info
    
    def get_discovered_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all discovered devices
        
        Returns:
            Dictionary of discovered devices
        """
        return self.discovered_devices