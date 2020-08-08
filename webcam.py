#!/usr/bin/python

import http.client
import httplib2
import os
import random
import time
import datetime
import socket
import google_auth_oauthlib.flow
import googleapiclient
import subprocess
import oauth2client
import optparse
import shlex
import locale
import apiclient.http
import sys
from oauth2client import file
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

####Toggle uploading
perform_upload = True

####File information
rectime = datetime.date.today().strftime("%m-%d-%y")
filename = "sparring-" + rectime + ".mp4" 
dirpath = "C:\\Users\\Invictus\\Desktop\\Webcam\\"
filepath = dirpath + filename
vidsize = "1280x720" #720p. See youtube dimensions.  Camera supports 1080p but upload conflicts with suspend times

####Open results log
uplog = open("C:\\Users\\Invictus\\Desktop\\Webcam\\Logs\\upload_log.txt", "a")
uplog.write('\n' + "Results of " + rectime + " upload:\n")

####Pull recording time length from launcher/crontab
try:
	sys.argv[1]
	try:
		#Verify record time argument is in the correct form
		t = time.strptime(sys.argv[1], "%H:%M:%S")
		filelength = sys.argv[1]
	except ValueError:
		print("Invalid format for recording length, defaulting to half an hour.  Did you enter HH:MM:SS?")
		uplog.write("Invalid format for recording length, defaulted to 1 hour.\n")
		filelength = "00:30:00" #Format like 05:04:03. Five hours, four minutes, three seconds
except:
	print("No recording length specified, defaulting to half an hour")
	uplog.write("No recording length specified, defaulted to half an hour.\n")	
	filelength = "00:30:00" 

####Youtube Information
title = "Invictus Sparring Session (" + rectime + ")"
cat = "17" #Category - Sports
desc = "Invictus Brazilian Jiu Jitsu and Muay Thai Academy\n1453 Wyoming Blvd NE\nAlbuquerque, NM 87112"
hashtags = 'Muay Thai, Albuquerque'
priv = 'Public' #Change to private to avoid publishing
#publishtime = datetime.datetime.strptime('2018-06-29 08:15:27.243860', '%Y-%m-%dT%H:%M:%S.%fZ')
#publishtime lets you specify a later date for the video to become public on Youtbe

#See "Parser section" for additional arguments to add to YouTube Video
vidargs = '--title "' + title + '" --category "' + cat + '" --description "' + desc + '" --tags "' + hashtags + '" --privacy "' + priv + '"' # + " --publish-at (" + publishtime + ")"

####Upload exceptions and settings
httplib2.RETRIES = 1
MAX_RETRIES = 2
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,	 
	socket.error, IOError, httplib2.HttpLib2Error, http.client.NotConnected,
	http.client.IncompleteRead, http.client.ImproperConnectionState,
	http.client.CannotSendRequest, http.client.CannotSendHeader,
	http.client.ResponseNotReady, http.client.BadStatusLine,
	googleapiclient.errors.HttpError)

####Authorization
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#	 https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#	 https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'C:\\Users\\Invictus\\Desktop\\Webcam\\Credentials\\client_secret.json'
CREDENTIALS_FILE = 'C:\\Users\\Invictus\\Desktop\\Webcam\\Credentials\\youtube-upload-credentials.json'
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

####Reencode Youtube variables
def to_utf8(s):
	current = locale.getpreferredencoding()
	if hasattr(s, 'decode'):
		return (s.decode(current).encode("UTF-8") if s and current != "UTF-8" else s)
	elif isinstance(s, bytes):
		return bytes.decode(s)
	else:
		return s

####Convert Youtube variable array to string
def string_to_dict(string):
	if string:
		pairs = [s.strip() for s in string.split(",")]
		return dict(pair.split("=") for pair in pairs)

####Authorize the request and store authorization credentials.
def get_authenticated_service():
	get_flow = oauth2client.client.flow_from_clientsecrets
	flow = get_flow(CLIENT_SECRETS_FILE, scope=SCOPES)
	storage = oauth2client.file.Storage(CREDENTIALS_FILE)
	existing_credentials = storage.get()
	if existing_credentials and not existing_credentials.invalid:
		http = existing_credentials.authorize(httplib2.Http())
		return googleapiclient.discovery.build("youtube", "v3", http=http)
	else:
		flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
		authorize_url = flow.step1_get_authorize_url()
		message = "Check this link in your browser: {0}".format(authorize_url)
		print(message)
		code = input("Enter verification code: ")
		credential = flow.step2_exchange(code, http=None)
		storage.put(credential)
		credential.set_store(storage)
		http = credential.authorize(httplib2.Http())
		return googleapiclient.discovery.build("youtube", "v3", http=http)

####Build upload request
def initialize_upload(youtube, options):
	title = to_utf8(options.title)
	if hasattr(to_utf8('string'), 'decode'):
			description = u(options.description or "").decode("string-escape")
	else:
			description = options.description
	tags = [to_utf8(s.strip()) for s in (options.tags or "").split(",")]
	body = {
			"snippet": {
					"title": title,
					"description": description,
					"categoryId": options.category,
					"tags": tags
			},
			"status": {
					"embeddable": options.embeddable,
					"privacyStatus": ("private" if options.publish_at else options.privacy),
					"publishAt": options.publish_at,
					"license": options.license,
			},
			"recordingDetails": {
					"recordingDate": options.recording_date,
			},
	}
	# The chunksize parameter specifies the size of each chunk of data, in
	# bytes, that will be uploaded at a time. Set a higher value for
	# reliable connections as fewer chunks lead to faster uploads. Set a lower
	# value for better recovery on less reliable connections.
	#
	# Setting 'chunksize' equal to -1 in the code below means that the entire
	# file will be uploaded in a single HTTP request. (If the upload fails,
	# it will still be retried where it left off.) This is usually a best
	# practice, but if you're using Python older than 2.6 or if you're
	# running on App Engine, you should set the chunksize to something like
	# 1024 * 1024 (1 megabyte).

	body_keys = ",".join(body.keys())
	media = apiclient.http.MediaFileUpload(filepath, chunksize=-1, resumable=True, mimetype="application/octet-stream")
	request = youtube.videos().insert(part=body_keys, body=body, media_body=media)
	resumable_upload(request)

####Perform upload
def resumable_upload(request):
	response = None
	working = True
	print ('Uploading file...')
	
	while working:
		try:
			status, response = request.next_chunk()
			if response is not None:
					if 'id' in response:
						working = False
						result = ('Video id "%s" was successfully uploaded.' % response['id']) + "  Finished at: " + datetime.datetime.now().strftime("%H:%M") + '\n'
						print (result)
						uplog.write(result)
						exit()
					else:
						result = ('The upload failed with an unexpected response:\n%s' % response) + '\n'
						print (result)
						uplog.write(result)
						exit()	
		except HttpError as e:
			if e.resp.status in RETRIABLE_STATUS_CODES:
				result = ('A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)) + '\n'
				print (result)
				uplog.write(result)
				exit()
			else:
				result = ('A non-retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)) + '\n'
				exit()

####Main code
if __name__ == '__main__':
	#Update upload information
	start_time = datetime.datetime.now()
	vidargs = vidargs + ' --recording-date "' +  start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ') + '"'
	
	#Start recording
	#cmd = "ffmpeg -y -f alsa -ac 1 -i hw:2 -f v4l2 -framerate 30 -video_size " + vidsize + " -i /dev/v4l/by-id/usb-046d_HD_Webcam_C615_7E455230-video-index0 -c:v libx264 -preset ultrafast -crf 17 -c:a aac -strict -2 -b:a k -pix_fmt yuyv422 -t " + filelength + " " + filepath
	cmd = 'ffmpeg -y -rtbufsize 100M -f dshow -framerate 30 -video_size ' + vidsize + ' -i video="HD Webcam C615":audio="Microphone (HD Webcam C615)" -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 26 -pix_fmt yuv420p -c:a mp2 -strict -2 -ac 2 -b:a 96k -t ' + filelength + ' ' + filepath

	try:
		subprocess.check_output(cmd, shell=True)
		record_success = True
		print("Recording complete.  Finished at: " + datetime.datetime.now().strftime("%H:%M"))
	except subprocess.CalledProcessError:
		uplog.write("Invalid ffmpeg command.  Aborting recording.\n")
		record_success = False
	except OSError:
		uplog.write("Error encountered while recording video.  Command not found.\n")
		record_success = False
	
	if record_success and perform_upload:
		#Before uploading, verify we have the data to do so.
		dataline = ""
		datalog = open("C:\\Users\\Invictus\\Desktop\\Webcam\\Logs\\data_log.txt")
		
		for line in datalog:
                        dataline = str(line)
		
		datalog.close()
		datalog = open("C:\\Users\\Invictus\\Desktop\\Webcam\\Logs\\data_log.txt", "a+")
		
		if dataline:
			data = dataline.split("*")
			period_start = datetime.datetime.strptime(data[0], "%Y-%m-%d")
			data_usage = int(data[1])
		else:
			period_start = datetime.datetime.today().replace(day=1)
			data_usage = 0
			datalog.write(period_start.strftime("%Y-%m-%d") + "*0")
			
		#Check to see if we're in a new period
		if (period_start + datetime.timedelta(days=30)) > datetime.datetime.today():
			#On the same period.  Lets see if we have the data upload
			print("Same period")
			if (int(data_usage + int(str(os.path.getsize(filepath)).replace("L", ""))) > 5368709120):
                                #Uploading this file would exceed our data limits.  Warn the user and abort the upload.
				result = "Data quota exceeded.  Aborting upload."
				print(result)
				uplog.write(result + "\n")
				perform_upload = False
			else:
				#We've got data to spare.  Update the data log and continue with the upload.
				datalog.seek(0)
				datalog.truncate()
				datalog.write((period_start).strftime("%Y-%m-%d") + "*" + str(data_usage + int(str(os.path.getsize(filepath)).replace("L", ""))))
		else:
			#We're on a new period.  Lets update the data log
			datalog.seek(0)
			datalog.truncate()
			datalog.write(datetime.datetime.today().replace(day=1).strftime("%Y-%m-%d") + "*" + str(os.path.getsize(filepath)).replace("L", ""))

	if perform_upload:
		#Prep upload
		parser = optparse.OptionParser()

		#Parser section - These are SOME of the attributes that you can add to a video.
		#For ease of editing, I allow the user to enter a single string (vidargs)
		#Which is broken down here and later transformed into the request body.
		####NOT ALL OF THESE ARE IMPLEMENTED IN THE REQUEST BODY SECTION
		parser.add_option('-t', '--title', dest='title', type="string",
			help='Video title')
		parser.add_option('-c', '--category', dest='category', type="string",
			help='Video category')
		parser.add_option('-d', '--description', dest='description', type="string",
			help='Video description')
		parser.add_option('', '--description-file', dest='description_file', type="string",
			help='Video description file', default=None)
		parser.add_option('', '--tags', dest='tags', type="string",
			help='Video tags (separated by commas: "tag1, tag2,...")')
		parser.add_option('', '--privacy', dest='privacy', metavar="STRING",
			default=None, help='Privacy status (public | unlisted | private)')
		parser.add_option('', '--publish-at', dest='publish_at', metavar="datetime",
			default=None, help='Publish date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ')
		parser.add_option('', '--license', dest='license', metavar="string",
			choices=('youtube', 'creativeCommon'), default='youtube',
			help='License for the video, either "youtube" (the default) or "creativeCommon"')
		parser.add_option('', '--recording-date', dest='recording_date', metavar="datetime",
			default=None, help="Recording date (ISO 8601): YYYY-MM-DDThh:mm:ss.sZ")
		parser.add_option('', '--default-language', dest='default_language', type="string",
			default=None, metavar="string",
			help="Default language (ISO 639-1: en | fr | de | ...)")
		parser.add_option('', '--playlist', dest='playlist', type="string",
			help='Playlist title (if it does not exist, it will be created)')
		parser.add_option('', '--embeddable', dest='embeddable', default=True,
			help='Video is embeddable')

		#Although its too late to fix it, this is a good place to display to the user
		#vidargs for debugging
		#print("Processed argument string: " + vidargs)
		options, args = parser.parse_args(shlex.split(vidargs))
		youtube = get_authenticated_service()

		#Attempt the upload
		try:
			initialize_upload(youtube, options)
                        #print("Test")
		except HttpError as e:
			print ('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
