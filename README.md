# docparser
Generate relational data and visualizations to easily analyze many documents

## Summary
Cross-analyzing documents becomes a challenge as a company's volume of digital and digitized documents scales out. This challenge can be effectively managed with modern tools available on Oracle Cloud Infrastructure (OCI) that automate document analysis and make it easy to visually overview the content in meaningful ways.

Deploy a flow that automatically classifies a document once it is loaded into Object Storage, and based on its classification type, extracts the key-value pairs from the document that are typical of its type. Then, the keys and values identified from the document are re-structured into relational data and are analytically visualized in Oracle Analytics Cloud (OAC) in an aggregation of previously loaded documents.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup Steps](#setup-steps)
3. [End-user Flow](#end-user-flow)
4. [Reset the Flow](#reset-the-flow)
5. [Acknowledgements](#acknowledgements)

## Prerequistes
* Your OCI user manages all-resources in a compartment

## Setup Steps
1. Within the compartment that you manage, create a new compartment, e.g. called `docparser`.
2. Within the compartment that you manage, create an OCI Policy with statement:
  ```
  allow any-user to manage all-resources in compartment id <OCID of your new compartment> where any {request.principal.id='<OCID of your new compartment>'}
  ```
3. Within the new compartment that you created, create 3 buckets:
   1. `incoming-documents`
   2. `classified-documents`
   3. `sdk-results-document-analysis`
5. Within the new compartment that you created, create an OCI Functions Application called `docparser-app`, specifying a subnet of your choice.
6. Turn on logs for your Application, which can be used for troubleshooting.
7. Open Cloud Shell, and establish your `fn` profile for using OCI Functions:
   ```
   fn use context <your region key>
   fn update context oracle.compartment-id <OCID of your new compartment>
   fn update context oracle.image-compartment-id <OCID of your new compartment>
   fn update context registry <your region key>.ocir.io/<your tenancy namespace>/docparser
   ```
8. Generate an authentication token and save the token to a notepad. To generate the token, navigate: `Person icon in the top-right corner of the web console > My profile > Auth tokens > Generate token`
9. In Cloud Shell, log-in to your docker account as your OCI user, supplying your authentication token as the password when prompted:
    ```
    docker login -u '<your tenancy namespace>/<your username>' <your region key>.ocir.io
    ```
11. Create a folder and navigate to the folder. For example:
    ```
    mkdir docparser
    cd docparser
    ```
13. Within the folder, create the following files with the same content as in this repo:
    1. [func.py](./cloudfunction/func.py)
    2. [func.yaml](./cloudfunction/func.yaml)
    3. [requirements.txt](./cloudfunction/requirements.txt)
14. From within your folder, deploy your Function to your Application.
    ```
    fn -v deploy --app doc-parser-app
    ```
15. Within your new compartment, create an Event Rule with condition that includes `OBJECT_CREATE` and `OBJECT_UPDATE` as criteria, and an action that references the Function you created.
16. Within your new compartment, create an Autonomous Data Warehouse (ADW) in your new compartment.
17. In ADW, create 2 JSON Collections named `CLASSIFICATIONDATA` and `KVEXTRACTIONDATA`, by navigating: `ADW Launchpad > JSON`
18. In ADW, copy the Oracle RESTful Data Services (ORDS) base URL, which will enable you to interact with your JSON Collections: `ADW Launchpad > Restful Services and SODA > Click Copy`.
19. Assign configuration variables to your Functions Application:
    1. **classification-json-collection-name**: `CLASSIFICATIONDATA`
    2. **kvextraction-json-collection-name**: `KVEXTRACTIONDATA`
    3. **db-user**: `admin`
    4. **db-schema**: `admin`
    5. **dbpwd-cipher**: `(use your password for the ADMIN user in your ADW instance)`
    6. **ords-base-url**: `(use the SODA URL that you copied from ADW)`
    7. **COMPARTMENT_OCID**: `(use the OCID of your new compartment)`
    8. **NAMESPACE_NAME**: `(use the namespace for your Object Storage buckets)`
    9. **INCOMING_DOCUMENTS_STORAGE_BUCKET**: `incoming-documents`
    10. **CLASSIFIED_DOCUMENTS_STORAGE_BUCKET**: `classified-documents`
    11. **SDK_RESULTS_STORAGE_BUCKET**: `sdk-results-document-analysis`
20. Within your new compartment, create an Oracle Analytics Cloud (OAC) instance that will be used to connect to your ADW instance.

## End-user Flow
1. Upload documents from [sample-documents](./sample-documents) into Object Storage bucket, `incoming-documents`.
2. Navigate to ADW and run the JSON Collection for `KVEXTRACTIONDATA` and `CLASSIFICATIONDATA` to see the new JSON documents that have populated.
3. Referring to [docparser.sql](./sql/docparser.sql), run the statement that creates a materialized view from the JSON Collection `KVEXTRACTIONDATA`.
4. Referring to [docparser.sql](./sql/docparser.sql), run the select statement that prints the contents of the materialized view.
5. Repeat steps 3. and 4., with the JSON Collection `CLASSIFICATIONDATA` and its materialized view.
6. Open OAC and generate a connection to your ADW instance.
7. In OAC, create a Dataset using the materialized view, `KVEXTRACTIONDATA_MV`, e.g. called `kvextraction_dataset`.
8. Create a workbook and experiment with visualizations for your dataset. For example:
   1. Create a tag cloud visualization that shows the prevalence of fieldlabel and fieldvalue pairs, while using the document type as the color variable, and a custom calculation defined by the number of distinct process job ids as the size variable.
   2. Create a pie chart visualization that shows the prevalence of document types in your database using the document type as the color variable as well as the category, and your custom calculation described in 8.1 as the slice size variable.

## Reset the Flow
1. Empty the JSON Collections, `CLASSIFICATIONDATA` and `KVEXTRACTIONDATA`.
2. Drop the materialized views you created in step 3. of the [End-user Flow](#end-user-flow), `CLASSIFICATIONDATA_MV` and `KVEXTRACTIONDATA_MV`.
3. Reload the dataset in OAC.

## Acknowledgements
* Borrowed OCI Function code, Functions Application configuration variables, bucket implementation, and OCI Events Rule logic from [this blog](https://www.ateam-oracle.com/post/automated-document-classification-and-key-value-extraction-using-oci-document-understanding-and-oci-data-labeling-service#Label%20Data%20and%20Create%20Custom%20Model) for the events-functions pattern
* Borrowed documents used as input data from [this LiveLab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=3585&p210_wec=&session=113944798144441)
