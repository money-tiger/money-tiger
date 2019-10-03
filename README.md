# money-tiger
Projet in Data processing for the technion and Galil medical center. The project goal is to create a POC of a better way to answer the appeals sent from the different MHOs (Medical Health Organization) regarding monthly payments. Instead of answering one by one, we suggest working on groups with similar properties and using past data to offer new answers.

## Prerequisites

You should install the following:
* Jupyter Notebook (https://jupyter.org/install)
* Python 3.7
* Python libs:
  * Gensim Doc2Vec
  * Numpy
  * Pandas
  * Dash (https://dash.plot.ly/getting-started)
  * SKlearn
  
## Overview
  
Money Tiger uses Doc2Vec to convert hebrew medical text into vectors and One-Hot to convert categoric features into numeric Data Frame. This is performed in order to compare appeals to one another. Using DBSCAN it than clusters the data to groups and offers answers based on KNN of the new unanswered appeal and the solved data from previous months. In addition, the user can use predetermined rules to answer large amount of straightforward appeals, or look at the hard ones one by one with individual KNN.

## Built With

* Dash - used to build the GUI.
* Doc2Vec by Gensim.
* SKlearn - used for the preprocessing, clustring and KNN.
* Pandas and numpy - used for handling the data.

## Disclosure

"Money Tiger" is a student project and ment to be a POC and not a complete product (although all the way the users feedback guided the development), there are some features that are missing (i.e multipale MHO support). The system is designed based on the appeals excel sheets of July-September 2019 and they are not uploaded.
