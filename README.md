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

In aggregate, during a time of emergency, visualizing where on the map first responders are being dispatches to can give those leading auxiliary response efforts valuable information about where they should be sending their assistance.

**_Note to Future DSI Cohorts:_**

>A primary contribution of our work is the [Broadcastify Archive Toolkit library](https://github.com/ljhopkins2/BArT). If you've selected this project, consider leveraging `BArT` to build a corpus of radio dispatch audio data on which to train your model. We're also indebted to the [DSI-NY-7 Campfire Radio-to-Location](https://github.com/mchbmn/radio-to-location) and [DSI-CHI-7 Project Red Siren](https://github.com/project-red-siren-dsi-chi-cc7/deliverables), so...paying it forward.



### Framework

 <img src="https://github.com/delvakwa/police-radio-to-mapping/blob/master/assets/screenshots/framework.png" align="right" width="200">We conceived a five-step process to represent the end-to-end journey of a radio transmission to a point potted on a map.That framework is **represented graphically nearby**. Below we'll briefly describe each step in the framework, what we built, and what next steps could be to advance the state of the art on a full-fledged dispatch-to-heatmap tool.

#### Acquire Archive Audio

##### _Description_
We decided to focus on acquiring archived dispatch transmissions rather than on handling a live-streaming feed. Not only did the technical lift for handling live-streamed data seem to exceed the available time, but – given the current state of the art – it was more important to build a corpus of audio data to train a model. We also hypothesized that we could use dispatch streams generally (as opposed to just when large-scale emergencies or disasters occurred), since our aim is for a tool that will be "turned on" after a disaster occurs, and not one to predict when radio transmission suggest a disaster _might_ be occurring.

##### _What We Built_

We used [Broadcastify](www.broadcastify.com) ("the world's largest source of Public Safety...live audio streams") as our source of archived dispatches. Because this process proved to be highly manual and time-consuming (in our own experience and that of previous projects we referenced), we developed the Broadcastify Archive Toolkit (BArT) to automate this process. We encourage future cohorts to leverage or iterate this tool to leapfrog the cumbersome manual download process. Documentation for BArT can be found at https://github.com/ljhopkins2/BArT.

##### _Next Steps_

As of this writing, some enhancements we'd like to see on BArT include
- Flexible date/time selection on .build() method
- De-coupling mp3 filename scraping from archive build; do it during download instead
- Parallelize mp3 filename acquisition & mp3 download
- Register BArT with [pyPI](https://pypi.org/)
- Create a setup script (pip install bart) to gracefully handle dependencies
- Built-in pickler/de-pickler?

#### Parse & Segment Audio

##### _Description_

##### _What We Built_

##### _Next Steps_

#### Convert Text to Speech

##### _Description_

##### _What We Built_

##### _Next Steps_

#### Extract Geolocation Data

##### _Description_

##### _What We Built_

##### _Next Steps_

#### Plot on Heatmap

##### _Description_

##### _What We Built_

##### _Next Steps_
