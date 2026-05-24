import json
import pandas as pd

from sqlalchemy import text

from app.database.snowflake_conn import get_engine
from app.llm.gemini_client import get_gemini_client


class SchemaIntelligenceAgent:

    def __init__(self):

        self.engine = get_engine()

        self.client = get_gemini_client()

    def analyze_dataset(
        self,
        dataset_id,
        table_name
    ):

        query = f'''
    SELECT *
    FROM AI_ANALYTICS.RAW.{table_name}
    LIMIT 20
    '''

        df = pd.read_sql(query, self.engine)

        columns = list(df.columns)

        sample_data = df.head(5).to_dict(
            orient="records"
        )

        prompt = f"""
You are an enterprise AI data analyst.

Analyze this dataset.

Your tasks:

1. Detect business domain
2. Understand semantic meaning of each column
3. Identify KPIs
4. Classify columns as:
   - measure
   - dimension
   - timestamp
   - identifier
5. Suggest business dashboards

DATASET COLUMNS:
{columns}

SAMPLE DATA:
{sample_data}

Return ONLY valid JSON.

Expected JSON format:

{{
    "domain": "",

    "columns": [
        {{
            "column_name": "",
            "semantic_type": "",
            "business_meaning": "",
            "role": ""
        }}
    ],

    "kpis": [
        {{
            "kpi_name": "",
            "kpi_description": ""
        }}
    ],

    "dashboard_recommendations": []
}}
"""

        response=self.client.models.generate_content(model="gemini-2.0-flash",contents=prompt)

        raw_output=response.text
                                                     
                                                     

        # remove markdown formatting
        cleaned_output = raw_output.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        )

        parsed_result = json.loads(
            cleaned_output
        )

        self.store_analysis(
            dataset_id,
            table_name,
            len(df),
            len(columns),
            parsed_result
        )

        return parsed_result

    def store_analysis(
        self,
        dataset_id,
        table_name,
        total_rows,
        total_columns,
        result
    ):

        with self.engine.connect() as conn:

            # DATASET PROFILE
            profile_query = text("""
                INSERT INTO METADATA.dataset_profile
                VALUES (
                    :dataset_id,
                    :table_name,
                    :total_rows,
                    :total_columns,
                    :domain,
                    :created_at
                )
            """)

            conn.execute(
                profile_query,
                {
                    "dataset_id": dataset_id,
                    "table_name": table_name,
                    "total_rows": total_rows,
                    "total_columns": total_columns,
                    "domain": result["domain"],
                    "created_at": pd.Timestamp.now()
                }
            )

            # COLUMN CLASSIFICATION
            for column in result["columns"]:

                column_query = text("""
                    INSERT INTO METADATA.column_classification
                    VALUES (
                        :dataset_id,
                        :column_name,
                        :semantic_type,
                        :business_meaning,
                        :detected_role
                    )
                """)

                conn.execute(
                    column_query,
                    {
                        "dataset_id": dataset_id,
                        "column_name": column["column_name"],
                        "semantic_type": column["semantic_type"],
                        "business_meaning": column["business_meaning"],
                        "detected_role": column["role"]
                    }
                )

            # KPI STORAGE
            for kpi in result["kpis"]:

                kpi_query = text("""
                    INSERT INTO METADATA.detected_kpis
                    VALUES (
                        :dataset_id,
                        :kpi_name,
                        :kpi_description
                    )
                """)

                conn.execute(
                    kpi_query,
                    {
                        "dataset_id": dataset_id,
                        "kpi_name": kpi["kpi_name"],
                        "kpi_description": kpi["kpi_description"]
                    }
                )

            conn.commit()