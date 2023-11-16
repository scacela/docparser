import io
import json
import logging
import os
import uuid
import oci.ai_document
import oci.object_storage
import requests
import datetime
import uuid
from fdk import response

def generate_timestamp():
   # Generate current date and time
   current_datetime = datetime.datetime.now()

   # Format the date and time as a string
   formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
   return formatted_datetime

try:

   signer = oci.auth.signers.get_resource_principals_signer()
   object_storage_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
   ai_document_client = oci.ai_document.AIServiceDocumentClientCompositeOperations(oci.ai_document.AIServiceDocumentClient({}, signer=signer))


   if os.getenv("COMPARTMENT_OCID") is not None:
      compartment_ocid = os.getenv('COMPARTMENT_OCID')
   else:
      raise ValueError("ERROR: Missing configuration key  COMPARTMENT_OCID ")

   if os.getenv("NAMESPACE_NAME") is not None:
      namespace = os.getenv('NAMESPACE_NAME')
   else:
      raise ValueError("ERROR: Missing configuration key  NAMESPACE_NAME ")
   if os.getenv("SDK_RESULTS_STORAGE_BUCKET") is not None:
      sdk_results_storage_bucket = os.getenv('SDK_RESULTS_STORAGE_BUCKET')
   else:
      raise ValueError("ERROR: Missing configuration key  OUTPUT_STORAGE_BUCKET ")
   if os.getenv("INCOMING_DOCUMENTS_STORAGE_BUCKET") is not None:
      incoming_documents_storage_bucket = os.getenv('INCOMING_DOCUMENTS_STORAGE_BUCKET')
   else:
      raise ValueError("ERROR: Missing configuration key  INCOMING_DOCUMENTS_STORAGE_BUCKET ")
   if os.getenv("CLASSIFIED_DOCUMENTS_STORAGE_BUCKET") is not None:
      classified_documents_storage_bucket = os.getenv('CLASSIFIED_DOCUMENTS_STORAGE_BUCKET')
   else:
      raise ValueError("ERROR: Missing configuration key  CLASSIFIED_DOCUMENTS_STORAGE_BUCKET ")
   if os.getenv("ords-base-url") is not None:
      ordsbaseurl = os.getenv('ords-base-url')
   else:
      raise ValueError("ERROR: Missing configuration key  ords-base-url ")
   if os.getenv("dbpwd-cipher") is not None:
      dbpwd = os.getenv('dbpwd-cipher')
   else:
      raise ValueError("ERROR: Missing configuration key  dbpwd-cipher ")
   if os.getenv("db-schema") is not None:
      dbschema = os.getenv('db-schema')
   else:
      raise ValueError("ERROR: Missing configuration key  db-schema")
   if os.getenv("db-user") is not None:
      dbuser = os.getenv('db-user')
   else:
      raise ValueError("ERROR: Missing configuration key  db-user ")
   if os.getenv("classification-json-collection-name") is not None:
      classification_json_collection_name = os.getenv('classification-json-collection-name')
   else:
      raise ValueError("ERROR: Missing configuration key  classification-json-collection-name ")
   if os.getenv("kvextraction-json-collection-name") is not None:
      kvextraction_json_collection_name = os.getenv('kvextraction-json-collection-name')
   else:
      raise ValueError("ERROR: Missing configuration key  kvextraction-json-collection-name ")

except Exception as e:
   logging.getLogger().error(e)
   raise

def classify(document_name, namespace, sdk_results_storage_bucket):
   input_location = oci.ai_document.models.ObjectLocation()
   input_location.namespace_name = namespace
   input_location.bucket_name = incoming_documents_storage_bucket

   # Setup the output location where processor job results will be created
   output_location = oci.ai_document.models.OutputLocation()
   output_location.namespace_name = namespace
   output_location.bucket_name = sdk_results_storage_bucket
   output_location.prefix = "classify"
   logging.getLogger().info("Inside classify")
   # Set the object_name to classify
   input_location.object_name = document_name
   # Feature to invoke is the classification feature
   document_classification_feature = oci.ai_document.models.DocumentClassificationFeature()
    # Call the processor job
   create_processor_job_details = oci.ai_document.models.CreateProcessorJobDetails(
      display_name=str(uuid.uuid4()),
      input_location=oci.ai_document.models.ObjectStorageLocations(object_locations=[input_location]),
      output_location=output_location,

      compartment_id=compartment_ocid,
      processor_config=oci.ai_document.models.GeneralProcessorConfig(

         features=[document_classification_feature],

         is_zip_output_enabled=False
      )
   )
    # Wait for the processor job response
   create_processor_response = ai_document_client.create_processor_job_and_wait_for_state(
      create_processor_job_details=create_processor_job_details,
      wait_for_states=[oci.ai_document.models.ProcessorJob.LIFECYCLE_STATE_SUCCEEDED],
      waiter_kwargs={"wait_callback": create_processor_job_callback})
   # Get the output json from the bucket
   create_processor_job_response = create_processor_response.data
   process_job_id = create_processor_job_response.id
   get_object_response = object_storage_client.get_object(namespace_name=output_location.namespace_name,
                                             bucket_name=output_location.bucket_name,
                                             object_name="{}/{}/{}_{}/results/{}.json".format(
                                                output_location.prefix, process_job_id,
                                                input_location.namespace_name,
                                                input_location.bucket_name,
                                                input_location.object_name))
   # Get the inference json
   data = json.loads(get_object_response.data.content)
   # parse the response json to get the classified document type
   document_type = data['pages'][0]['detectedDocumentTypes'][0]['documentType']
   # soda_insert
   # Add new key-value pairs
   data['date_custom'] = generate_timestamp()
   data['process_job_id_custom'] = process_job_id
   data['document_name_custom'] = document_name 
   data['document_type'] = document_type
   soda_insert(ordsbaseurl, dbschema, dbuser, dbpwd, data, classification_json_collection_name)
   return document_type

def create_processor_job_callback(times_called, response):
   logging.getLogger().info("Waiting for processor lifecycle state to go into succeeded state:", response.data)


def move_classified_documents_to_bucket(document_name, document_type):
   logging.getLogger().info("inside move_classified_documents_to_bucket")
   # Get the document from source bucket
   response_object = object_storage_client.get_object(namespace, incoming_documents_storage_bucket, document_name)

   # decide the sub folder names in object storage bucket based on document type
   if document_type == 'INVOICE':
      folder_name = 'INVOICE'
   if document_type == 'DRIVER_LICENSE':
      folder_name = 'DRIVER_LICENSE'
   if document_type == 'PASSPORT':
      folder_name = 'PASSPORT'
   if document_type == 'BANK_STATEMENT':
      folder_name = 'BANK_STATEMENT'
   if document_type == 'RESUME':
      folder_name = 'RESUME'
   if document_type == 'RECEIPT':
      folder_name = 'RECEIPT'
   if document_type == 'PAYSLIP':
      folder_name = 'PAYSLIP'
   if document_type == 'OTHERS':
      folder_name = 'OTHERS'
   if document_type == 'TAX_FORM':
      folder_name = 'TAX_FORM'
   if document_type == 'CHECK':
      folder_name = 'CHECK'

   # Write to classified documents bucket
   with io.BytesIO() as buf:
      for chunk in response_object.data.raw.stream(1024 * 1024, decode_content=False):
         buf.write(chunk)
         buf.seek(0)

      object_storage_client.put_object(namespace, classified_documents_storage_bucket,
                               folder_name + '/' + document_name, buf.read())

# SODA call to perform DB insert
def soda_insert(ordsbaseurl, dbschema, dbuser, dbpwd, obj, json_collection_name):
    auth=(dbuser, dbpwd)
    sodaurl = ordsbaseurl + dbschema + '/soda/latest/'
    collectionurl = sodaurl + json_collection_name
    headers = {'Content-Type': 'application/json'}
    r = requests.post(collectionurl, auth=auth, headers=headers, data=json.dumps(obj))
    r_json = {}
    try:
        r_json = json.loads(r.text)
    except ValueError as e:
        print('SODA Insert Error: ' + str(e), flush=True)
        raise
    return r_json

# Handler method
def handler(ctx, data: io.BytesIO = None):
   try:
      body = json.loads(data.getvalue())
      document_name = body["data"]["resourceName"]
      document_type = classify(document_name, namespace, sdk_results_storage_bucket)
      # Move the documents to a classified_documents bucket
      move_classified_documents_to_bucket(document_name, document_type)
      extract_key_value(document_name, document_type, namespace, classified_documents_storage_bucket, sdk_results_storage_bucket, incoming_documents_storage_bucket)
   except Exception as handler_error:
      logging.getLogger().error(handler_error)
      return response.Response(
         ctx,
         status_code=500,
         response_data="Processing failed due to " + str(handler_error)
      )
   return response.Response(
      ctx,
      response_data="success"
   )

def extract_key_value(document_name, document_type, namespace, classified_documents_storage_bucket, sdk_results_storage_bucket, incoming_documents_storage_bucket):
   # Setup the output location where processor job results will be created
   output_location = oci.ai_document.models.OutputLocation()
   output_location.namespace_name = namespace
   output_location.bucket_name = sdk_results_storage_bucket
   output_location.prefix = "keyvalue"
   input_location = oci.ai_document.models.ObjectLocation()
   input_location.namespace_name = namespace
   input_location.bucket_name = classified_documents_storage_bucket
   input_location.bucket_name = incoming_documents_storage_bucket

   input_location.object_name = document_name
   key_value_detection_feature = oci.ai_document.models.DocumentKeyValueExtractionFeature()
   document_classification_feature = oci.ai_document.models.DocumentClassificationFeature()
   # Set up the Key-Value extraction processor job
   create_processor_job_details = oci.ai_document.models.CreateProcessorJobDetails(
      display_name=str(uuid.uuid4()),
      input_location=oci.ai_document.models.ObjectStorageLocations(object_locations=[input_location]),
      output_location=output_location,
      compartment_id=compartment_ocid,
      processor_config=oci.ai_document.models.GeneralProcessorConfig(

         features=[key_value_detection_feature, document_classification_feature],
         document_type=document_type,
         is_zip_output_enabled=False,
      )
   )

   # Wait for the processor job response
   create_processor_response = ai_document_client.create_processor_job_and_wait_for_state(
      create_processor_job_details=create_processor_job_details,
      wait_for_states=[oci.ai_document.models.ProcessorJob.LIFECYCLE_STATE_SUCCEEDED],
      waiter_kwargs={"wait_callback": create_processor_job_callback})
   # Get the output json from the bucket
   create_processor_job_response = create_processor_response.data
   process_job_id = create_processor_job_response.id
   get_object_response = object_storage_client.get_object(namespace_name=output_location.namespace_name,
                                             bucket_name=output_location.bucket_name,
                                             object_name="{}/{}/{}_{}/results/{}.json".format(
                                                output_location.prefix, process_job_id,
                                                input_location.namespace_name,
                                                input_location.bucket_name,
                                                input_location.object_name))
   # TODO-You can parse the response JSON and get the values of keys you defined.
   data = json.loads(get_object_response.data.content)
   # Add new key-value pairs
   data['date_custom'] = generate_timestamp()
   data['process_job_id_custom'] = process_job_id
   data['document_name_custom'] = document_name
   data['document_type_custom'] = document_type
   # TODO-Call your target application APIs by passing the extracted key values
   soda_insert(ordsbaseurl, dbschema, dbuser, dbpwd, data, kvextraction_json_collection_name)
