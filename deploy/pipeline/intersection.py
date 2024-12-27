import shapely
import pandas as pd
import os
import cv2

video = cv2.VideoCapture("output/kt-vehicle-30s.mp4")
# video = cv2.VideoCapture("output/kt-30s.mp4")
fps = video.get(cv2.CAP_PROP_FPS)

# output = pd.read_csv(("output/vehicle ID/test_output.csv"))
# output = pd.read_csv(("output/pedestrian ID/test_output.csv"))

def get_boxes(xmin, ymin, xmax, ymax):
    return [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]

def get_bottoms(xmin, ymin, xmax, ymax, scale):
    y_scaled = (ymax + ymin) * scale
    return [(xmin, ymin), (xmin, y_scaled), (xmax, y_scaled), (xmax, ymin)]

def get_center(xmin, ymin, xmax, ymax, scale):
    x_radius = (xmax + xmin) * scale
    y_radius = (ymax + ymin) * scale
    return [(xmin + x_radius, ymin + y_radius), (xmin + x_radius, ymax - y_radius), (xmax - x_radius, ymax - y_radius), (xmax - x_radius, ymin + y_radius)]

def convert_seconds(total_seconds):
    hours = str(int(total_seconds // 3600))
    minutes = str(int((total_seconds % 3600) // 60))
    seconds = str(round(total_seconds % 60, 2))

    time = hours+ ":"+ minutes + ":" + seconds
    return time

def generate_output_csv(pipeline, output, vehicle):
    output.columns = ["frame_id", "human", "human_box", "human_count", "vehicle", "vehicle_boxes", "vehicle_count","vehicle_plate", "vehicle_plate_boxes"]

    path_csv = "output/test_output.csv"
    output.to_csv(path_csv, index=False)

    output_csv = []
    for id in pipeline.predictor.collector.get_res().keys():
        for frameId in range(len(pipeline.predictor.collector.get_res()[id]["frames"])):
            frame = [id]
            frame.append(pipeline.predictor.collector.get_res()[id]["frames"][frameId])
            for rects in pipeline.predictor.collector.get_res()[id]["rects"][frameId]:
                frame.append(rects[0])
                frame.append(rects[1])
                frame.append(rects[2])
                frame.append(rects[3])
                frame.append(rects[4])
            output_csv.append(frame)
    if vehicle:
        vehicle_csv = pd.DataFrame(output_csv)
        plate = []
        # for id in pipeline.predictor.collector.get_res().keys():
        #     for frameId in range(len(pipeline.predictor.collector.get_res()[id]["frames"])):
                # for vehicleplate in pipeline.predictor.collector.get_res()[id]["vehicleplate"]:
                #     plate.append(vehicleplate)
        vehicle_csv.columns = ["vehicle Id", "frame ID", "confidence", "xmin", "ymin", "xmax", "ymax"]
        # vehicle_csv.insert(column = "vehicle plate", value = plate)
        path = 'output/vehicle ID/'
        if not os.path.exists(path):
            os.mkdir(path)
            print(f"Folder '{path}' created!")
        else:
            print(f"Folder '{path}' already exists")
        file = path + "/vehicle_output.csv"
        vehicle_csv.to_csv(file, index= False)  
    else:
        pedestrian_csv = pd.DataFrame(output_csv)
        pedestrian_csv.columns = ["pedestrian Id","frame ID", "confidence", "xmin", "ymin", "xmax", "ymax"]
        path = 'output/pedestrian ID/'
        if not os.path.exists(path):
            os.mkdir(path)
            print(f"Folder '{path}' created!")
        else:
            print(f"Folder '{path}' already exists")
        file = path + "/pedestrian_output.csv"
        pedestrian_csv.to_csv(file, index= False)
        
def line_intersect(object_type, output, regions):
    lines = dict()
    for section in regions:
        print(regions[section])
        line = shapely.geometry.LineString(regions[section])
        lines[section] = line

    count = 0
    break_in = []
    for section in lines:
        for ind in output.index:
                object_area = shapely.geometry.Polygon(get_bottom(output['xmin'][ind], output['ymin'][ind], output['xmax'][ind], output['ymax'][ind], 0.15))
                if output[object_type][ind] not in break_in and lines[section].intersects(object_area):
                    break_in.append(output[object_type][ind])
                    second = output[object_type][ind] / 30
                    time = convert_seconds(second)
                    count += 1
                    print(f"{object_type} ", output[object_type][ind], f"passed the {section} at " , time, "\n-----")
    return count

def area_intersect(object_type, output, regions):
    areas = dict()
    for section in regions:
        print(regions[section])
        area = shapely.geometry.LineString(regions[section])
        areas[section] = area

    count = 0
    break_in = []
    previous_objecct_id = 0
    for section in areas:
        for ind in output.index:
                object_area = shapely.geometry.Polygon(get_bottom(output['xmin'][ind], output['ymin'][ind], output['xmax'][ind], output['ymax'][ind], 0.15))
                if output[object_type][ind] not in break_in and areas[section].intersects(object_area):
                    break_in.append(output[object_type][ind])
                    second = output[object_type][ind] / 30
                    time = convert_seconds(second)
                    count += 1
                    print(f"{object_type}: ", output[object_type][ind],f"steps in the {section} at " , time, "\n-----")
                    previous_objecct_id = break_in[-1]
                elif output[object_type][ind] != previous_objecct_id and previous_objecct_id in break_in:
                    second = output["frame ID"][ind-1] / 30
                    time = convert_seconds(second)
                    print(f"{object_type}: ", previous_objecct_id, f"steps out of the {section} at " , time, "\n-----")
                    precious_pedestrian_id = output[object_type][ind]
        print(f"{count} {object_type[:-3]}s steps in the {section}.\n")
    return count


def pedestrian_intersection(output, region, mode):

    if mode == "line":
        count = line_intersect("predestrian Id", output, region)
        print(f"\n{count} pedestrian in total")
    elif mode == "area":
        area_intersect("predestrian Id", output, region)
        count = print(f"\n{count} pedestrian in total")
    else:
        print("No intersection was counted")
    

def vehicle_intersection(output, areas):

    if mode == "line":
        count = line_intersect("vehicle Id", output, region)
        print(f"\n{count} vehicle in total")
    elif mode == "area":
        area_intersect("vehicle Id", output, region)
        count = print(f"\n{count} vehicle in total")
    else:
        print("No intersection was counted")


