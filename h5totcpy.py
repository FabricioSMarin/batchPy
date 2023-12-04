#This is how I extracted 20um data:

import h5py
import dxchange
import numpy as np
el = 26 # 11 is abs
prefix = '/mnt/micdata1/2ide/2023-1/Laminography-1/img.dat/2xfm_'


data = np.zeros([306-245,141,301],dtype='float32')
theta = np.zeros(306-245,dtype='float32')
for k in range(245,306):
	 fname = f'{prefix}{k:04}.mda.h5'
	 print(fname)
	 try:
			 with h5py.File(fname,'r') as fid:
					 data[k-245] = fid['MAPS/scalers'][el]
					 theta[k-245] = float(fid['MAPS/extra_pvs'][1,591])
					 print(f'{data.shape=}, {theta=}')
	 except:
			 print('miss k')

dxchange.write_tiff_stack(data,f'datael{el}/d',overwrite=True)
np.save('data/theta.npy',theta)
	

# and this is how I made an h5 file from it:
data = dxchange.read_tiff_stack(f'datael{el}/d_00000.tiff',ind=range(0,60))[:,:141,:298]
const = data[0,0,0]
print(const)
# data[68] = (data[67]+data[69])/2
# data[13] = (data[12]+data[14])/2
data = np.pad(data,((0,0),(0,0),(0,2)),mode='edge')
data_dark = np.zeros([1,data.shape[1],data.shape[2]],dtype='float32')
data_white = np.ones([1,data.shape[1],data.shape[2]],dtype='float32')*const
theta = np.load('data/theta.npy')
# theta[68] = 25.5
print(theta)
	
with h5py.File(f'data20umel{el}.h5','w') as fid:
	 fid.create_dataset('exchange/data',data=data)
	 fid.create_dataset('exchange/data_white',data=data_white)
	 fid.create_dataset('exchange/data_dark',data=data_dark)
	 fid.create_dataset('exchange/theta', data=theta)
print(data.shape)

# this is the line to reconstruct it with tomocupy:
tomocupy recon_steps --file-name data20umel11.h5 --lamino-angle 18.25 --center-search-width 50 --rotation-axis 151 --reconstruction-type full --fbp-filter shepp --minus-log False