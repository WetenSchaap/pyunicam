"""
Universal class for controlling cameras. All camera classes inherit from this over-arching class. 
"""
import numpy as np
import numbers
import time

class UniversalCam(object):
    def __init__(self):
        self.camType = "universal"
        # settings all devices should //always// have. You can always add more.
        self.AVAILABLE_PROPERTIES = [
            "exposureTime", # µs
            "exposureTimeAuto", # bool
            "acquisitionFramerate", # fps
            "acquisitionFramerateAuto", # bool
            "gain", # dB
            "gainAuto", # bool
            'pixelFormat', # str, depends on camera, typically like "BayerRG8" or something
            'gammaEnable', # bool
            'gamma', # Not sure about the unit actually, some factor
            "height", # pair of px (0,1200) for instance
            "width", # pair of px (0,1200) for instance
        ] # BY DEFINITION: an automated variable setting MUST be regular name + auto and a bool setting. I don't care about funky alternative methods (yet)
        self.connectCam()
        ### Universal settings
        if 'ayer' in self.getProperty('pixelFormat'): 
            # This means raw Bayer pattern, which we basically NEVER want. So set to regular RGB output. bayer and Bayer will both work this way.
            # To see available pixelformats, check self.camConnection.get_info('PixelFormat')
            try:
                self.setProperty('pixelFormat','BGR8')
            except:
                print(f"Warning, pixelformat is Bayer patterned ('{self.getProperty('pixelFormat')}')!")
        # We are doing science, not making pretty pictures, so diable Gamma by default
        try:
            if self.getProperty('gammaEnable'):
                self.setProperty('gammaEnable',False)
        except NotImplementedError:
            # if camera does not support it, we are also statisfied
            pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        #Exception handling here
        self.close()
    
    def connectCam(self):
        """
        ConnectCam establishes the actual connection the the camera and saves the deeper connected camera object, which we are hiding from the user, as self.camConnection. We also set self.propertyConvert, which converts the internal property names I use in the AVAILABLE_PROPERTIES to functions, names, or values used by the camera internally.
        """
        self.camConnection = dict()
        self.propertyConvert = {k:1 for k in self.AVAILABLE_PROPERTIES}

    def close(self):
        """
        Stop any actions I am performing w the camera, and close the connection with the camera gracefully.
        """
        self.stopCapture()
        self.camConnection.close()
    
    def startCapture(self):
        """
        Start capturing images with camera. This function is non-blocking. Images that are captured need to be collected using getImages function. Stop collection with stopCapture.
        """
        self.camConnection.start()
        
    def stopCapture(self):
        """
        Stop capturing images with camera (when started with startCapture). Images that are captured need to be collected using getImages function.
        """
        self.camConnection.stop()

    def getImages(self) -> np.ndarray:
        """
        Return images captured by a capturing camera (see startCapture). Data is always returned as a numpy array. Every time you call this function, you receive one (1) image. You continue until no images are left to collect.
        
        Returns
        -------
        np.ndarray
            Captured image in a numpy array.

        Example
        ------
        To take a movie of 20 frames, run:
        
        c = pyunicam.connect_cam('thor')
        c.startCapture()
        imgs = [ (c.getImages(),time.time()) for frame in range(20)]
        c.stopCapture()
        """
        return np.random.randint(low=0,high=255,size=[500,500,3],dtype=np.uint8) # dummy data that looks like an image.

    def setProperty(self, prop : str, value : str|bool|numbers.Number):
        """
        Get the value of a camera property (like exposure time). You can select properties from a list printed by self.printProperties(). Watch the units!
        """
        if not (prop in self.AVAILABLE_PROPERTIES):
            raise NotImplementedError(f"the property '{prop}' is not implemented (or you made a spelling error). Available properties are listed below: \n{self.AVAILABLE_PROPERTIES}")
        setValue = self.getProperty(prop) # To trigger any errors while not writing, just as a precaution
        self._setPropertyDeep(prop,value)
        # Now check if anything was actually set, and throw error if not. Needs some leeway, since some values (but not all) are some hexadecimal thing, so will not be set *exactly* (12 may become 12.02 or something)
        setValue = self.getProperty(prop)
        if not withinFrac(value,setValue,0.05) and value != -1: # Since -1 means automated
           raise IOError(f'property not set correctly: tried setting {prop} to {value}, but upon inspection {prop} was set to {setValue}')
        else:
            return setValue

    def getProperty(self, prop : str):
        if not (prop in self.AVAILABLE_PROPERTIES):
            raise NotImplementedError(f"the property '{prop}' is not implemented (or you made a spelling error). Available properties are listed below: \n{self.AVAILABLE_PROPERTIES}")
        return self._getPropertyDeep(prop)

    def takeOneImage(self) -> np.ndarray:
        """
        Take a single image using the camera. This is mostly just a convenience function.
        """
        self.startCapture()
        d = self.getImages()
        self.stopCapture()
        return d

    def printProperties(self):
        """
        Print a nicely formatted list of possible properties of the camera that can be accessed through this interface. Should also give units of these properties, but maybe I forgot to do that.
        """
        _ = [print(prop) for prop in self.UNIVERSALPROPERTIES] # very naughty one-liner

    def getMetadata(self) -> dict:
        """
        Get camera metadata, to log what camera was actually used (usefull for like firmware or hardware updates).

        Returns
        -------
        cameraMetadata : dict
            dict containing relevant data
        """
        cameraMetadata = {
            "DeviceModelName" : "universal",
            "DeviceVendorName" : "Acme Inc.",
            "DeviceVersion" : "1.0",
        }
        return cameraMetadata

    def _setPropertyDeep(self, prop : str, value : str|bool|numbers.Number):
        """
        Function that actually sets a property is set using setProperty. setProperty just does input checking etc, the real nitty-gritty happens here.
        """
        self.propertyConvert[prop] = value

    def _getPropertyDeep(self, prop : str) -> str|bool|numbers.Number:
        """
        Function that actually gets a property when using getProperty. getProperty just does input checking etc, the real nitty-gritty happens here.
        Typically reads from self.propertyConvert somehow, but children are free to decide how to do that exactly
        """
        try:
            return self.propertyConvert[prop]
        except (KeyError,IndexError):
            raise NotImplementedError('This is really not supposed to happen, property requested does not have a definition. Tell Piet to fix this.')

def withinFrac( valA : numbers.Number , valB : numbers.Number , fraction : float ) -> bool:
    '''
    Check if value B is within a fraction of value A more or less.
    If A or B is not a number but something else, just do regular compare.
    '''
    if not isinstance(valA, numbers.Number) or not isinstance(valB, numbers.Number) or valA == 0:
        return valA == valB
    pr = valA * fraction
    if (valA-pr) < valB < (valA+pr):
        return True
    else:
        return False