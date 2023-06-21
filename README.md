# GTFS-pathfinder
Python code implementing file extraction and pathfinding for GTFS transportation networks datasets

GTFS is a common format for transportation network datasets, see https://developers.google.com/transit/gtfs for precise specifications

The gtfs_getter.py file downloads the latest gtfs zip released at the url given at the beginnning of the file, which can be modified, by default it is the french TER train network. It then extracts it and stores it in the specified directory, by default gtfs/, and erases the previous data if there was some.

By default gtfs_getter is called each time you run gtfs_extractor, to ensure the data is up to date, adding up to 20 seconds to the runtime.

This script is meant to be used in a python IDE like Spyder where you can run the file and then run commands in a console.

The gtfs_extractor.py file implements extraction of a GTFS dataset, assuming this dataset is already present in the directory specified (gtfs/ by default). Upon starting the program, it reads the data and stores it optimally in order to perform quickly the pathfinding later, this step may take up to 30 seconds.

Once the GTFS data is loaded, you can run the following commands in the console :
- l = dijkstra_clean_prompt(departure,arrival,dates)
  This command will perform a dijkstra algorithm in the graph of the network to find the shortest path on given dates.
  You need to give the names of departure and arrival stations, and these names must match exactly the names in the dataset, the code is case-sensitive. The potential dates of travel are to be given in a list of strings of the form "DD/MM/YYYY", even if there is only one date it must be given in a list of one element.
  The function may print "no trips found on given dates"

- display_dijkstra(l)
  This function will give a clean display of the trip l previously obtained



Détails à propos des données TER :
Ce projet a pour motivation initiale de trouver un itinéraire empruntant uniquement des TER, afin nottament de pouvoir transporter une planche de surf ou un vélo facilement, ce qui n'est pas toujours possible en empruntant des intercités ou TGV. Le jeu de données par défaut est donc celui des TER SNCF sur toute la France.
