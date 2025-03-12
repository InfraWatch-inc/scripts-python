import psutil
import GPUtil
import platform
import subprocess
from typing import List

from psutil import cpu_percent


class SystemData:
    motherboardUuid: str or None

    def __init__(self):
        self.SO = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()[0]
        self.get_mother_board_id()


    def get_mother_board_id (self):
        try:
            windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard "
                                                    "| Select-Object -ExpandProperty SerialNumber"]

            linux_sh = "sudo dmidecode -s system-uuid"

            sh = windows_sh if self.SO == "Windows" else linux_sh

            self.motherboardUuid = subprocess.check_output(sh, shell=True).decode().strip()

        except subprocess.SubprocessError as e:
            self.motherboardUuid = None
            print(e)

    def __str__(self):
        return f"{self.SO} {self.architecture} {self.version}"



class CPUData:
    cores: int
    threads: int
    times: float
    freq: object
    use: float
    cpu_model: str or None

    def __init__(self):
        self.update()
        self.__cpu_model()


    def update(self):
        self.cores = psutil.cpu_count(logical=False)
        self.threads = psutil.cpu_count(logical=True)
        self.times = psutil.cpu_times()
        self.freq = psutil.cpu_freq().current
        self.use = cpu_percent()

    def __cpu_model (self):
        SO = platform.system()
        try:
            windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_Processor | Select-Object -ExpandProperty Name"]

            linux_sh = "cat /proc/cpuinfo | grep 'model name' | uniq"

            sh = windows_sh if SO == "Windows" else linux_sh

            self.cpu_model = subprocess.check_output(sh, shell=True).decode().strip()

        except subprocess.SubprocessError as e:
            self.cpu_model = None
            print(e)

    def __str__(self):
        return f"(cores={self.cores}, threads={self.threads}, times={self.times}, freq={self.freq})"


class GPUData:
    gpus: List[GPUtil.GPU]

    def __init__(self):
        self.qtdGPUs = len(GPUtil.getGPUs())
        self.update()

    def update(self):
        self.gpus = GPUtil.getGPUs()


class RAMData:
    def __init__(self):
        self.freeSwap = None
        self.UsedSwap = None
        self.totalSwap = None
        self.free = None
        self.used = None
        self.total = None
        self.update()
    
    
    def update(self):
        self.total = (psutil.virtual_memory().total / (1024 ** 3)).__ceil__()
        self.used = (psutil.virtual_memory().used / (1024 ** 3)).__ceil__()
        self.free = (psutil.virtual_memory().free / (1024 ** 3)).__ceil__()
        self.totalSwap = (psutil.swap_memory().total / (1024 ** 3)).__ceil__()
        self.UsedSwap = (psutil.swap_memory().used / (1024 ** 3)).__ceil__()
        self.freeSwap = (psutil.swap_memory().free / (1024 ** 3)).__ceil__()
