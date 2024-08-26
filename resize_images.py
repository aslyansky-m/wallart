import glob
import cv2
import os

images = glob.glob('D:/camera/selected/birds/*.jpg')
output_fld = 'resized/'
scale_factor = 0.25

os.makedirs(output_fld, exist_ok=True)

for img_path in images:
    im = cv2.imread(img_path)
    im = cv2.resize(im, (0, 0), fx=scale_factor, fy=scale_factor)
    cv2.imwrite(output_fld + os.path.basename(img_path), im)
    
    