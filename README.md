# pyunicam

Pyunicam is a Python module to control (scientific) cameras using a universal Python wrapper. Many/most scientific camera manufacturers have some sort of Python interface, but they are always slightly different between devices, which is (very) annoying, as well as very complex. This module is built to solve this problem exposing a single universal control interface. Advanced settings, etc, are typically better handled trough the original interface, but if you do relatively straighforward things (say, adjusting gain and taking a video at a specific framerate), this modules should be much easier to use.

It is really only intended for use in our lab, but who knows, maybe it is usefull to someone else out there.

The general procedure for usage would be:

```python
import matplotlib.pyplot as plt
from pyunicam import *

with connect_cam("thor") as cam: # open a camera, in this case a thorcam
    data = cam.takeOneImage()    # take a single image. `data` is a numpy array, the number of dimensions is 2 in the camera is grayscale, and 3 if the camera uses color.
    plt.imshow(d)                # see how that turned out
    plt.show()
    print(f"Exposure time is set to {cam.getProperty('exposureTime')} µs") # Get some random setting
    cam.setProperty('exposureTime', 100000)                                # Set some random setting
    print(f"Exposure time is set to {cam.getProperty('exposureTime')} µs") # Check that the setting changed
    cam.startCapture()                                                     # Initalize taking a video
    imgs = [ (cam.getImages(),time.time()) for frame in range(20)]         # Take 20 frames of images
    cam.stopCapture()                                                      # Stop taking video
    med = np.median(np.array(imgs), axis = 0)                              # imgs is now a list on numpy array images. You can save these or do some post-processing. Whatever you want.
```

## Implemented camera brands

Currently the following camera brands have been implemented:

- [Thorlabs cameras](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=13243) - implemented using the `thorlabs_tsi_sdk` module.
- [FLIR cameras](https://www.flir.eu/browse/industrial/machine-vision-cameras/) - implemented using the `spinnaker-python` and `simple_pyspin` modules.
- A dummy camera, which produces random noise, usefull for testing.

But be aware, I only implemented things we actually needed, and spend no time on going much beyond that! So, the Thorlabs camera we have in our lab does not support `gain` for instance, and therefore I have not implemented setting the gain in the thorcam module.

If you want your own camera added, or something unimplemented implemented, let me know, I can probably help.

## Camera properties

The camera properties you can get and sometimes set (if the camera has them implemented) are the following:
- "exposureTime", in µs
- "exposureTimeAuto"
- "acquisitionFramerate", in frames per second
- "acquisitionFramerateAuto"
- "gain", in dB
- "gainAuto"
- 'pixelFormat', depends on camera, typically like "BayerRG8" or something. Is relevant for color cameras, probably leave this value alone.
- 'gammaEnable', defaults to False
- 'gamma', Not sure about the unit actually, some factor
- "height", pair of px (0,1200) for instance
- "width", pair of px (0,1200) for instance

Access them with the `cam.getProperty` and `cam.setProperty` functions.

## Installing

Installing can be a bit of a hassle, because you need to install this module, as well as any modules for each camera. This probably means you need to manually install things. Follow the general guide below, and the installation instructions per camera. Do this before installing this module!

### FLIR camera

1. Go to [the FLIR software downloads](https://www.flir.com/support-center/iis/machine-vision/downloads/spinnaker-sdk-download/spinnaker-sdk--download-files/#anchor2)
1. Download both the SDK and the "python sdk". The Python SDK is the FLIR Python interface, called "pyspin".
1. Read the readme for the SDK to learn how to install it. And install it via whatever shady method they tell you to follow.
1. Install the python module in the python enviroment you use:
    - Using `pip`:
    ```bash
    pip install /the/path/to/the/spinnaker/wheel/spinnaker_python-someversionnumbers.whl
    ```
    - Using `poetry`: add the following to you `pyproject.toml` file
    ``` toml
    spinnaker-python = {path = "/the/path/to/the/spinnaker/wheel/spinnaker_python-someversionnumbers.whl"}
    ```

### Thorlabs camera

1. Go to the [Thorlabs camera download page](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam)
2. Download and install the regular Thorcam software under the *software* tab, and download the SDK under the *programming interfaces* tab.
3. Unpack the zip, and place the files somewhere where you will not accidentally delete them
4. Copy the following files (within the files you just unzipped): all files in `SDK\Native Toolkit\dlls\Native_32_lib\` to `SDK\Python Toolkit\dlls\32_lib\` and all files in `SDK\Native Toolkit\dlls\Native_64_lib\` to `SDK\Python Toolkit\dlls\64_lib\`
5. Install the python module in the python enviroment you use:
    - Using `pip`:
    ```bash
    pip install <path to unpack location>/SDK/Python Toolkit/thorlabs_tsi_camera_python_sdk_package.zip
    ```
    - Using `poetry`: add the following to you `pyproject.toml` file
    ``` toml
    spinnaker-python = {path = "<path to unpack location>/SDK/Python Toolkit/thorlabs_tsi_camera_python_sdk_package.zip"}
    ```

### General

This module is designed such that you do *not* need all packages for all cameras to control a single specific camera. Instead, you specify which camera you have, and thus which packages you need/want. We use 'extras' for that. Possible extras are:

- `flir` - for FLIR cameras.
- `test` - for testing.

Since this module is not added to Pypi (yet), you will have to install it manually from this repo. In the examples, below we include the `flir` extra. 

Using *pip*, run:
``` bash
python -m pip install -e "pyunicam[flir] @ git+https://github.com/WetenSchaap/pyunicam.git"
```

Using, *poetry*, you can add the following to your `pyproject.toml`:

``` toml
pyunicam = { git = "https://github.com/WetenSchaap/pyunicam.git", extras = ["flir"]}
```
