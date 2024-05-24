from pyunicam import *
from.universal import *

def connect_cam(camtype: str) -> UniversalCam:
    if 'flir' in camtype:
        return FlirCam()
    elif 'thor' in camtype:
        return ThorCam()
    elif 'dummy' in camtype:
        return DummyCam()
    else:
        raise ValueError(f"No valid camera found with name {camtype}")
