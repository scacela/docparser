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
* Your compartment has availability for the following resources:
  * 1x Compartment
  * 1x Policy
  * 3x Object Storage Bucket
  * 1x OCI Functions Application
  * 1x OCI Function
  * 1x Container Image Repository
  * 1x Events Rule
  * 1x ADW
  * 1x OAC

## Setup Steps
1. Within the compartment that you manage, create a new compartment, e.g. called `docparser`.
2. Within the compartment that you manage, create an OCI Policy with statement:
   > **Note:** replace &lt;placeholder values&gt; with your own values.
   ```
   allow any-user to manage all-resources in compartment id <OCID of your new compartment> where any {request.principal.id='<OCID of your new compartment>'}
   ```
3. Within the new compartment that you created, create 3 buckets named as indicated below. Ensure that the buckets Emit Object Events by checking the correspondng checkbox.
   1. `incoming-documents`: The user uploads documents to this bucket to trigger the rest of the flow.
   2. `classified-documents`: Documents will be copied from `incoming-documents` to this bucket, to a folder indicating the classification type associated with the document.
   3. `sdk-results-document-analysis`: The JSON analysis from the API calls will be redirected to this bucket.
5. Within the new compartment that you created, create an OCI Functions Application called `docparser-app`, specifying a subnet of your choice.
6. Turn on logs for your Application, which can be used for troubleshooting.
7. Open Cloud Shell, and establish your `fn` profile for using OCI Functions:
   > **Note:** replace &lt;placeholder values&gt; with your own values.
   ```
   fn use context <your region identifier>
   fn update context oracle.compartment-id <OCID of your new compartment>
   fn update context oracle.image-compartment-id <OCID of your new compartment>
   fn update context registry <your region key>.ocir.io/<your tenancy namespace>/docparserrepo
   ```
9. Generate an authentication token and save the token to a notepad. To generate the token, navigate: `Person icon in the top-right corner of the web console > My profile > Auth tokens > Generate token`
10. In Cloud Shell, log-in to your docker account as your OCI user, supplying your authentication token as the password when prompted:
    > **Note:** replace &lt;placeholder values&gt; with your own values.
    ```
    docker login -u '<your tenancy namespace>/<your username>' <your region key>.ocir.io
    ```
12. Create a folder and navigate to the folder. For example:
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
    > **Note:** replace &lt;placeholder values&gt; with your own values.
    1. `classification-json-collection-name`: `CLASSIFICATIONDATA`
    2. `kvextraction-json-collection-name`: `KVEXTRACTIONDATA`
    3. `db-user`: `admin`
    4. `db-schema`: `admin`
    5. `dbpwd-cipher`: &lt;your password for the ADMIN user in your ADW instance&gt;
    6. `ords-base-url`: &lt;ORDS base URL that you copied from ADW&gt;
    7. `COMPARTMENT_OCID`: &lt;OCID of your new compartment&gt;
    8. `NAMESPACE_NAME`: &lt;namespace for your Object Storage buckets&gt;
    9. `INCOMING_DOCUMENTS_STORAGE_BUCKET`: `incoming-documents`
    10. `CLASSIFIED_DOCUMENTS_STORAGE_BUCKET`: `classified-documents`
    11. `SDK_RESULTS_STORAGE_BUCKET`: `sdk-results-document-analysis`
21. Within your new compartment, create an Oracle Analytics Cloud (OAC) instance that will be used to connect to your ADW instance.

## End-user Flow
1. Upload documents from [sample-documents](./sample-documents) into Object Storage bucket, `incoming-documents`.
2. Navigate to ADW and run the JSON Collection for `KVEXTRACTIONDATA` and `CLASSIFICATIONDATA` to see the new JSON documents that have populated.
3. Referring to [docparser.sql](./sql/docparser.sql), run the statement that creates a materialized view from the JSON Collection `KVEXTRACTIONDATA`.
4. Referring to [docparser.sql](./sql/docparser.sql), run the select statement that prints the contents of the materialized view.
5. Repeat steps 3. and 4., with the JSON Collection `CLASSIFICATIONDATA` and its materialized view.
6. Open OAC and generate a connection to your ADW instance.
7. In OAC, create a Dataset using the materialized view, `KVEXTRACTIONDATA_MV`, e.g. called `kvextraction_dataset`.
8. Create a Workbook, e.g. called `kvextraction_workbook`, and experiment with visualizations for your Dataset. For example:
   1. Create a Tag Cloud visualization that shows the prevalence of various key-value pairs in your Dataset with the following variables:
      1. `Category`: `FIELDLABEL`, `FIELDVALUE`
      2. `Color`: `DOCUMENT_TYPE_CUSTOM`
      3. `Values (Size)`: Custom Calculation defined by `COUNT(DISTINCT(PROCESS_JOB_ID_CUSTOM)`, e.g. called `count_distinct_by_process_job`
   3. Create a Pie visualization that shows the prevalence of various document types in your Dataset with the following variables:
      1. `Category`: `DOCUMENT_TYPE_CUSTOM`
      2. `Color`: `DOCUMENT_TYPE_CUSTOM`
      3. `Values (Slice)`: Custom Calculation defined by `COUNT(DISTINCT(PROCESS_JOB_ID_CUSTOM)`, e.g. called `count_distinct_by_process_job`

## Reset the Flow
1. Empty the JSON Collections, `CLASSIFICATIONDATA` and `KVEXTRACTIONDATA`.
2. Referring to [docparser.sql](./sql/docparser.sql), drop the materialized views you created in step 3. of the [End-user Flow](#end-user-flow), `CLASSIFICATIONDATA_MV` and `KVEXTRACTIONDATA_MV`.
3. Reload the dataset in OAC.

## Acknowledgements
* Borrowed OCI Function code, Functions Application configuration variables, bucket implementation, and OCI Events Rule logic from [this blog](https://www.ateam-oracle.com/post/automated-document-classification-and-key-value-extraction-using-oci-document-understanding-and-oci-data-labeling-service#Label%20Data%20and%20Create%20Custom%20Model) for the events-functions pattern
* Borrowed documents used as input data from [this LiveLab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=3585&p210_wec=&session=113944798144441)
