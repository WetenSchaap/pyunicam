from numbers import Number
import time
from .universal import *
import threading
import warnings

class ThorCam(UniversalCam):
    def __init__(self):
        import thorlabs_tsi_sdk
        import thorlabs_tsi_sdk.tl_camera
        import thorlabs_tsi_sdk.windows_setup
        self.thorlabs_tsi_sdk = thorlabs_tsi_sdk
        self.thorlabs_tsi_sdk.tl_camera = thorlabs_tsi_sdk.tl_camera
        self.thorlabs_tsi_sdk.windows_setup = thorlabs_tsi_sdk.windows_setup
        super(ThorCam, self).__init__()
        self.camType = "thor"

    def connectCam(self):
        self.thorlabs_tsi_sdk.windows_setup.configure_path()
        self.thorFramerate = -1 # so it is not possible to set the framerate natively in the thorcam, but I can of course manually force it. If framerate is -1, leave it to the camera, otherwise attempt to interfere using _thor_framerate_setter
        self.thorConnectSDK = self.thorlabs_tsi_sdk.tl_camera.TLCameraSDK()
        allCams = self.thorConnectSDK.discover_available_cameras()
        self.camConnection = self.thorConnectSDK.open_camera(allCams[0]) # I simply assume there is only 1 camera attached. Fuck me if that is not the case.
        self.propertyConvert = {
            "exposureTime" : 'exposure_time_us',
            "exposureTimeAuto" : "Not implemented",
            "acquisitionFramerate" : "special",
            "acquisitionFramerateAuto" : True,
            "gain" : "gain",
            "gainAuto": "Not implemented",
            "height" : 'sensor_height_pixels',
            "width" : 'sensor_width_pixels',
            'pixelFormat' : 'grayscale',
            'gammaEnable' : "Not implemented",
            'gamma' : 'Not implemented',
        }

    def close(self):
        self.stopCapture()
        self.camConnection.dispose()
        time.sleep(0.01)
        self.thorConnectSDK.dispose()

    def startCapture(self):
        if self.propertyConvert["acquisitionFramerateAuto"]:
            self.camConnection.frames_per_trigger_zero_for_unlimited = 0
            self.camConnection.arm(frames_to_buffer = 100)
            self.camConnection.issue_software_trigger()
        else:
            self.killThorCaptureThread = threading.Event()
            self.thorCaptureImageCacheLock = threading.Lock()
            self.thorCaptureImageCache = list()
            self.thorCaptureThread = threading.Thread(target=self._thor_capture_with_framerate)
            self.thorCaptureThread.start()

    def stopCapture(self):
        if self.propertyConvert["acquisitionFramerateAuto"]:
            self.camConnection.disarm()
        else:
            self.killThorCaptureThread.set()
            self.thorCaptureThread.join()
            self.camConnection.disarm()
    
    def getImages(self) -> list[np.ndarray]:
        if self.propertyConvert["acquisitionFramerateAuto"]:
            while True:
                try:
                    return np.copy(self.camConnection.get_pending_frame_or_null().image_buffer)
                except AttributeError:
                    pass # poll again
        else: 
            # this looks funky but makes sense: go over list, if it is empty, you expect more. If it takes too long, throw an error.
            totalTime = 0
            while True:
                try:
                    with self.thorCaptureImageCacheLock:
                        return self.thorCaptureImageCache.pop(0)
                except IndexError:
                    if totalTime > ((1/self.propertyConvert["acquisitionFramerate"]) * 3):
                        # If this error occurs, something very serious went wrong
                        raise ValueError("No images are being generated. Probably you ran out of memory or the camera disconnected or crashed.")
                    else:
                        totalTime += 0.01
                        time.sleep(0.01)

    def takeOneImage(self) -> np.ndarray:
        """
        Take a single image using the camera. This is mostly just a convenience function.
        """
        self.camConnection.frames_per_trigger_zero_for_unlimited = 0 # Without this, it will not work...
        self.camConnection.arm(frames_to_buffer = 2)
        self.camConnection.issue_software_trigger()
        # this won't work without a tiny pause, depends on how long camera has been on etc.
        while True:
            try:
                d = np.copy(self.camConnection.get_pending_frame_or_null().image_buffer)
                break
            except AttributeError:
                pass # poll again
        self.camConnection.disarm()
        return d

    def getMetadata(self) -> dict:
        cameraMetadata = {
            "DeviceModelName" : self.camConnection.model,
            "DeviceName" : self.camConnection.name,
            "DeviceVendorName" : "ThorLabs",
            "DeviceSerialNumber" : self.camConnection.serial_number,
            "DeviceSensorType" : self.camConnection.camera_sensor_type.name,
        }
        return cameraMetadata

    def _setPropertyDeep(self, prop : str, value : str|bool|numbers.Number):
        '''
        Set Thor camera properties. Note that only very few properties can actually be set.
        '''
        if 'Auto' in prop:
            raise NotImplementedError("Automated setting of properties is not implented in the thorcam")
        if prop == "acquisitionFramerate":
            self._thor_framerate_setter(value)
        else:
            thorname_of_property = self._get_real_property_name(prop)
            if value == -1:
                # Just set a random value, since we need to do something to prevent a crash
                self.camConnection.__setattr__(thorname_of_property,1000)
            else:
                self.camConnection.__setattr__(thorname_of_property,value)

    def _getPropertyDeep(self, prop: str) -> str | bool | Number:
        thor_prop_name = self._get_real_property_name(prop)
        # if thor_prop_name in ('special', True, False) or prop in ('acquisitionFramerate'):
        #     return thor_prop_name
        try:
            return self.camConnection.__getattribute__(str(thor_prop_name))
        except self.thorlabs_tsi_sdk.tl_camera.TLCameraError as e:
            raise NotImplementedError(repr(e))
        except AttributeError as e:
            if prop in ('pixelFormat','acquisitionFramerate','acquisitionFramerateAuto'): # weird cases can go here
                return self.propertyConvert[prop]
            else:
                raise e

    def _get_real_property_name(self, prop : str) -> str:
        try:
            thorname_of_property = self.propertyConvert[prop]
        except KeyError:
            raise KeyError(f'property {prop} does not exist for Thor cameras, or is not implemented')
        if thorname_of_property == "Not implemented":
            raise NotImplementedError(f'property {prop} is not implemented in the hardware of this Thor camera')
        return thorname_of_property

    def _thor_framerate_setter(self, value : float, minfps=1):
        '''
        Enforce a framerate on the Thor camera. This is //not// natively supported, and a hack. You should only do this if the exposure time is quite a bit shorter than the fps you want to reach. My gut feeling says 1 fps is the approx cutoff, faster than that > play with exposure times! Set minfps explicitly if you want to ignore this limit.
        '''
        if value == -1:
            # keep things on auto as expected.
            self.propertyConvert["acquisitionFramerateAuto"] = True
            self.propertyConvert["acquisitionFramerate"] = 1 / self.camConnection.frame_time_us
        else:
            # Take into account exposuretime, etc.
            self.propertyConvert["acquisitionFramerateAuto"] = False 
            self.propertyConvert["acquisitionFramerate"] = value
            if value > minfps:
                warnings.warn("Since framerate setting is not really supported by the Thorcam, I need to use a custom hack. It does not work for high framerates. I detect you are probably using a potentially too high framerate, but i will continue anyway.")

    def _thor_capture_with_framerate(self):
        time_per_loop = 1 / self.propertyConvert["acquisitionFramerate"]
        self.camConnection.frames_per_trigger_zero_for_unlimited = 0
        self.camConnection.arm(frames_to_buffer = 100)
        while not self.killThorCaptureThread.is_set():
            looptimes = time.time()
            # take pic, add to cache         
            self.camConnection.issue_software_trigger()
            # need to pause, how long is unknown a priori.
            while True:
                try:
                    d = np.copy(self.camConnection.get_pending_frame_or_null().image_buffer)
                    with self.thorCaptureImageCacheLock:
                        self.thorCaptureImageCache.append( d )
                    break
                except AttributeError:
                    pass # poll again
            # sleep until next pic
            looptime = time.time() - looptimes
            try:
                time.sleep(time_per_loop - looptime)
            except ValueError:
                raise ValueError(f"framerate is set to fast, data collection cannot keep up! Time of one loop is: {looptime} s, while desired looptime is {time_per_loop} s.")
