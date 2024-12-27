import shapely
import pandas as pd
import os
import cv2


areas = {"a": [[1, 2], [3, 4]],
     "b": [[5, 6], [7, 8]]}

region = list()
for position in areas:
     print(areas[position])
     area = shapely.geometry.LineString(areas[position])
     region.append(area)

[lineA, lineB]
print(region)