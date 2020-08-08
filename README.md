~~~~~~~~~~~~Quick Guide~~~~~~~~~~~~

Manual Run:

1) Open the Command Prompt (found on the desktop).

2) Open the webcam directory with this command:

	cd C:/Users/invictus/Desktop/webcam/

4)  Enter the following command, where "20" is the number of seconds to wait before recording starts and "00:00:00" is how long you want to record in hours, minutes, seconds. 
(Eg. one hour, thirty minutes, five seconds is 01:30:05):


	timeout 20; python webcam.py "00:00:00"

5) Close terminal when program is complete.

Scheduled Run:
1) Open the task scheduler (found on Desktop)
2) Create a "basic task".
3) Give task a name, press next
4) Select "one time", press next
5) Enter desired date and time
6) Choose "start a program", press next.
7) Hit the browse button and navigate to this directory:
	C:\Users\invictus\Desktop\webcam
8) Select the webcam.py file and hit next.
9) Click Finish

~~~~~~~~~~~~FIRST TIME SETUP~~~~~~~~~~~~
In order to upload videos to Youtube, this script needs oauth2 credentials provided by Youtube.  These credentials can be acquired by:

1) Open your browser and visit: https://console.developers.google.com/
2) Create a new project
3) Select "Enable APIs and Services"
4) Search for "YouTube Data API v3"
5) Enable the API.
6) Return to the project
7) Select "Crendentials"
8) Click "Create Credentials"
9) Select "OAuth Client ID"
10) Choose an Application Type of "Other" and name your credentials.
11) A prompt will appear displaying your credentials.  Press OK to return to the credentials page.
12) On the credentials page a new entry for your credentials will appear. Press the download icon below the trash icon to save them.
13) Open your download directory and move the download .json file to the webcam folder.
14) Rename the downloaded .json file "client_secret"
15) Open a terminal and run the following commands:
	cd /home/invictus/Desktop/webcam/
	python3 -c "import webcam; webcam.get_authenticated_service()"
16) The terminal will generate a weblink and prompt you to enter in an authorization code.  Open this weblink in your browser, sign in and grant permissions, then paste the authorization code into the terminal and press enter.
17) A youtube credentials file will automatically be generated. The script is now ready to run.
18) In the terminal, enter crontab -e
19) Add a new crontab line for each date and time you want recording to occur using the example above
20) Press Ctrl+S to save, Crtl+X to exit.  Recording and uploading will now occur at the scheduled times. 

In order to upload videos greater that 15 minutes, you must verify your youtube account
1) Goto www.youtube.com/verify to do so