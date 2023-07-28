# Guide to using DMI Open Data Plugin version 0.1 for QGIS

![Cover](guide%20image/cover.png)

## About DMIs Open Data and the plugin

DMI gathers large numbers of weather- and oceanographic data every minute that are used in forecasts, warnings, climate data and climate models. DMIs Open Data allow the user to freely download and use all this data. Documentation and more information about DMI Open Data can be found [here](https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data). 
This guide will only describe the actions behind the plugin that is available in QGIS, how to use it and the outputs. 
The plugin allows the user to easily import data from DMIs Open Data from Meteorological Observations (metObs), Climate Data (climateData), Lightning Data (lightningData), Radar Data (radarData) and Oceanographic Observations (oceanObs). At each tab must be used in order to get data. An API-key can freely be created [here](https://confluence.govcloud.dk/display/FDAPI/User+Creation). 

## Installation

Open QGIS and go to Plugins and then Manage and Install Plugins. ![Manage Plugins](guide%20image/plugin_installer.png)  
Search for DMI Open Data and install the plugin. The plugin will be located in the plugin toolbar.

![Installation](guide%20image/installl.png)

## Activate your API keys

Go to Settings &rarr; Options &rarr; DMI Open Data. 
![API Settings](guide%20image/api_setting.png)
A new tab will open that will allow you to insert your API keys.
![API Keys](guide%20image/api_keys.png)

## Meteorological Observations

Meteorological observations are observations made by meteorological stations and are not quality controlled. Read more about the data [here](https://confluence.govcloud.dk/display/FDAPI/Meteorological+Observation). 
 - Usage

The plugin lets you import up to 7 parameters, for as many stations as wanted. Furthermore, it is possible to limit the data based on a time interval, and to save data as Comma Separated Values (csv).
It is not possible to only pick a stationId and not a parameter, or only picking a parameter and no stationId. Not all stations measure all parameters. Be sure to check which stations measure what parameter in the “Stations and parameters” tab or read about it [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=53086560). 
 - Output

The output is a point shapefile (.shp) located at the coordinates of the station. The point’s attribute table can be accessed by right clicking the layer. Values, time of observation and stationId can be viewed. 

![Meteorological Observations](guide%20image/metobs.png)

## Climate Data

Climate data is data that has been quality checked by Danish Meteorological Institute (DMI). Climate data has 5 types of data available. Data from stations, data in 10x10km resolution, data in 20x20km resolution, data for municipalities and data for Denmark as a whole country. Read more about climate data [here](https://confluence.govcloud.dk/display/FDAPI/Climate+data).
 - Usage

Since climate data has 5 different types of data, it is possible to exchange between these by clicking on the radio buttons. Temporal resolution is also available in climate data. It is possible to switch between hour, day, month, and year. Not all parameters are available in all temporal resolutions. Read about which parameters are measured in which temporal resolutions [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=41717444).
 - Station

The output is the same as in meteorological observations except that there is one more field in the attribute table. This is because climate data is measured on a time interval, and not on an observed time. Therefor the fields include value, time from, time to and stationId.  
 - 10x10km resolution and 20x20km resolution

The output is a polygon shapefile. The division of cellIds are made from the national grid. 10x10 and 20x20km cell values are calculated by DMI, based on surrounding stations. Read more about it [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=41718900). The cell division can be found [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=41718900). 
 - Municipality 

The output is a point shapefile, that is available for each municipality. The values for the municipalities are calculated like the 10x10 and 20x20km grids. Each municipality has an ID, which can be found [here](https://danmarksadresser.dk/adressedata/kodelister/kommunekodeliste).
 - Country

The output is a point shapefile, that represents the value in Denmark based on calculations of stations in Denmark. 

![Climate Data](guide%20image/climate.png)

## Lightning Data

Lightning Data is lightnings observed by DMIs lightning sensors. DMI has 6 sensors located around Denmark, that measures cloud to ground (positive), cloud to ground (negative) and cloud to cloud. Lightning data has been measured since 2002. Read more about lightning data [here](https://confluence.govcloud.dk/display/FDAPI/Lightning+data).
 - Usage

Lightning data has three ways to sort data: BBOX, lightning type and datetime. 
BBOX allows the user to find lightning observed within a square of coordinates. BBOX must be written as a CSV file, as in the following example: 7.76,54.51,15.23,57.82. An easy way to find a BBOX can found [here](https://boundingbox.klokantech.com/). 
 - Output 

The output is a point shapefile that has a time of observation, a lightning type and an amplitude.

![Lightning Data](guide%20image/lightning.png)

## Radar Data

Radar Data from the plugin is a full range composite image that shows the volume measured by DMIs 5 radars. Radar data is not a direct measurement of e.g., precipitation. Radar data only goes 6 months back from the current date. Read more about radar data [here](https://confluence.govcloud.dk/display/FDAPI/Radar+Data).
 - Usage

It is possible to sort radar data in a time interval. 
 - Output

The output is one raster layer for each radar image. Each raster cell has one value. The cell size of each raster cell is 500 meter. 

![Radar Data](guide%20image/radar.png)

## Oceanographic Observations

 - About

Oceanographic observations are measured by DMI or the Danish Coastal Authority. This is done by tide gauge sensors located around the Danish coast. The stations measure the relative water height, and in some cases the water temperature. Read more about oceanographic observations [here](https://confluence.govcloud.dk/display/FDAPI/Oceanographic+Observation).
 - Usage

Oceanographic observations are dragged into QGIS, the same way as Meteorological Observations, and has the same selection options. 
 - Output

The output is also the same as Meteorological Observations and the fields include the parameter value, the time of observation and the id of the station. 

![Oceanographic Observations](guide%20image/ocean.png)

## Forecast Data (Vector)

 - About

Forecast data allows the user to import data from DMIs 3 Forecast models: HARMONIE (weather model), WAM (Wave model) and DKSS (Strom Surge model).
 - Usage

To choose between the different models, use the radio button. Each page has different parameters, areas and specifications. You can specify an area of interest, either by getting the closest point to a specified coordinate, or by defining a bounding box. Read more about forecast data [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=76155038). 
 - Output
The output is one or more points that contains the parameters chosen and a timestamp.
 

![Forecast Data](guide%20image/forecast_vector.png)

## Forecast Data (Raster)

 - About

Forecast data allows the user to import data from DMIs Forecast models. 2 models are available: Wave Model (WAM) and Storm Surge Model (DKSS). In version 0.1 of the plugin, only WAM and DKSS is available. When the two remaining models are released, they will also be included in the plugin. 
 - Usage

To choose between the different models, use the radio button. Each page has different parameters, areas and specifications. It is not possible to choose more than one parameter, as the output is all parameters in one layer. Read more about forecast data [here](https://confluence.govcloud.dk/display/FDAPI/Forecast+Data). 
 - Output

The output is one layer with all parameters, where the chosen parameter is displayed. In the layer symbology, you can choose between all parameters and depths (depths is only available for DKSS) by clicking on another band. Each band thereby represent a parameter and a depth, that can be visualized by clicking on it. 

![Forecast Data](guide%20image/forecast_raster.png)

## Stations and Parameters

- About

This tab allows the user to get an overview of all the meteorological and oceanographic stations that DMI manage. This also includes the stations in Greenland. Furthermore, it is possible to select stations that only measure certain parameters. A list of meteorological stations and their associated parameters can also be found [here](https://confluence.govcloud.dk/pages/viewpage.action?pageId=53086560).
- Usage

If the user wants to see meteorological stations, then it is the API-key for Climate Data that must be used. It is also only climatic parameters that are showed in the list of parameters, and stations that lie within the Climate Database. It is possible to sort between all DMIs stations, stations in Denmark only and stations in Greenland only. Furthermore, it can be sorted by whether the station measures a certain parameter, is active or is active within a certain range of time. 
- Output

The output is a point shapefile, each representing one station. The stations attribute table has 21 fields that describes the station.

![Information](guide%20image/information.png)