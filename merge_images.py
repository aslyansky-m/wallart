import cv2
import os

# to print 15x10cm images I merge pairs and print A4

fld = 'D:/camera/selected/birds/'

imgs = ['DSC01870_edited.jpg', 'DSC08806-Enhanced-NR_edited.jpg', 'DSC01793_edited.jpg', 'DSC05114_edited.jpg', 'DSC03802_edited.jpg', 'DSC01837_edited.jpg']

out_fld = 'merged/'

os.makedirs(out_fld, exist_ok=True)

for n in range(3):
    im1 = cv2.imread(fld + imgs[n])
    im2 = cv2.imread(fld + imgs[n+3])
    im2 = cv2.resize(im2, (im1.shape[1], im1.shape[0]))
    im = cv2.vconcat([im1, im2])
    cv2.imwrite(out_fld + 'merged' + str(n) + '.jpg', im)
    

