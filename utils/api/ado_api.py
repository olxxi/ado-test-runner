import requests
import json
import sqlite3
from sqlite3 import Error
from loguru import logger
from . import ado_parser
from ..constants import ADO_TOKEN, QUERY_LINK, WIQL_LINK, HEADERS, DB_NAME
# from utils.constants import ADO_TOKEN, QUERY_LINK, WIQL_LINK, HEADERS, DB_NAME
# from utils.api import ado_parser


def create_db_connection(db_file):
    """
    Create a database connection to a SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.debug(sqlite3.version)
        return conn
    except Error as e:
        logger.critical(f"Cannot connect to {db_file} database")

def get_query_name_by_query_id(query_id):
    """
    Returns query name by its id
    :param query_id:
    :return:
    """
    r_query = requests.get(QUERY_LINK + str(query_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        return parsed_data['name']

def get_test_cases_urls_by_query_id(query_id):
    """
    Get list of test case urls (Test Suite) by query ID
    :param query_id:
    :return:
    """
    r_query = requests.get(WIQL_LINK + str(query_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_urls_list = [test_case['url'] for test_case in parsed_data['workItems']]
        test_cases_ids_list = [test_case['id'] for test_case in parsed_data['workItems']]
        return dict(zip(test_cases_ids_list, test_case_urls_list))
    else:
        logger.critical(f"ADO returns status code {str(r_query.status_code)}. Check your ADO_TOKEN.")

def create_new_test_suite_in_db(query_id):
    logger.debug(query_id)
    logger.debug(ADO_TOKEN)
    test_cases_dict, test_suite_name = get_test_cases_urls_by_query_id(query_id), get_query_name_by_query_id(query_id)
    db_conn = create_db_connection(DB_NAME)
    db_cursor = db_conn.cursor()
    for id, url in test_cases_dict.items():
        logger.debug(id, url, test_suite_name)
        db_cursor.execute(f"INSERT INTO TEST_SUITES (TEST_SUITE_NAME, TEST_CASE_ID, TEST_CASE_URL) "
                          f"VALUES (?, ?, ?)", (test_suite_name, id, url))
        db_conn.commit()
    logger.info(f"{test_suite_name} was successfully added to the database. Contains {len(test_cases_dict)} test cases.")
    db_conn.close()
# create_new_test_suite_in_db("967b4daa-19d7-4966-a63c-0750ca1b56b8")

def get_test_suites_from_database():
    db_conn = create_db_connection(DB_NAME)
    db_cursor = db_conn.cursor()
    test_suites_db = db_cursor.execute("select distinct TEST_SUITE_NAME from TEST_SUITES").fetchall()
    test_suites_list = [suite[0] for suite in test_suites_db]
    return test_suites_list

def get_test_case_steps_by_url(test_case_url):
    """
    Get list of cleaned steps of the test case
    :param test_case_url:
    :return:
    """
    r_query = requests.get(test_case_url, headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        try:
            steps = parsed_data['fields']['Microsoft.VSTS.TCM.Steps']
        except KeyError:
            steps = "Test Case does not contain steps"
        # print(steps)
        steps_list = ado_parser.parse_html_steps(steps)
        return steps_list
# print(get_test_case_steps_by_url("https://dev.azure.com/HAL-LMKRD/d54c5f94-240d-4817-b74e-82588f96c6ba/_apis/wit/workItems/128710"))

def get_test_cases_from_db_by_suite_name(test_suite):
    db_conn = create_db_connection(DB_NAME)
    db_cursor = db_conn.cursor()
    test_cases_db = db_cursor.execute("select TEST_CASE_URL from TEST_SUITES where TEST_SUITE_NAME=(?)", (str(test_suite),)).fetchall()
    test_cases_list = [test_case[0] for test_case in test_cases_db]
    logger.info("something")
    return test_cases_list
# get_test_cases_from_db_by_suite_name('Velocity Test Cases')
