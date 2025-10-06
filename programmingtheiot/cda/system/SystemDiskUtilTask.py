import logging
import psutil

from programmingtheiot.cda.system.BaseSystemUtilTask import BaseSystemUtilTask
import programmingtheiot.common.ConfigConst as ConfigConst

class SystemDiskUtilTask(BaseSystemUtilTask):
    """
    Implementation of disk utilization monitoring task.
    """
    
    def __init__(self, path: str = '/'):
        """
        Initialize the disk utilization task.
        
        Args:
            path: The path to monitor disk usage for (default is root '/')
        """
        super(SystemDiskUtilTask, self).__init__(name=ConfigConst.DISK_UTIL_NAME)
        
        # Store the path to monitor
        self.diskPath = path
        logging.info(f"Initialized SystemDiskUtilTask for path: {self.diskPath}")
    
    def getTelemetryValue(self) -> float:
        """
        Get the current disk utilization percentage for the specified path.
        
        Returns:
            float: Disk utilization percentage (0.0 to 100.0)
        """
        try:
            # Get disk usage statistics for the specified path
            disk_usage = psutil.disk_usage(self.diskPath)
            
            # disk_usage.percent gives us the percentage directly
            disk_util_pct = disk_usage.percent
            
						# Uncomment the following lines for detailed debug information
            # logging.debug(f'Disk utilization for {self.diskPath}: {disk_util_pct:.2f}%')
            # logging.debug(f'  Total: {disk_usage.total / (1024**3):.2f} GB')
            # logging.debug(f'  Used: {disk_usage.used / (1024**3):.2f} GB')
            # logging.debug(f'  Free: {disk_usage.free / (1024**3):.2f} GB')
            
            return disk_util_pct
            
        except Exception as e:
            logging.error(f"Error getting disk utilization for {self.diskPath}: {e}")
            return 0.0
    
    def setDiskPath(self, path: str) -> bool:
        """
        Set a different path to monitor.
        
        Args:
            path: The filesystem path to monitor
            
        Returns:
            bool: True if path was set successfully, False otherwise
        """
        if path and len(path) > 0:
            self.diskPath = path
            logging.info(f"Updated disk monitoring path to: {self.diskPath}")
            return True
        return False