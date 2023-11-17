-- Create the CLASSIFICATIONDATA_MV materialized view
CREATE MATERIALIZED VIEW CLASSIFICATIONDATA_MV AS
    SELECT process_job_id_custom, date_custom, document_name_custom, document_type_custom FROM CLASSIFICATIONDATA,
        JSON_TABLE(
            KVEXTRACTIONDATA.JSON_DOCUMENT COLUMNS (
                NESTED PATH '$[*]' COLUMNS (
                    process_job_id_custom VARCHAR(255) PATH '$.process_job_id_custom',
                    date_custom VARCHAR(255) PATH '$.date_custom',
                    document_name_custom VARCHAR(255) PATH '$.document_name_custom',
                    document_type_custom VARCHAR(255) PATH '$.document_type_custom'
                )
            )
        );

-- Create the KVEXTRACTIONDATA_MV materialized view
CREATE MATERIALIZED VIEW KVEXTRACTIONDATA_MV AS
    SELECT process_job_id_custom, date_custom, document_name_custom, document_type_custom, fieldlabel, fieldvalue FROM KVEXTRACTIONDATA,
        JSON_TABLE(
            KVEXTRACTIONDATA.JSON_DOCUMENT COLUMNS (
                NESTED PATH '$[*]' COLUMNS (
                    process_job_id_custom VARCHAR(255) PATH '$.process_job_id_custom',
                    date_custom VARCHAR(255) PATH '$.date_custom',
                    document_name_custom VARCHAR(255) PATH '$.document_name_custom',
                    document_type_custom VARCHAR(255) PATH '$.document_type_custom'
                )
            )
        ) jt1,
        JSON_TABLE(
            KVEXTRACTIONDATA.JSON_DOCUMENT COLUMNS (
                NESTED PATH '$.pages[*].documentFields[*]' COLUMNS (
                    fieldlabel VARCHAR(255) PATH '$.fieldLabel.name',
                    fieldvalue VARCHAR(255) PATH '$.fieldValue.value'
                )
            )
        );

-- print the contents of the CLASSIFICATIONDATA_MV materialized view
SELECT * FROM CLASSIFICATIONDATA_MV;

-- print the contents of the KVEXTRACTIONDATA_MV materialized view
SELECT * FROM KVEXTRACTIONDATA_MV;

-- drop the CLASSIFICATIONDATA_MV materialized view
DROP MATERIALIZED VIEW CLASSIFICATIONDATA_MV;

-- drop the KVEXTRACTIONDATA_MV materialized view
DROP MATERIALIZED VIEW KVEXTRACTIONDATA_MV;
