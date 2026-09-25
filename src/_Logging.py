# Lib
import logging
import inspect

# ================================================================================
# Create logger object ===========================================================
# ================================================================================

# Create counter decorator fo logger.
class CallCounted:
    """Decorator to determine number of calls for a method"""

    def __init__(self,method):
        self.method=method
        self.counter=0
      
    def __call__(self, message,*args,**kwargs):
        """
        Allows to count each logger call.
        """
        self.counter+=1
        
        # Get call function name
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        file_name = frame.f_code.co_filename.split("/")[-1]
        message =  " - From: ["+ function_name + "] in [" + file_name +  "] - " + message 
        return self.method(message, *args,**kwargs)

# Create or get the logger
logger = logging.getLogger('shared_logger')
logger.setLevel(logging.DEBUG)  # Log everything (DEBUG level or higher)

# Add the counter decorator to logger's methods
logger.debug = CallCounted(logger.debug)
logger.info = CallCounted(logger.info)
logger.warning = CallCounted(logger.warning)
logger.critical = CallCounted(logger.critical)

# Prevent multiple handlers if the logger is configured multiple times
if not logger.handlers:
    # Create a file handler to log to a file
    file_handler = logging.FileHandler('debug.log', mode="w")
    file_handler.setLevel(logging.DEBUG)

    # Define log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

# ================================================================================
# Create logger recap ============================================================
# ================================================================================

def log_recap(logger):
    """
    Print a recap of the number of info, warning and critical message in the object `logger`.
    """
    print("=========================================================")
    print("END")
    print(">["+str(logger.info.counter)    +"] Info entries detected.")
    print(">["+str(logger.warning.counter) +"] Warning entries detected.")
    print(">["+str(logger.critical.counter)+"] Critical entries detected.")
    if logger.warning.counter > 1:
        print(">> TRNSYS simulation might fail because of raised warning. Please check the log file.")
    if logger.critical.counter > 1:
        print(">> TRNSYS simulation will fail because of raised critical. Please check the log file.")
    print("=========================================================")

    logger.info("=========================================================")
    logger.info("END")
    logger.info(">["+str(logger.info.counter)    +"] Info entries detected.")
    logger.info(">["+str(logger.warning.counter) +"] Warning entries detected.")
    logger.info(">["+str(logger.critical.counter)+"] Critical entries detected.")
    if logger.warning.counter > 1:
        logger.info(">> TRNSYS simulation might fail because of raised warning. Please check the log file.")
    if logger.critical.counter > 1:
        logger.info(">> TRNSYS simulation will fail because of raised critical. Please check the log file.")
    print("=========================================================")

# ================================================================================
# ================================================================================
# ================================================================================
