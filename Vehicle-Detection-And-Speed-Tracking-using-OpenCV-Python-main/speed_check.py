import cv2
import dlib
import time
import math
import os

# Debug flag for troubleshooting
DEBUG = True

# Check if required files exist
if not os.path.exists('C:/Users/ashut/Downloads/Telegram Desktop/Vehicle_Detection_And_Speed_Tracking_using_OpenCV_Python_main/Vehicle-Detection-And-Speed-Tracking-using-OpenCV-Python-main/myhaar.xml'):
    print("ERROR: myhaar.xml file not found in specified directory")
    exit(1)

if not os.path.exists('C:/Users/ashut/Downloads/Telegram Desktop/Vehicle_Detection_And_Speed_Tracking_using_OpenCV_Python_main/Vehicle-Detection-And-Speed-Tracking-using-OpenCV-Python-main/cars.mp4'):
    print("ERROR: cars.mp4 file not found in specified directory")
    exit(1)

try:
    # Load cascade classifier
    carCascade = cv2.CascadeClassifier('C:/Users/ashut/Downloads/Telegram Desktop/Vehicle_Detection_And_Speed_Tracking_using_OpenCV_Python_main/Vehicle-Detection-And-Speed-Tracking-using-OpenCV-Python-main/myhaar.xml')
    if carCascade.empty():
        print("ERROR: Failed to load cascade classifier. Check if myhaar.xml is valid")
        exit(1)
    elif DEBUG:
        print("Cascade classifier loaded successfully")
    
    # Open video file
    video = cv2.VideoCapture('C:/Users/ashut/Downloads/Telegram Desktop/Vehicle_Detection_And_Speed_Tracking_using_OpenCV_Python_main/Vehicle-Detection-And-Speed-Tracking-using-OpenCV-Python-main/cars.mp4')
    if not video.isOpened():
        print("ERROR: Could not open video file. Check if cars.mp4 is valid")
        exit(1)
    elif DEBUG:
        print("Video file opened successfully")
except Exception as e:
    print(f"Initialization error: {e}")
    exit(1)

WIDTH = 1280
HEIGHT = 720

def estimateSpeed(location1, location2):
    try:
        d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))
        # ppm = location2[2] / carWidth
        ppm = 8.8  # Pixels per meter
        d_meters = d_pixels / ppm
        if DEBUG:
            print(f"d_pixels={d_pixels}, d_meters={d_meters}")
        fps = 20
        speed = d_meters * fps * 3.6  # Convert to km/h
        return speed
    except Exception as e:
        print(f"Error in estimateSpeed: {e}")
        return 0

def trackMultipleObjects():
    rectangleColor = (0, 255, 0)
    frameCounter = 0
    currentCarID = 0
    fps = 0
    
    carTracker = {}
    carNumbers = {}
    carLocation1 = {}
    carLocation2 = {}
    speed = [None] * 1000
    
    # Write output to video file
    try:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Using XVID codec instead of MJPG
        out = cv2.VideoWriter('outpy.avi', fourcc, 10, (WIDTH, HEIGHT))
        if DEBUG:
            print("Video writer initialized successfully")
    except Exception as e:
        print(f"Error initializing video writer: {e}")
        out = None

    if DEBUG:
        print("Starting main tracking loop")

    while True:
        try:
            start_time = time.time()
            rc, image = video.read()
            
            if image is None:
                print("End of video or error reading frame")
                break
            
            image = cv2.resize(image, (WIDTH, HEIGHT))
            resultImage = image.copy()
            
            frameCounter += 1
            
            if DEBUG and frameCounter % 30 == 0:  # Print status every 30 frames
                print(f"Processing frame {frameCounter}")
                print(f"Number of cars being tracked: {len(carTracker)}")
            
            # Memory management - limit number of tracked cars
            if len(carTracker) > 50:  # Arbitrary limit
                oldest_car = min(carTracker.keys())
                carTracker.pop(oldest_car, None)
                carLocation1.pop(oldest_car, None)
                carLocation2.pop(oldest_car, None)
                if DEBUG:
                    print(f"Removed oldest car {oldest_car} to prevent memory issues")
            
            carIDtoDelete = []

            for carID in carTracker.keys():
                trackingQuality = carTracker[carID].update(image)
                
                if trackingQuality < 7:
                    carIDtoDelete.append(carID)
                    
            for carID in carIDtoDelete:
                if DEBUG:
                    print(f"Removing carID {carID} from list of trackers.")
                carTracker.pop(carID, None)
                carLocation1.pop(carID, None)
                carLocation2.pop(carID, None)
            
            # Only detect cars every 10 frames to improve performance
            if frameCounter % 10 == 0:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                try:
                    cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
                    
                    if DEBUG and frameCounter % 30 == 0:
                        print(f"Detected {len(cars)} cars in frame {frameCounter}")
                    
                    for (_x, _y, _w, _h) in cars:
                        x = int(_x)
                        y = int(_y)
                        w = int(_w)
                        h = int(_h)
                    
                        x_bar = x + 0.5 * w
                        y_bar = y + 0.5 * h
                        
                        matchCarID = None
                    
                        for carID in carTracker.keys():
                            trackedPosition = carTracker[carID].get_position()
                            
                            t_x = int(trackedPosition.left())
                            t_y = int(trackedPosition.top())
                            t_w = int(trackedPosition.width())
                            t_h = int(trackedPosition.height())
                            
                            t_x_bar = t_x + 0.5 * t_w
                            t_y_bar = t_y + 0.5 * t_h
                        
                            # Check if the car is already being tracked
                            if ((t_x <= x_bar <= (t_x + t_w)) and 
                                (t_y <= y_bar <= (t_y + t_h)) and 
                                (x <= t_x_bar <= (x + w)) and 
                                (y <= t_y_bar <= (y + h))):
                                matchCarID = carID
                        
                        # If the car is not already being tracked, create a new tracker
                        if matchCarID is None:
                            if DEBUG:
                                print(f"Creating new tracker {currentCarID}")
                            
                            tracker = dlib.correlation_tracker()
                            tracker.start_track(image, dlib.rectangle(x, y, x + w, y + h))
                            
                            carTracker[currentCarID] = tracker
                            carLocation1[currentCarID] = [x, y, w, h]

                            currentCarID += 1
                except Exception as e:
                    print(f"Error in car detection: {e}")
            
            # Optional: Draw reference line
            # cv2.line(resultImage, (0, 480), (1280, 480), (255, 0, 0), 5)

            # Update and draw bounding boxes for all tracked cars
            for carID in carTracker.keys():
                try:
                    trackedPosition = carTracker[carID].get_position()
                            
                    t_x = int(trackedPosition.left())
                    t_y = int(trackedPosition.top())
                    t_w = int(trackedPosition.width())
                    t_h = int(trackedPosition.height())
                    
                    cv2.rectangle(resultImage, (t_x, t_y), (t_x + t_w, t_y + t_h), rectangleColor, 4)
                    
                    # Update car location for speed estimation
                    carLocation2[carID] = [t_x, t_y, t_w, t_h]
                except Exception as e:
                    print(f"Error updating car position for ID {carID}: {e}")
            
            end_time = time.time()
            
            # Calculate FPS
            if end_time != start_time:
                fps = 1.0 / (end_time - start_time)
                
            # Optionally display FPS
            # cv2.putText(resultImage, f'FPS: {int(fps)}', (620, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

            # Calculate and display speed for each car
            for i in carLocation1.keys():
                try:    
                    if frameCounter % 1 == 0:  # Process every frame
                        [x1, y1, w1, h1] = carLocation1[i]
                        [x2, y2, w2, h2] = carLocation2[i]
                
                        # Update car location for next calculation
                        carLocation1[i] = [x2, y2, w2, h2]
                
                        # If the car has moved, estimate its speed
                        if [x1, y1, w1, h1] != [x2, y2, w2, h2]:
                            # Only calculate speed once when car is at certain y-position
                            if (speed[i] is None or speed[i] == 0) and y1 >= 275 and y1 <= 285:
                                speed[i] = estimateSpeed([x1, y1, w1, h1], [x2, y2, w2, h2])
                                if DEBUG and speed[i] > 0:
                                    print(f"CarID {i}: speed is {speed[i]:.2f} km/h")

                            # Display speed above a certain y-position threshold
                            if speed[i] is not None and y1 >= 180:
                                cv2.putText(resultImage, f"{int(speed[i])} km/hr", 
                                            (int(x1 + w1/2), int(y1-5)),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                except Exception as e:
                    print(f"Error calculating speed for carID {i}: {e}")
                    
            # Display the resulting frame
            cv2.imshow('result', resultImage)
            
            # Write frame to output video if enabled
            if out is not None:
                out.write(resultImage)

            # Exit if ESC key is pressed
            if cv2.waitKey(33) == 27:  # 27 is the ESC key
                break
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            break
    
    # Clean up
    if out is not None:
        out.release()
    video.release()
    cv2.destroyAllWindows()
    
    if DEBUG:
        print("Tracking completed")

if __name__ == '__main__':
    try:
        trackMultipleObjects()
    except Exception as e:
        print(f"Program error: {e}")

