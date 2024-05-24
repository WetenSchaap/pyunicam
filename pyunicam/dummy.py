from .universal import *


class DummyCam(UniversalCam):
    def __init__(self):
        super(DummyCam, self).__init__()
        self.camType = "dummy"

    def startCapture(self):
        try:
            if self.camRunningDummy:
                raise ValueError("dummy camera was allready started")
            else:
                self.camRunningDummy = True
        except NameError:
            self.camRunningDummy = True

    def stopCapture(self):
        try:
            if self.camRunningDummy:
                self.camRunningDummy = False
            else:
                raise ValueError("dummy camera was not recording")
        except NameError:
            raise ValueError("dummy camera was not recording")

    def connectCam(self):
        self.propertyConvert = {i:"auto" for i in self.AVAILABLE_PROPERTIES}
        self.camConnection = True

    def getMetadata(self):
        cameraMetadata = {
                "DeviceModelName" : "dummy",
                "DeviceVendorName" : "dummy Inc.",
                "DeviceVersion" : "0.0",
        }
        return cameraMetadata