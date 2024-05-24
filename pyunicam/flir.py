import time

from numpy import ndarray
from .universal import *

class FlirCam(UniversalCam):
    def __init__(self):
        import simple_pyspin
        import flir
        self.flirmodule = flir
        self.simple_pyspin = simple_pyspin
        super(FlirCam, self).__init__()
        self.camType = "flir"
        
    def connectCam(self):
        self.propertyConvert = {
            "exposureTime":"ExposureTime",
            "exposureTimeAuto":"ExposureAuto",
            "acquisitionFramerate":"AcquisitionFrameRate",
            "acquisitionFramerateAuto":"AcquisitionFrameRateEnable",
            "gain":"Gain",
            "gainAuto": "GainAuto",
            "height":"Height",
            "width":"Width",
            'pixelFormat':'PixelFormat',
            'gammaEnable' : 'GammaEnable',
            'gamma' : 'Gamma',
        }
        self.camConnection = self.simple_pyspin.Camera()
        self.camConnection.init()

    def getMetadata(self) -> dict:
        """
        Get camera metadata, to log what camera was actually used (usefull for like firmware or hardware updates).

        Returns
        -------
        cameraMetadata
            dict containing relevant data
        """
        cameraMetadata = {
            "DeviceModelName" : self.camConnection.DeviceModelName,
            "DeviceVendorName" : self.camConnection.DeviceVendorName,
            "DeviceVersion" : self.camConnection.DeviceVersion,
        }
        return cameraMetadata

    def getImages(self) -> ndarray:
        return self.camConnection.get_array()

    def _setPropertyDeep(self, prop : str, value : str|bool|numbers.Number):
        '''Set FLIR camera properties. If property is set to -1, set it to auto. If set to anything else as -1, set the property to manual mode (so AUTO=False!), if it is available.'''
        if 'Auto' in prop:
            return self._setPropertyFLIRDeep(property,value)
        autoProp = prop + "Auto"
        if value == -1:
            # do not set value at all, but enable automation
            if not autoProp in self.AVAILABLE_PROPERTIES:
                raise NotImplementedError(f"{prop} has no default or automated setting. Set something manually!")
            return self._setPropertyFLIRDeep(autoProp,True)
        else:
            # set to manual (if available)
            try:
                self._setPropertyFLIRDeep(autoProp,False)
            except KeyError:
                pass
            # AND set value
            self._setPropertyFLIRDeep(prop,value)

    def _setPropertyFLIRDeep(self, property : str, value : str|bool|numbers.Number, recursedepth=0, maxrecursedepth=5):
        irregularSetting = ( "exposureTimeAuto","gainAuto","acquisitionFramerateAuto",'pixelFormat' )
        if not property in irregularSetting:
            try:
                self.camConnection.camera_attributes[self.propertyConvert[property]].SetValue(value)
                return self._getPropertyFLIR(property)
            except self.simple_pyspin.PySpin.SpinnakerException as e: # no connection, wait a bit and try again, do n times. Sometimes this seems to happen?
                if recursedepth >= maxrecursedepth:
                    raise e
                time.sleep(0.01)
                dummy = self._getPropertyFLIR(property)
                self._setPropertyFLIRDeep(property, value, recursedepth=recursedepth+1,maxrecursedepth=5)
        else:
            if property == "exposureTimeAuto":
                self.flirmodule.exposureAutoSetter(self.camConnection,value)
            elif property == "gainAuto":
                self.flirmodule.gainAutoSetter(self.camConnection,value)
            elif property == 'acquisitionFramerateAuto':
                self.camConnection.AcquisitionFrameRateEnable = (not value)
            elif property == 'pixelFormat':
                self.camConnection.PixelFormat = value
            else:
                raise NotImplementedError("Trying to set unimplemented property. Or maybe you made a spelling error")

    def _getPropertyDeep(self,prop : str) -> str|bool|numbers.Number:
        result = self.camConnection.get_info(self.propertyConvert[prop])["value"]
        if result in ('off', 'Off', 'false', 'False'):
            return False
        elif result in ('on','On','continuous','once','Continuous','Once'):
            return True
        return result
