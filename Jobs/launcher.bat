C:


cd C:\Users\invictus\Desktop\webcam


python webcam.py


echo "Deleting old videos"


forfiles -p C:\Users\invictus\Desktop\webcam\ -s -m *.mp4 -d -30 -c "cmd /c del @path"

timeout 30