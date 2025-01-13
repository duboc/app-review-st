from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types
from google.cloud.bigquery_storage_v1 import writer
from google.protobuf import descriptor_pb2
import pandas as pd
from typing import Dict, List
import uuid
import re

class BigQueryStorageWriter:
    def __init__(self):
        self.write_client = bigquery_storage_v1.BigQueryWriteClient()

    def normalize_column_name(self, name: str) -> str:
        """Convert column names to protobuf-compatible format."""
        # Convert camelCase to snake_case
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        # Replace any remaining invalid characters with underscore
        name = re.sub('[^a-z0-9_]', '_', name)
        return name

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize all column names in the DataFrame."""
        return df.rename(columns={col: self.normalize_column_name(col) for col in df.columns})

    def create_row_data(self, row: Dict) -> bytes:
        """Convert a row dictionary to protobuf serialized bytes."""
        # Create a unique review ID to prevent duplicates
        row['review_id'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{row['app_id']}_{row['review_id']}"))
        
        # Convert the row to protobuf format
        proto_row = types.ProtoRows()
        for key, value in row.items():
            # Convert value to string if it's not already
            if not isinstance(value, str):
                value = str(value)
            setattr(proto_row, key, value)
        
        return proto_row.SerializeToString()

    def append_rows(self, project_id: str, dataset_id: str, table_id: str, df: pd.DataFrame):
        """Append rows from a DataFrame to BigQuery using Storage Write API."""
        # Normalize column names
        df = self.normalize_dataframe(df)
        
        parent = self.write_client.table_path(project_id, dataset_id, table_id)
        stream_name = f'{parent}/_default'
        
        # Create write stream
        write_stream = types.WriteStream()
        request_template = types.AppendRowsRequest()
        request_template.write_stream = stream_name

        # Set up proto schema
        proto_schema = types.ProtoSchema()
        proto_descriptor = descriptor_pb2.DescriptorProto()
        
        # Define schema based on DataFrame columns
        for column in df.columns:
            field = proto_descriptor.field.add()
            field.name = column
            field.type = 9  # STRING type
            field.number = len(proto_descriptor.field)

        proto_schema.proto_descriptor = proto_descriptor
        proto_data = types.AppendRowsRequest.ProtoData()
        proto_data.writer_schema = proto_schema
        request_template.proto_rows = proto_data

        # Create append rows stream
        append_rows_stream = writer.AppendRowsStream(self.write_client, request_template)

        # Process rows in batches
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]
            
            # Convert batch to rows
            proto_rows = types.ProtoRows()
            for _, row in batch_df.iterrows():
                proto_rows.serialized_rows.append(
                    self.create_row_data(row.to_dict())
                )

            # Create and send request
            request = types.AppendRowsRequest()
            proto_data = types.AppendRowsRequest.ProtoData()
            proto_data.rows = proto_rows
            request.proto_rows = proto_data

            append_rows_stream.send(request)

        return f"Successfully appended {len(df)} rows to {parent}" 