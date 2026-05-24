import pandas as pd
import uuid

from datetime import datetime
from sqlalchemy import text
import chardet
import csv
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
)

from app.database.snowflake_conn import get_engine
from app.agents.schema_agent import SchemaIntelligenceAgent

class IngestionAgent:

    def __init__(self):

        self.engine = get_engine()

    def ingest_csv(self, file):

        # Generate dataset id
        dataset_id = str(uuid.uuid4())[:8]

        # Dynamic table name
        cleaned_name = file.name.replace(".csv", "").replace(" ", "_")

        table_name = f"{cleaned_name}_{dataset_id}"

        # Read CSV
        # Read CSV safely

        # Read raw bytes
        raw_data = file.read()

        # Detect encoding
        encoding = chardet.detect(raw_data)["encoding"]

        # Reset pointer
        file.seek(0)

        # Detect delimiter
        sample = raw_data[:5000].decode(encoding, errors="ignore")

        sniffer = csv.Sniffer()

        delimiter = sniffer.sniff(sample).delimiter

        # Reset pointer again
        file.seek(0)

        # Read CSV dynamically
        df = pd.read_csv(
          file,
          encoding=encoding,
          delimiter=delimiter
          )
        # Upload to Snowflake
        df.to_sql(
            table_name,
            self.engine,
            schema="RAW",
            if_exists="replace",
            index=False
        )

        # Store metadata
        self.store_metadata(
            dataset_id,
            file.name,
            table_name
        )

        # Store schema information
        self.store_schema_info(
            dataset_id,
            df
        )
        schema_agent = SchemaIntelligenceAgent()

        schema_analysis = schema_agent.analyze_dataset(
        dataset_id,
        table_name
        )

        return {
            "dataset_id": dataset_id,
            "table_name": table_name,
            "columns": list(df.columns),
            "rows": len(df),
            "schema_analysis":schema_analysis
        }

    def store_metadata(
        self,
        dataset_id,
        dataset_name,
        table_name
    ):

        query = text("""
            INSERT INTO METADATA.uploaded_datasets
            VALUES (
                :dataset_id,
                :dataset_name,
                :upload_timestamp,
                :table_name,
                :status
            )
        """)

        with self.engine.connect() as connection:

            connection.execute(
                query,
                {
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "upload_timestamp": datetime.now(),
                    "table_name": table_name,
                    "status": "UPLOADED"
                }
            )

            connection.commit()

    def store_schema_info(
        self,
        dataset_id,
        df
    ):

        with self.engine.connect() as connection:

            for column in df.columns:

                query = text("""
                    INSERT INTO METADATA.schema_registry
                    VALUES (
                        :dataset_id,
                        :column_name,
                        :data_type
                    )
                """)

                connection.execute(
                    query,
                    {
                        "dataset_id": dataset_id,
                        "column_name": column,
                        "data_type": str(df[column].dtype)
                    }
                )

            connection.commit()