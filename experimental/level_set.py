from skimage import segmentation
import numpy as np
import matplotlib.pyplot as plt


img = segmentation.disk_level_set((100, 100), center=(50, 50), radius=15).astype('float64')
plt.imshow(img)
plt.show()

theta = np.linspace(0, 2 * np.pi, 150)

radius = 15
a = radius * np.cos(theta)
b = radius * np.sin(theta)
plt.plot(50 + a, 50 + b)


plt.show()

img = segmentation.inverse_gaussian_gradient(img, sigma=5, alpha=200)
plt.imshow(img)
plt.show()


level_set = segmentation.disk_level_set((100, 100), center=(50, 50), radius=25)\
    .astype('float64')
# commented fragment destabilizes evolution
# inner = segmentation.disk_level_set((100, 100), center=(50, 50), radius=5)
# level_set[inner == 1] = 0

plt.imshow(level_set)
plt.show()


def callback(ls):
    plt.imshow(ls)
    theta = np.linspace(0, 2 * np.pi, 150)

    radius = 15
    a = radius * np.cos(theta)
    b = radius * np.sin(theta)

    plt.plot(50 + a, 50 + b)
    plt.show()


res = segmentation. \
    morphological_geodesic_active_contour(img,
                                          init_level_set=level_set,
                                          iterations=20,
                                          balloon=-1,
                                          smoothing=3,
                                          iter_callback=callback)

plt.imshow(res)
plt.show()
