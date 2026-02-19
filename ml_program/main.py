import cv2
import csv
import os
from camera import CameraManager
from mp_declaration import mediaPipeDeclaration
from pose_landmarks import PoseLandmarks

def main():
    mp_helper = mediaPipeDeclaration()
    pose = mp_helper.initialize_pose_detection()
    
    camera_manager = CameraManager()
    if not camera_manager.initialize_camera():
        print("Failed to initialize camera")
        return

    pose_landmarks = PoseLandmarks() 
    cv2.namedWindow("Conducting Tutor - Pose Detection", cv2.WINDOW_NORMAL)

    # Check if file exists before opening
    file_exists = os.path.isfile('data.csv')

    # Open in 'a' (append) mode
    with open('data.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Only write header if the file is new
        if not file_exists:
            header = []
            for i in range(1, 101):
                header.extend([f"x{i}", f"y{i}"])
            csv_writer.writerow(header)
        
        row_data = []

        
        try:
            while True:
                success, frame = camera_manager.capture_frame()
                if not success:
                    break
                
                frame = cv2.flip(frame, 1) 
                rgb_frame = camera_manager.convert_to_rgb(frame)
                results = mp_helper.process_pose_detection(pose, rgb_frame)
                
                if results and results.pose_landmarks:
                    pose_landmarks.update_landmarks(results)
                    frame = mp_helper.draw_pose_landmarks(frame, results)

                    # Get coordinates
                    rw = pose_landmarks.get_pose_landmark_15()
                    
                    if rw[0] is not None:
                        row_data.extend([rw[0], rw[1]])
                        
                        # Once we have 100 pairs (200 values), write the row
                        if len(row_data) >= 200:
                            csv_writer.writerow(row_data)
                            row_data = [] # Reset for next sequence
                            print("Saved a sequence of 100 frames.")

                # Show visual feedback of progress
                progress = len(row_data) // 2
                cv2.rectangle(frame, (10, 10), (210, 40), (50, 50, 50), -1)
                cv2.rectangle(frame, (10, 10), (10 + (progress * 2), 40), (0, 255, 0), -1)
                cv2.putText(frame, f"Seq Progress: {progress}/100", (15, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow("Conducting Tutor - Pose Detection", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            camera_manager.cleanup()
            pose.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()