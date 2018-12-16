import luigi
import os

TASK_NAMESPACE_ANALYSIS = 'analysis'


class CommonConfig(luigi.Config):
    task_namespace = TASK_NAMESPACE_ANALYSIS

    data_dir = os.getenv('ANALYSIS_DATA_PATH')
    database_summary_url = os.getenv('ANALYSIS_BATCH_DATABASE_SUMMARY_URL')
