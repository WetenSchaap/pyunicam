#%% imports
import pyunicam
import time
import matplotlib.pyplot as plt
import numpy as np
# %%
c = pyunicam.connect_cam('thor')

# %%
d= c.takeOneImage()

plt.imshow(d)
print(f'max px value is {np.max(d)}')
# %%
print(c.getProperty('exposureTime'))
# %%
c.setProperty('exposureTime',33303)
# %%
d= c.takeOneImage()
plt.imshow(d)

print(f'max px value is {np.max(d)}')
#%%
c.startCapture()
imgs = [ (c.getImages(),time.time()) for frame in range(20)] 
c.stopCapture()
# %%
c.setProperty('acquisitionFramerate',0.5) 
c.startCapture()
imgs = [ (c.getImages(),time.time()) for frame in range(20)] 
c.stopCapture()
# %%
