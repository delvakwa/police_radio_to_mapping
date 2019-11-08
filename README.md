# Mapping Emergency Dispatch Transmissions

**General Assembly Data Science Immersive**<br>
Project 5: Client Project<br>
DSI-ATL-8: Anthony Chapman, Carol Chiu, Kwamae Delva, and Joseph Hopkins

## Executive Summary

### Problem Statement

_**Problem 10:** Using live police radio reports for real time identification of people needing assistance._

>Currently, FEMA identifies areas that require immediate attention (for search and rescue efforts) either by responding to reports and requests put directly by the public or, recently, using social media posts. This tool will utilize live police radio reports to identify hot spots representing locations of people who need immediate attention. The tool will flag neighborhoods or specific streets where the police and first-respondents were called to provide assistance related to the event.

### Background

During a disaster, auxiliary responders (such as those under the direction of FEMA) need information about where resources can be best deployed to meet urgent or large-scale needs. Emergency radio transmissions are a rich source of this information because
- **They’re real time:** broadcasts are coming over the airwaves literally RIGHT NOW
- **They contain rich location information:** by their nature, dispatches involve telling the responder where the emergency is occurring
- **They're real emergencies:** experienced dispatchers have vetted inbound calls for real need for services and triaged them

In aggregate, during a time of emergency, visualizing where on the map first responders are being dispatched to can give those leading auxiliary response efforts valuable information about where they should be sending their support.

**_Note to Future DSI Cohorts:_**

>A primary contribution of our work is the [Broadcastify Archive Toolkit](https://github.com/ljhopkins2/broadcastify-archtk) for python. If you've selected this project, consider leveraging the toolkit to build a corpus of radio dispatch audio data on which to train your model. We're also indebted to the [DSI-NY-7 Campfire Radio-to-Location](https://github.com/mchbmn/radio-to-location) and [DSI-CHI-7 Project Red Siren](https://github.com/project-red-siren-dsi-chi-cc7/deliverables), so...paying it forward.



### Framework

 <img src="https://github.com/delvakwa/police-radio-to-mapping/blob/master/assets/screenshots/framework.png" align="right" width="200">We conceived a five-step process to represent the end-to-end journey of a radio transmission to a point potted on a map.That framework is **represented graphically nearby**. Below we'll briefly describe each step in the framework, what we built, and what next steps could be to advance the state of the art on a full-fledged dispatch-to-heatmap tool.

#### 01 Acquire Archive Audio

##### _Description_
We decided to focus on acquiring archived dispatch transmissions rather than on handling a live-streaming feed. Not only did the technical lift for handling live-streamed data seem to exceed the available time, but – given the current state of the art – it was more important to build a corpus of audio data to train a model. We also hypothesized that we could use dispatch streams generally (as opposed to just when large-scale emergencies or disasters occurred), since our aim is for a tool that will be "turned on" after a disaster occurs, and not one to predict when radio transmission suggest a disaster _might_ be occurring.

##### _What We Built_

We used [Broadcastify](www.broadcastify.com) ("the world's largest source of Public Safety...live audio streams") as our source of archived dispatches. Because this process proved to be highly manual and time-consuming (in our own experience and that of previous projects we referenced), we developed the Broadcastify Archive Toolkit (`broadcastify-archtk`) for python to automate this process. We encourage future cohorts to leverage or iterate this tool to leapfrog the cumbersome manual download process. The toolkit can be found at https://github.com/ljhopkins2/broadcastify-archtk.

#### 02 Parse & Segment Audio

##### _Description_

While listening to our mp3 files, we realized that silence, low volume audio, and incoherent noises plagued our audio files. We decided to extract all of that out and focus on the sections of our audio that would generate the best results.

##### _What We Built_

We used the pydub Python package to parse and segment our mp3 files. Pydub accepts mp3 files and has methods that detect silence, detect audio, and split the mp3 files based on silence. We utilized the last method to pull samples of audio from our data. There are two parameters we passed in as well -- min_silence_len and silence_thresh. These determine how long a pause needs to be in milliseconds before it’s registered as silence, and how loud something needs to be in dbFS before its registered as audio. We played with a few min_silence_len and silence_thresh values, but settled on 2.5 seconds and -16dbFS for our dataset. 

##### _Next Steps_

Some enhancements we'd like to implement when parsing and segmenting audio include:
- Multiprocessing to speed up parsing and segmenting time
- Using the Audacity API instead of Pydub since it appears to reduce processing time

#### 03 Convert Text to Speech

##### _Description_

After converting our mp3 files to wav files, we are ready to use Google's Speech to Text API. This API returns transcriptions of audio data and confidence scores measuring how well the API think it did, both of which we stored into a dataframe. We also decided to use street locations from the city we pulled audio data from to help the API acknowledge road and highway names. In order to speed up this process, we ran a multiprocessing package around the API. 

##### _What We Built_

Google’s Speech to Text API accepts a wav file and stores it into memory. When calling the speech to text API, we can pass in a dictionary for it to reference its results on. We decided to run the API with and without street context to see if which setting would provide better results. The API then proceeds to detect speech in the audio file and return a transcription of what it heard and it’s confidence in the results. We returned those results as a dataframe. 

##### _Next Steps_

Some enhancements we'd like to implement when using a Speech to Text API include:
- Finding an API that produces better results
- Training an API on location and radio data to improve performance

#### 04 Extract Geolocation Data

##### _Description_

Now that we have transcriptions of our audio files, we need to find any locations in the text. spaCy, the Natural Language Processesing API, seemed like the best fit because it has a matcher class that allows us to create our own set of rules for spaCy to flag. 

##### _What We Built_

We used spaCy, a powerful Natural Language Processing API, to extract true locations from our Speech to Text transcriptions. SpaCy has a matcher that allows us to create a custom dictionary of things to look for in text. Words related to streets are passed in (street, place, trail, etc), and spaCy looks for those words in our transcripts. When a word matches one of those in our dictionary, spaCy then searches the words around it for context, and returns what it believes to be the address. We then compile extracted location in a dataframe. 

##### _Next Steps_

Some enhancements we'd like to implement when extracting Geolocation data include:
- Using an API already trained on address data 
- Referencing known addresses in the API and determining whether or not the address given is real or not

#### 05 Plot on Heatmap

##### _Description_

Finally, we used the address data extracted to acquire latitudes and longitudes of the places mentioned in our audio data. We then inserted those coordinates into the Google Maps API and mapped them to find the exact address locations mentioned. 

##### _What We Built_

We used a function that accepts an address and a google api key to search google for the address given. It then saves the results as a JSON and parses through it to find the latitude and longitude of the address given, and saves those results. 

The Google Mapping API accepts a latitude and longitude to center the map around, and then maps exact road locations based on latitudes and longitudes passed into it. We reference the dataframe that contains the results from the Spacy NLP API for our latitude and longitude mapping coordinates. 

##### _Next Steps_

Some enhancements we'd like to implement when plotting our locations on a heatmap include:
- Mapping more than one point on the map using the Folium API
- Changing the colors of the points on the map to determine importance based on audio context
