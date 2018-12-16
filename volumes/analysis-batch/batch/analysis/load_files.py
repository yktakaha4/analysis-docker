import csv
import glob
import luigi
import os
import psycopg2
import re
import tempfile
import yaml

from batch.analysis.common_config import CommonConfig
from logging import getLogger

TASK_NAMESPACE_ANALYSIS = 'analysis'
logger = getLogger(__name__)


class LoadFilesTask(luigi.Task):
    task_namespace = TASK_NAMESPACE_ANALYSIS

    config = CommonConfig()

    source_files_path = luigi.Parameter()
    definition_files_path = luigi.Parameter()

    def run(self):
        logger.info('start loading...')
        logger.info('- - - - -')

        # 定義ファイル毎に処理
        for definition_file_path in glob.glob(os.path.join(self.definition_files_path, '*.yml')):
            # 定義読み込み
            logger.info('definitions: {}'.format(definition_file_path))
            with open(definition_file_path, 'r') as f:
                definition = yaml.load(f)

            # 処理対象を抽出
            target_files_path = self.filter_target(definition)

            logger.info('matching {} files...'.format(len(target_files_path)))
            if len(target_files_path) == 0:
                continue

            # 作業ファイルを作成
            with tempfile.TemporaryFile('w+') as tpf:
                # 処理対象を作業ファイルにマージ
                self.merge_files(tpf, definition, target_files_path)

                # 作業ファイルをDBへコピー
                self.copy_to_db(tpf, definition)

        logger.info('done.')

    def filter_target(self, definition):
        # 処理対象ファイルの抽出
        logger.info('pattern: {}'.format(definition['pattern']))
        target_files_path = []
        for source_file_path in glob.glob(self.source_files_path):
            if re.search(definition['pattern'], os.path.abspath(source_file_path)) is not None:
                target_files_path.append(source_file_path)

        return target_files_path

    def merge_files(self, tpf, definition, target_files_path):
        # 処理対象ファイルを整形
        logger.info('format target files...')
        file_format = definition['format']
        for target_file_path in target_files_path:
            # 処理対象ファイルを一つずつ処理
            logger.info('formatting: {}'.format(target_file_path))
            with open(target_file_path, 'r',
                      encoding=file_format['encoding'], newline=file_format['newline']) as tf:
                r = csv.reader(
                    tf, delimiter=file_format['delimiter'], doublequote=file_format['doublequote'],
                    escapechar=file_format['escapechar'], skipinitialspace=file_format['skipinitialspace'])

                w = csv.writer(tpf, delimiter='\t', quotechar='', quoting=csv.QUOTE_NONE, lineterminator='\n')

                # 行のスキップ
                for i in range(file_format['skip']):
                    next(r)

                # １行ずつ読み込み、整形を実施
                if 'replacers' in file_format:
                    logger.info('format with {} replacers...'.format(len(file_format['replacers'])))
                    for row in r:
                        for index, cell in enumerate(row):
                            for replacer in file_format['replacers']:
                                if ('index' not in replacer) or (replacer['index'] == index):
                                    cell = re.sub(replacer['pattern'], replacer['newvalue'], cell)
                            row[index] = cell
                        w.writerow(row)
                else:
                    for row in r:
                        w.writerow(row)

    def copy_to_db(self, tpf, definition):
        # DB接続
        logger.info('connect database...')
        with psycopg2.connect(self.config.database_summary_url) as conn:
            with conn.cursor() as cur:
                # DDLの実行
                if 'ddl' in definition:
                    logger.info('execute ddl...')
                    query = definition['ddl'].format(table_name=definition['table_name'])
                    logger.debug(query)
                    cur.execute(query)

                # COPYの実行
                logger.debug('execute copy...')
                tpf.seek(0)
                cur.copy_from(tpf, definition['table_name'])

                conn.commit()

        logger.info('close database...')
