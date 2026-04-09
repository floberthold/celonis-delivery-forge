import logging
import typing
import uuid
from abc import ABC
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr
from python_core_internal_client import AsyncClient, PythonCoreBaseEnum, PythonCoreBaseModel, PythonCoreDatetime

logger = logging.getLogger("python_core_internal_client.integration")


class DynamicVariableOpType(PythonCoreBaseEnum):
    FIND_MAX = "FIND_MAX"
    FIND_MIN = "FIND_MIN"
    LIST = "LIST"


class FilterParserDataType(PythonCoreBaseEnum):
    DATE = "DATE"
    DOUBLE = "DOUBLE"
    INT = "INT"
    STRING = "STRING"
    COLUMN = "COLUMN"
    QUALIFIED_COLUMN = "QUALIFIED_COLUMN"
    LIST_DOUBLE = "LIST_DOUBLE"
    LIST_INT = "LIST_INT"
    LIST_STRING = "LIST_STRING"
    NULL = "NULL"


class VariableType(PythonCoreBaseEnum):
    PRIVATE_CONSTANT = "PRIVATE_CONSTANT"
    PUBLIC_CONSTANT = "PUBLIC_CONSTANT"
    DYNAMIC = "DYNAMIC"


class TaskType(PythonCoreBaseEnum):
    EXTRACTION = "EXTRACTION"
    TRANSFORMATION = "TRANSFORMATION"
    DATA_MODEL_LOAD = "DATA_MODEL_LOAD"


class TemplateProtectionStatus(PythonCoreBaseEnum):
    OPEN = "OPEN"
    VIEWABLE = "VIEWABLE"
    PROTECTED = "PROTECTED"
    LOCKED = "LOCKED"


class ParameterType(PythonCoreBaseEnum):
    CUSTOM = "CUSTOM"
    DATASOURCE = "DATASOURCE"


class StreamingType(PythonCoreBaseEnum):
    SALESFORCE = "SALESFORCE"
    SERVICEBUS = "SERVICEBUS"
    EVENTHUB = "EVENTHUB"
    KAFKA = "KAFKA"


class ExecutionPattern(PythonCoreBaseEnum):
    HOURLY = "HOURLY"
    X_HOURLY = "X_HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class ExecutionStatus(PythonCoreBaseEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    CANCEL = "CANCEL"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class ExtractionMode(PythonCoreBaseEnum):
    FULL = "FULL"
    DELTA = "DELTA"


class MonthPattern(PythonCoreBaseEnum):
    SPECIFIC_DAY = "SPECIFIC_DAY"
    LAST_DAY = "LAST_DAY"


class SchedulingType(PythonCoreBaseEnum):
    FREQUENCY_BASED = "FREQUENCY_BASED"
    SCHEDULE_TRIGGERED = "SCHEDULE_TRIGGERED"


class ChangeDateOffsetType(PythonCoreBaseEnum):
    DAYS = "DAYS"
    HOURS = "HOURS"
    MINUTES = "MINUTES"


class DataPushDeleteStrategy(PythonCoreBaseEnum):
    DELETE = "DELETE"
    STORE_IN_STAGING_TABLE = "STORE_IN_STAGING_TABLE"
    IGNORE = "IGNORE"
    DELETE_AND_STORE_IN_STAGING_TABLE = "DELETE_AND_STORE_IN_STAGING_TABLE"


class JoinType(PythonCoreBaseEnum):
    NONE = "NONE"
    JOIN = "JOIN"
    COLUMN_VALUE = "COLUMN_VALUE"


class TableConfigurationParameterKey(PythonCoreBaseEnum):
    BATCH_SIZE = "BATCH_SIZE"
    ROLLING_PAGE_SIZE = "ROLLING_PAGE_SIZE"
    SPLIT_JOB_BY_DAYS = "SPLIT_JOB_BY_DAYS"
    MAX_STRING_LENGTH = "MAX_STRING_LENGTH"
    BINARY_HANDLING = "BINARY_HANDLING"
    DELTA_LOAD_AS_REPLACE_MERGE = "DELTA_LOAD_AS_REPLACE_MERGE"
    EXTRACT_DISPLAY_VALUES = "EXTRACT_DISPLAY_VALUES"
    METADATA_SOURCE = "METADATA_SOURCE"
    MAX_EXTRACTED_RECORDS = "MAX_EXTRACTED_RECORDS"
    PARTITION_COLUMNS = "PARTITION_COLUMNS"
    ORDER_COLUMNS = "ORDER_COLUMNS"
    REMOVE_DUPLICATES_WITH_ORDER = "REMOVE_DUPLICATES_WITH_ORDER"
    CHANGELOG_EXTRACTION_STRATEGY_OPTIONS = "CHANGELOG_EXTRACTION_STRATEGY_OPTIONS"
    CHANGELOG_TABLE_NAME = "CHANGELOG_TABLE_NAME"
    CHANGELOG_TABLE_NAME_COLUMN = "CHANGELOG_TABLE_NAME_COLUMN"
    CHANGELOG_ID_COLUMN = "CHANGELOG_ID_COLUMN"
    SOURCE_SYSTEM_JOIN_COLUMN = "SOURCE_SYSTEM_JOIN_COLUMN"
    CHANGELOG_JOIN_COLUMN = "CHANGELOG_JOIN_COLUMN"
    CHANGELOG_CHANGE_TYPE_COLUMN = "CHANGELOG_CHANGE_TYPE_COLUMN"
    CHANGELOG_DELETE_CHANGE_TYPE_IDENTIFIER = "CHANGELOG_DELETE_CHANGE_TYPE_IDENTIFIER"
    CHANGELOG_CLEANUP_METHOD = "CHANGELOG_CLEANUP_METHOD"
    CHANGELOG_CLEANUP_STATUS_COLUMN = "CHANGELOG_CLEANUP_STATUS_COLUMN"
    CHANGELOG_CLEANUP_STATUS_VALUE = "CHANGELOG_CLEANUP_STATUS_VALUE"
    CHANGELOG_CHANGE_TIMESTAMP_COLUMN = "CHANGELOG_CHANGE_TIMESTAMP_COLUMN"
    IGNORE_ERRORS_ON_RESPONSE = "IGNORE_ERRORS_ON_RESPONSE"
    STRING_COLUMN_LENGTH = "STRING_COLUMN_LENGTH"
    CURRENCY = "CURRENCY"
    FILE_EXTENSION_OPTIONS = "FILE_EXTENSION_OPTIONS"
    FILE_HAS_HEADER_ROW = "FILE_HAS_HEADER_ROW"
    FILE_ENCODING = "FILE_ENCODING"
    FIELD_SEPARATOR = "FIELD_SEPARATOR"
    QUOTE_CHARACTER = "QUOTE_CHARACTER"
    ESCAPE_SEQUENCE = "ESCAPE_SEQUENCE"
    DECIMAL_SEPARATOR = "DECIMAL_SEPARATOR"
    THOUSAND_SEPARATOR = "THOUSAND_SEPARATOR"
    LINE_ENDING = "LINE_ENDING"
    DATA_FORMAT = "DATA_FORMAT"
    CURRENCY_FROM = "CURRENCY_FROM"
    CURRENCY_TO = "CURRENCY_TO"
    CONVERSION_TYPE = "CONVERSION_TYPE"
    PAGINATION_WINDOW_IN_DAYS = "PAGINATION_WINDOW_IN_DAYS"


class TableExtractionType(PythonCoreBaseEnum):
    PARENT_TABLE = "PARENT_TABLE"
    DEPENDENT_TABLE = "DEPENDENT_TABLE"
    NESTED_TABLE = "NESTED_TABLE"


class ColumnType(PythonCoreBaseEnum):
    INTEGER = "INTEGER"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"


class DataPushUpsertStrategy(PythonCoreBaseEnum):
    UPSERT_WITH_UNCHANGED_METADATA = "UPSERT_WITH_UNCHANGED_METADATA"
    UPSERT_WITH_NULLIFICATION = "UPSERT_WITH_NULLIFICATION"


class FileDataTableType(PythonCoreBaseEnum):
    EXCEL = "EXCEL"
    CSV = "CSV"
    PARQUET = "PARQUET"
    JSON = "JSON"
    XES = "XES"


class CustomExtractorApiType(PythonCoreBaseEnum):
    DEFAULT = "DEFAULT"
    ODATA_V2 = "ODATA_V2"
    ODATA_V4 = "ODATA_V4"


class CustomExtractorAuthenticationMethod(PythonCoreBaseEnum):
    BASIC_AUTHENTICATION = "BASIC_AUTHENTICATION"
    BEARER_AUTHENTICATION = "BEARER_AUTHENTICATION"
    API_KEY_AUTHENTICATION = "API_KEY_AUTHENTICATION"
    OAUTH2_AUTHORIZATION_CODE = "OAUTH2_AUTHORIZATION_CODE"
    OAUTH2_AUTHORIZATION_CODE_REFRESH_TOKEN = "OAUTH2_AUTHORIZATION_CODE_REFRESH_TOKEN"
    OAUTH2_CLIENT_CREDENTIALS = "OAUTH2_CLIENT_CREDENTIALS"
    OAUTH2_RESOURCE_OWNER_CREDENTIALS = "OAUTH2_RESOURCE_OWNER_CREDENTIALS"
    OAUTH2_JWT_BEARER = "OAUTH2_JWT_BEARER"
    OAUTH2_PROXY = "OAUTH2_PROXY"


class CustomExtractorColumnType(PythonCoreBaseEnum):
    INTEGER = "INTEGER"
    DATETIME = "DATETIME"
    DATE = "DATE"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    TEXT = "TEXT"


class CustomExtractorErrorHandlingOperator(PythonCoreBaseEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    NOT_CONTAINS = "NOT_CONTAINS"
    CONTAINS = "CONTAINS"


class CustomExtractorErrorHandlingOption(PythonCoreBaseEnum):
    HTTP_STATUS = "HTTP_STATUS"
    HTTP_RESPONSE_BODY = "HTTP_RESPONSE_BODY"
    JSON_FIELD_IN_RESPONSE = "JSON_FIELD_IN_RESPONSE"


class CustomExtractorPaginationMethod(PythonCoreBaseEnum):
    PAGE_BY_PAGE_PAGINATION = "PAGE_BY_PAGE_PAGINATION"
    LIMIT_AND_OFFSET_PAGINATION = "LIMIT_AND_OFFSET_PAGINATION"
    NEXT_PAGE_URL_IN_RESPONSE_PAGINATION = "NEXT_PAGE_URL_IN_RESPONSE_PAGINATION"
    NEXT_PAGE_TOKEN_IN_RESPONSE_PAGINATION = "NEXT_PAGE_TOKEN_IN_RESPONSE_PAGINATION"
    WEB_LINKING_PAGINATION = "WEB_LINKING_PAGINATION"
    INCREMENT_FILTER_PARAMETER_PAGINATION = "INCREMENT_FILTER_PARAMETER_PAGINATION"


class CustomExtractorResponseType(PythonCoreBaseEnum):
    JSON = "JSON"
    XML = "XML"


class JwtSignatureAlgorithm(PythonCoreBaseEnum):
    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"


class DataTransferExportType(PythonCoreBaseEnum):
    ALL = "ALL"
    LIMITED = "LIMITED"


class ReachableAndValidOption(PythonCoreBaseEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class AutoMergeExecutionMode(PythonCoreBaseEnum):
    DISTINCT = "DISTINCT"
    NON_DISTINCT = "NON_DISTINCT"


class CalendarDay(PythonCoreBaseEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class DataModelCalendarType(PythonCoreBaseEnum):
    NONE = "NONE"
    CUSTOM = "CUSTOM"
    FACTORY = "FACTORY"


class DataModelSignalLinkColumnDirection(PythonCoreBaseEnum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class DataPermissionType(PythonCoreBaseEnum):
    TABLES = "TABLES"
    MANUAL = "MANUAL"
    SYNCHRONIZED = "SYNCHRONIZED"


class AdvancedDataPermissionMode(PythonCoreBaseEnum):
    AND = "AND"
    OR = "OR"


class DataPermissionAssignmentType(PythonCoreBaseEnum):
    VALUE = "VALUE"
    UNLIMITED = "UNLIMITED"


class DataPermissionSyncStatus(PythonCoreBaseEnum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataPermissionTableType(PythonCoreBaseEnum):
    USER = "USER"
    GROUP = "GROUP"


class PoolConfigurationStatus(PythonCoreBaseEnum):
    NEW_CUSTOM_POOL_WITHOUT_TARGET_CONFIGURATION = "NEW_CUSTOM_POOL_WITHOUT_TARGET_CONFIGURATION"
    NEW = "NEW"
    DATA_SOURCES_CONFIGURED = "DATA_SOURCES_CONFIGURED"
    OPTIONS_CONFIGURED = "OPTIONS_CONFIGURED"
    CONFIGURED = "CONFIGURED"


class DatabaseTenancyType(PythonCoreBaseEnum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"


class DatabaseType(PythonCoreBaseEnum):
    MSSQL = "MSSQL"
    HANA = "HANA"


class PoolProviderType(PythonCoreBaseEnum):
    HDFS = "HDFS"
    DATABASE = "DATABASE"
    CUSTOM = "CUSTOM"
    HIVE = "HIVE"
    MOCK = "MOCK"


class AnonymizationAlgorithm(PythonCoreBaseEnum):
    SHA_1 = "SHA_1"
    SHA_256 = "SHA_256"
    SHA_256_NO_SALT = "SHA_256_NO_SALT"
    SHA_512 = "SHA_512"
    SHA_512_NO_SALT = "SHA_512_NO_SALT"


class ZendeskAuthMethods(PythonCoreBaseEnum):
    OAUTH = "OAUTH"
    STOREDCREDENTIALS = "STOREDCREDENTIALS"


class WorkdayApiVersion(PythonCoreBaseEnum):
    V33 = "v33"
    V34_2 = "v34_2"


class WorkdayAuthMethods(PythonCoreBaseEnum):
    OAUTH = "OAUTH"
    STOREDCREDENTIALS = "STOREDCREDENTIALS"


class DataSourceEnvironment(PythonCoreBaseEnum):
    SANDBOX = "SANDBOX"
    PROD = "PROD"


class ServiceNowAuthMethods(PythonCoreBaseEnum):
    STOREDCREDENTIALS = "STOREDCREDENTIALS"
    OAUTH = "OAUTH"


class SapSnsVersions(PythonCoreBaseEnum):
    V1 = "V1"
    V2 = "V2"


class CompressionType(PythonCoreBaseEnum):
    GZIP = "GZIP"
    SEVEN_ZIP = "SEVEN_ZIP"
    SAPCAR = "SAPCAR"
    ABAP_ZIP = "ABAP_ZIP"
    UNCOMPRESSED = "UNCOMPRESSED"


class Middleware(PythonCoreBaseEnum):
    NONE = "NONE"
    PI_PO = "PI_PO"
    MESSAGE_SERVER = "MESSAGE_SERVER"


class PiPoAdapter(PythonCoreBaseEnum):
    SOAP = "SOAP"
    RFC = "RFC"


class SapVersion(PythonCoreBaseEnum):
    ECC_5_OR_HIGHER = "ECC_5_OR_HIGHER"
    ECC_4 = "ECC_4"


class SalesForceAuthMethods(PythonCoreBaseEnum):
    OAUTH = "OAUTH"
    CONSUMER_OAUTH = "CONSUMER_OAUTH"
    STOREDCREDENTIALS = "STOREDCREDENTIALS"


class SalesforceProxyService(PythonCoreBaseEnum):
    NO_PROXY_SERVICE = "NO_PROXY_SERVICE"
    MIDDLEWARE = "MIDDLEWARE"


class OracleCloudInstanceVersions(PythonCoreBaseEnum):
    V18_A = "V18A"
    V18_B = "V18B"
    V18_C = "V18C"
    V20_A = "V20A"
    V20_B = "V20B"
    V20_C = "V20C"


class FieldglassApiGroup(PythonCoreBaseEnum):
    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    APPROVAL = "APPROVAL"
    AUDIT_TRAIL = "AUDIT_TRAIL"


class CoupaApiVersion(PythonCoreBaseEnum):
    R21 = "R21"
    R22 = "R22"
    R23 = "R23"
    R24 = "R24"
    R25 = "R25"
    R26 = "R26"
    R27 = "R27"


class CoupaAuthMethods(PythonCoreBaseEnum):
    OAUTH = "OAUTH"
    API_KEY = "API_KEY"


class AribaApiGroup(PythonCoreBaseEnum):
    PROCUREMENT = "PROCUREMENT"
    SOURCING = "SOURCING"
    ANALYTICAL_REPORTING = "ANALYTICAL_REPORTING"
    CONTRACT_COMPLIANCE = "CONTRACT_COMPLIANCE"
    SUPPLIER_DATA = "SUPPLIER_DATA"
    EXTERNAL_APPROVAL = "EXTERNAL_APPROVAL"
    DOCUMENT_APPROVAL = "DOCUMENT_APPROVAL"
    CUSTOM_FORMS = "CUSTOM_FORMS"
    MASTER_DATA = "MASTER_DATA"


class AribaProxyService(PythonCoreBaseEnum):
    NO_PROXY_SERVICE = "NO_PROXY_SERVICE"
    PI_PO = "PI_PO"
    APIGEE = "APIGEE"


class AribaRegion(PythonCoreBaseEnum):
    US = "US"
    EU = "EU"
    RU = "RU"
    JP = "JP"
    UAE = "UAE"
    KSA = "KSA"
    CN = "CN"
    AU = "AU"


class AribaTemplateType(PythonCoreBaseEnum):
    STANDARD = "STANDARD"
    STANDARD_V1 = "STANDARD_V1"
    STANDARD_V2 = "STANDARD_V2"
    CUSTOM = "CUSTOM"


class AmazonS3Region(PythonCoreBaseEnum):
    GOV_CLOUD = "GovCloud"
    US_GOV_EAST_1 = "US_GOV_EAST_1"
    US_EAST_1 = "US_EAST_1"
    US_EAST_2 = "US_EAST_2"
    US_WEST_1 = "US_WEST_1"
    US_WEST_2 = "US_WEST_2"
    EU_WEST_1 = "EU_WEST_1"
    EU_WEST_2 = "EU_WEST_2"
    EU_WEST_3 = "EU_WEST_3"
    EU_CENTRAL_1 = "EU_CENTRAL_1"
    EU_NORTH_1 = "EU_NORTH_1"
    AP_EAST_1 = "AP_EAST_1"
    AP_SOUTH_1 = "AP_SOUTH_1"
    AP_SOUTHEAST_1 = "AP_SOUTHEAST_1"
    AP_SOUTHEAST_2 = "AP_SOUTHEAST_2"
    AP_NORTHEAST_1 = "AP_NORTHEAST_1"
    AP_NORTHEAST_2 = "AP_NORTHEAST_2"
    SA_EAST_1 = "SA_EAST_1"
    CN_NORTH_1 = "CN_NORTH_1"
    CN_NORTHWEST_1 = "CN_NORTHWEST_1"
    CA_CENTRAL_1 = "CA_CENTRAL_1"
    ME_SOUTH_1 = "ME_SOUTH_1"


class SerializationType(PythonCoreBaseEnum):
    JSON = "JSON"
    YAML = "YAML"


class JobStatus(PythonCoreBaseEnum):
    NEW = "NEW"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"
    CANCELED = "CANCELED"


class JobType(PythonCoreBaseEnum):
    REPLACE = "REPLACE"
    DELTA = "DELTA"


class UploadFileType(PythonCoreBaseEnum):
    PARQUET = "PARQUET"
    CSV = "CSV"


class DataPermissionStrategy(PythonCoreBaseEnum):
    AND = "AND"
    OR = "OR"


class ExportType(PythonCoreBaseEnum):
    PARQUET = "PARQUET"
    EXCEL = "EXCEL"
    CSV = "CSV"


class ExportStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class UplinkRegistrationType(PythonCoreBaseEnum):
    CELONIS4 = "CELONIS4"
    CONNECTOR = "CONNECTOR"


class ExceptionType(PythonCoreBaseEnum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class ExecutionLogMessageType(PythonCoreBaseEnum):
    RUN = "RUN"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    CANCEL = "CANCEL"
    INFO = "INFO"
    WARN = "WARN"
    DEBUG = "DEBUG"
    SKIPPED = "SKIPPED"


class ExecutionMessageCode(PythonCoreBaseEnum):
    CONNECTOR_BUILDER_INFER_DUPLICATE_COLUMN = "CONNECTOR_BUILDER_INFER_DUPLICATE_COLUMN"
    CONNECTOR_BUILDER_INFER_TYPE_MISMATCH = "CONNECTOR_BUILDER_INFER_TYPE_MISMATCH"
    CONNECTOR_BUILDER_INFER_UNKNOWN_TYPE = "CONNECTOR_BUILDER_INFER_UNKNOWN_TYPE"
    CONNECTOR_BUILDER_INFER_INVALID_JSON = "CONNECTOR_BUILDER_INFER_INVALID_JSON"
    CONNECTOR_BUILDER_RESPONSE_ROOT_NOT_OBJECT = "CONNECTOR_BUILDER_RESPONSE_ROOT_NOT_OBJECT"
    CONNECTOR_BUILDER_INVALID_RESPONSE_ROOT = "CONNECTOR_BUILDER_INVALID_RESPONSE_ROOT"
    CONNECTOR_BUILDER_GET_SAMPLES_FAILED = "CONNECTOR_BUILDER_GET_SAMPLES_FAILED"
    CANCELING_EXTRACTION = "CANCELING_EXTRACTION"
    AT_LEAST_ONE_TABLE_EXTRACTION_FAILED = "AT_LEAST_ONE_TABLE_EXTRACTION_FAILED"
    STARTING_LOADING_TABLE_TO_TARGET = "STARTING_LOADING_TABLE_TO_TARGET"
    STARTING_RUNNING_JOB = "STARTING_RUNNING_JOB"
    EXTRACTION_SUCCESSFUL = "EXTRACTION_SUCCESSFUL"
    WAITING_FOR_SUCCESS_STATE = "WAITING_FOR_SUCCESS_STATE"
    REACHED_DATA_PUSH_JOB_LIMIT = "REACHED_DATA_PUSH_JOB_LIMIT"
    LOADING_TABLE = "LOADING_TABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    EXTRACTION_FAILED_WITH_EXCEPTION = "EXTRACTION_FAILED_WITH_EXCEPTION"
    EXTRACTION_FAILED_AFTER_RETRY_EXHAUSTED = "EXTRACTION_FAILED_AFTER_RETRY_EXHAUSTED"
    STOPPED_RETRYING_DATAPUSHJOB_CREATION = "STOPPED_RETRYING_DATAPUSHJOB_CREATION"
    USING_TARGET_TABLE_NAME = "USING_TARGET_TABLE_NAME"
    PUSHING_FILE_FOR_TABLE = "PUSHING_FILE_FOR_TABLE"
    CALLED_UPLOAD_FILE = "CALLED_UPLOAD_FILE"
    STARTING_EXTRACTION_FOR_RESOURCE = "STARTING_EXTRACTION_FOR_RESOURCE"
    NUMBER_OF_RECORDS_THAT_WILL_BE_EXTRACTED = "NUMBER_OF_RECORDS_THAT_WILL_BE_EXTRACTED"
    FINAL_COUNT_FOR_TABLE = "FINAL_COUNT_FOR_TABLE"
    EMPTY_RESPONSE_FROM_EXTRACTOR = "EMPTY_RESPONSE_FROM_EXTRACTOR"
    EXTRACTOR_NOT_REACHABLE = "EXTRACTOR_NOT_REACHABLE"
    INTEGRATION_NOT_USED_BY_TYPE = "INTEGRATION_NOT_USED_BY_TYPE"
    INTERNAL_ERROR_FROM_EXTRACTOR = "INTERNAL_ERROR_FROM_EXTRACTOR"
    ERROR_WHILE_MAKING_CAPABILITIES_REQUEST = "ERROR_WHILE_MAKING_CAPABILITIES_REQUEST"
    UPLINK_NOT_REACHABLE = "UPLINK_NOT_REACHABLE"
    CONNECTION_CONFIGURATION_VALID = "CONNECTION_CONFIGURATION_VALID"
    CONNECTION_CONFIGURATION_INVALID = "CONNECTION_CONFIGURATION_INVALID"
    CONNECTION_CHECK_MISSING_JDBC_DRIVER = "CONNECTION_CHECK_MISSING_JDBC_DRIVER"
    CPP_2013_PACKAGES_NOT_INSTALLED = "CPP_2013_PACKAGES_NOT_INSTALLED"
    EXTRACTOR_VERSION_DOES_NOT_SUPPORT_COMPRESSION = "EXTRACTOR_VERSION_DOES_NOT_SUPPORT_COMPRESSION"
    EXTRACTOR_VERSION_DOES_NOT_SUPPORT_ADVANCED_SETTINGS = "EXTRACTOR_VERSION_DOES_NOT_SUPPORT_ADVANCED_SETTINGS"
    NECESSARY_FUNCTION_NOT_IMPLEMENTED_IN_SAP = "NECESSARY_FUNCTION_NOT_IMPLEMENTED_IN_SAP"
    UPDATE_RFC_TO_USE_ZIP = "UPDATE_RFC_TO_USE_ZIP"
    ERROR_DURING_CONNECTION_VALIDATION = "ERROR_DURING_CONNECTION_VALIDATION"
    SAP_ERR_NETWORK = "SAP_ERR_NETWORK"
    SAP_ERR_NO_RFC_PING_AUTH = "SAP_ERR_NO_RFC_PING_AUTH"
    SAP_ERR_NO_AUTH = "SAP_ERR_NO_AUTH"
    RFC_ERR_FILE_PERMISSIONS = "RFC_ERR_FILE_PERMISSIONS"
    RFC_ERR_WRITE_FILE = "RFC_ERR_WRITE_FILE"
    RFC_ERR_COMPRESS_FILE = "RFC_ERR_COMPRESS_FILE"
    RFC_ERR_COMPRESS_FILE_NOT_FOUND = "RFC_ERR_COMPRESS_FILE_NOT_FOUND"
    RFC_ERR_DELETE_FILE = "RFC_ERR_DELETE_FILE"
    RFC_ERR_LIST_FILES = "RFC_ERR_LIST_FILES"
    RFC_ERR_GENERIC = "RFC_ERR_GENERIC"
    RFC_WARN_DEFAULT_TARGET_PATH = "RFC_WARN_DEFAULT_TARGET_PATH"
    JCO_NOT_FOUND = "JCO_NOT_FOUND"
    JCO_NATIVE_LIB_NOT_FOUND = "JCO_NATIVE_LIB_NOT_FOUND"
    JCO_NATIVE_LIB_UNSUPPORTED_OS = "JCO_NATIVE_LIB_UNSUPPORTED_OS"
    JCO_NATIVE_LIB_COPY_ERROR = "JCO_NATIVE_LIB_COPY_ERROR"
    SAP_CHECK_JCO_JAR_INSTALLED = "SAP_CHECK_JCO_JAR_INSTALLED"
    SAP_CHECK_JCO_NATIVE_LIB_INSTALLED = "SAP_CHECK_JCO_NATIVE_LIB_INSTALLED"
    SAP_CHECK_MSVC_2013_INSTALLED = "SAP_CHECK_MSVC_2013_INSTALLED"
    SAP_CHECK_NETWORK = "SAP_CHECK_NETWORK"
    SAP_CHECK_NECESSARY_FUNCTIONS_IMPLEMENTED_IN_SAP = "SAP_CHECK_NECESSARY_FUNCTIONS_IMPLEMENTED_IN_SAP"
    SAP_CHECK_EXTRACTOR_VERSION_SUPPORT_COMPRESSION = "SAP_CHECK_EXTRACTOR_VERSION_SUPPORT_COMPRESSION"
    SAP_CHECK_PARQUET_WRITING = "SAP_CHECK_PARQUET_WRITING"
    SAP_CHECK_RFC_TEST_FILE_CREATION = "SAP_CHECK_RFC_TEST_FILE_CREATION"
    SAP_CHECK_RFC_TEST_FILE_COMPRESSION = "SAP_CHECK_RFC_TEST_FILE_COMPRESSION"
    SAP_CHECK_RFC_TEST_FILE_DELETION = "SAP_CHECK_RFC_TEST_FILE_DELETION"
    SAP_CHECK_RFC_LIST_FILES = "SAP_CHECK_RFC_LIST_FILES"
    INTERNAL_ERROR_PERFORMING_TEST = "INTERNAL_ERROR_PERFORMING_TEST"
    SAP_CONFIGURATION_VALIDATION_FAILED = "SAP_CONFIGURATION_VALIDATION_FAILED"
    NO_FILE_RECEIVED_FROM_SAP = "NO_FILE_RECEIVED_FROM_SAP"
    CHANGE_LOG_ENABLED_NECESSARY_FUNCTION_NOT_IMPLEMENTED_IN_SAP = (
        "CHANGE_LOG_ENABLED_NECESSARY_FUNCTION_NOT_IMPLEMENTED_IN_SAP"
    )
    ERROR_RUNNING_VALIDATION_FUNCTION = "ERROR_RUNNING_VALIDATION_FUNCTION"
    NO_RUNNABLE_EXTRACTIONS_OR_TRANSFORMATIONS = "NO_RUNNABLE_EXTRACTIONS_OR_TRANSFORMATIONS"
    DATA_CONSUMPTION_LIMIT_EXCEEDED = "DATA_CONSUMPTION_LIMIT_EXCEEDED"
    STARTING_EXECUTION_OF_EXTRACTION = "STARTING_EXECUTION_OF_EXTRACTION"
    JOB_HAS_NO_DATA_SOURCE = "JOB_HAS_NO_DATA_SOURCE"
    DATASOURCE_NOT_REACHABLE = "DATASOURCE_NOT_REACHABLE"
    DATASOURCE_CONFIGURATION_IS_INVALID = "DATASOURCE_CONFIGURATION_IS_INVALID"
    REQUIRED_FEATURE_NOT_ENABLED = "REQUIRED_FEATURE_NOT_ENABLED"
    CANNOT_READ_DATA_SOURCE = "CANNOT_READ_DATA_SOURCE"
    CANNOT_RETRIEVE_EXTRACTOR_METADATA = "CANNOT_RETRIEVE_EXTRACTOR_METADATA"
    AMBIGUOUS_TABLE_NAME_IN_EXTRACTION = "AMBIGUOUS_TABLE_NAME_IN_EXTRACTION"
    METADATA_HAS_CHANGED = "METADATA_HAS_CHANGED"
    NO_TABLE_IN_EXTRACTION = "NO_TABLE_IN_EXTRACTION"
    EXTRACTION_IS_SKIPPED = "EXTRACTION_IS_SKIPPED"
    VARIABLE_RESOLVING_ERROR = "VARIABLE_RESOLVING_ERROR"
    DELETE_ONLY_POSSIBLE_FOR_DELTA = "DELETE_ONLY_POSSIBLE_FOR_DELTA"
    TABLE_MAPPING_ERROR = "TABLE_MAPPING_ERROR"
    JOB_EXECUTION_CANCELLED = "JOB_EXECUTION_CANCELLED"
    ERROR_STARTING_EXTRACTION = "ERROR_STARTING_EXTRACTION"
    VERSION_INFORMATION = "VERSION_INFORMATION"
    DATA_CONNECTION_CONFIGURATION = "DATA_CONNECTION_CONFIGURATION"
    TABLE_CONFIGURATION = "TABLE_CONFIGURATION"
    TABLE_SUCCESSFULLY_EXTRACTED = "TABLE_SUCCESSFULLY_EXTRACTED"
    ERROR_COMPLETING_TABLE_LOAD = "ERROR_COMPLETING_TABLE_LOAD"
    INVALID_EXTRACTION_IS_RUNNING = "INVALID_EXTRACTION_IS_RUNNING"
    GOT_CHUNK_FOR_TERMINAL_EXTRACTION = "GOT_CHUNK_FOR_TERMINAL_EXTRACTION"
    CANCELING_EXTRACTION_WITH_NAME = "CANCELING_EXTRACTION_WITH_NAME"
    GOT_CHUNK_FOR_TABLE = "GOT_CHUNK_FOR_TABLE"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    JOB_ALREADY_RUNNING = "JOB_ALREADY_RUNNING"
    STARTING_RUNNING_JOB_WITH_NAME = "STARTING_RUNNING_JOB_WITH_NAME"
    EARLIER_JOB_IN_SCHEDULE_FAILED_OR_CANCELLED = "EARLIER_JOB_IN_SCHEDULE_FAILED_OR_CANCELLED"
    JOB_COULD_NOT_STARTED = "JOB_COULD_NOT_STARTED"
    EXECUTING_JOB_IN_SCHEDULE = "EXECUTING_JOB_IN_SCHEDULE"
    JOB_ALREADY_RUNNING_CANNOT_EXECUTE_SCHEDULE = "JOB_ALREADY_RUNNING_CANNOT_EXECUTE_SCHEDULE"
    CANNOT_EXECUTE_SCHEDULED_JOBS = "CANNOT_EXECUTE_SCHEDULED_JOBS"
    EXECUTION_CANCELED_ON_REQUEST = "EXECUTION_CANCELED_ON_REQUEST"
    EXECUTION_AUTOMATICALLY_CANCELLED_AFTER_X_MINUTES = "EXECUTION_AUTOMATICALLY_CANCELLED_AFTER_X_MINUTES"
    EXECUTION_CANCELED_AFTER_CONNECTOR_DISCONNECT = "EXECUTION_CANCELED_AFTER_CONNECTOR_DISCONNECT"
    REMOVING_TMP_FOLDER = "REMOVING_TMP_FOLDER"
    CANNOT_REMOVE_TMP_FOLDER = "CANNOT_REMOVE_TMP_FOLDER"
    CHECKING_SOURCE_SYSTEM_METADATA_CHANGE = "CHECKING_SOURCE_SYSTEM_METADATA_CHANGE"
    UNABLE_GET_COLUMNS_FOR_TABLE = "UNABLE_GET_COLUMNS_FOR_TABLE"
    NO_METADATA_FOUND_FOR_COMPARISON = "NO_METADATA_FOUND_FOR_COMPARISON"
    COLUMNS_HAVE_CHANGED = "COLUMNS_HAVE_CHANGED"
    CANNOT_MAP_TABLE_NAME_IN_EXTRACTION = "CANNOT_MAP_TABLE_NAME_IN_EXTRACTION"
    COLUMN_SMALL_FOR_ANONYMIZATION = "COLUMN_SMALL_FOR_ANONYMIZATION"
    COLUMN_INVALID_FOR_ANONYMIZATION = "COLUMN_INVALID_FOR_ANONYMIZATION"
    METADATA_CHANGED_FOR_TABLE = "METADATA_CHANGED_FOR_TABLE"
    FAILED_TO_START_EXECUTION_ITEM = "FAILED_TO_START_EXECUTION_ITEM"
    FAILED_TO_CHANGE_EXECUTION_ITEM_STATUS = "FAILED_TO_CHANGE_EXECUTION_ITEM_STATUS"
    DELTA_LOAD_HAS_NO_FILTER = "DELTA_LOAD_HAS_NO_FILTER"
    WSDL_FILE_NOT_FOUND = "WSDL_FILE_NOT_FOUND"
    WSDL_MULTIPLE_FILES_FOUND = "WSDL_MULTIPLE_FILES_FOUND"
    WSDL_DIRECTORY_NOT_READABLE = "WSDL_DIRECTORY_NOT_READABLE"
    WSDL_DIRECTORY_IS_EMPTY = "WSDL_DIRECTORY_IS_EMPTY"
    WSDL_PORT_NOT_FOUND = "WSDL_PORT_NOT_FOUND"
    EXTRACTING_FROM_ROW = "EXTRACTING_FROM_ROW"
    NO_VALUE_FOUND_IN_FIRST_COLUMN = "NO_VALUE_FOUND_IN_FIRST_COLUMN"
    ERROR_WHILE_EXTRACTING_TABLE = "ERROR_WHILE_EXTRACTING_TABLE"
    ERROR_RETRIEVING_SPREADSHEET = "ERROR_RETRIEVING_SPREADSHEET"
    GOOGLE_SHEETS_API_LIMIT_REACHED = "GOOGLE_SHEETS_API_LIMIT_REACHED"
    MISSING_FULL_LOAD_COLUMN = "MISSING_FULL_LOAD_COLUMN"
    MISSING_DELTA_LOAD_COLUMN = "MISSING_DELTA_LOAD_COLUMN"
    CONTAINS_FAULTY_COLUMN = "CONTAINS_FAULTY_COLUMN"
    MISSING_MANDATORY_DATE_FILTER_COLUMN = "MISSING_MANDATORY_DATE_FILTER_COLUMN"
    EMPTY_DIRECTORY_AS_TABLE = "EMPTY_DIRECTORY_AS_TABLE"
    DIRECTORY_CONTAINS_MULTIPLE_TYPES = "DIRECTORY_CONTAINS_MULTIPLE_TYPES"
    DOWNLOAD_FINISHED_FOR_FILE = "DOWNLOAD_FINISHED_FOR_FILE"
    DOWNLOAD_PROGRESS_OF_FILE = "DOWNLOAD_PROGRESS_OF_FILE"
    ERROR_EXECUTING_BATCH = "ERROR_EXECUTING_BATCH"
    NO_RECORDS_FOUND_FOR_TABLE = "NO_RECORDS_FOUND_FOR_TABLE"
    UNKNOWN_COLUMN_IN_FILTER = "UNKNOWN_COLUMN_IN_FILTER"
    INCOMPATIBLE_COMPARISON_IN_FILTER = "INCOMPATIBLE_COMPARISON_IN_FILTER"
    REMOVE_DUPLICATE_WITHOUT_PK = "REMOVE_DUPLICATE_WITHOUT_PK"
    SPECIAL_CHAR_IN_TABLE_NAME = "SPECIAL_CHAR_IN_TABLE_NAME"
    DUPLICATE_COLUMN_DETECTED = "DUPLICATE_COLUMN_DETECTED"


class JobResult(PythonCoreBaseEnum):
    SUCCESS = "SUCCESS"
    RUNNING = "RUNNING"
    FAILURE = "FAILURE"


class TableExtractionValidationType(PythonCoreBaseEnum):
    FATAL = "FATAL"
    WARNING = "WARNING"


class LogLevel(PythonCoreBaseEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataJobSkippedNotificationType(PythonCoreBaseEnum):
    ONLY_FIRST_TIME_AFTER_SKIPPED = "ONLY_FIRST_TIME_AFTER_SKIPPED"
    IN_ALL_CASES = "IN_ALL_CASES"


class DataJobSuccessfulNotificationType(PythonCoreBaseEnum):
    ONLY_FIRST_TIME_AFTER_FAILURE = "ONLY_FIRST_TIME_AFTER_FAILURE"
    IN_ALL_CASES = "IN_ALL_CASES"


class PoolColumnType(PythonCoreBaseEnum):
    STRING = "STRING"
    DATE = "DATE"
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"


class PropertyType(PythonCoreBaseEnum):
    TABLE = "TABLE"
    VIEW = "VIEW"


class LoadState(PythonCoreBaseEnum):
    LOADED = "LOADED"
    NOT_LOADED = "NOT_LOADED"


class AccessControlEntrySubjectType(PythonCoreBaseEnum):
    USER = "USER"
    GROUP = "GROUP"
    APPLICATION = "APPLICATION"


class ConnectorStatusStepResult(PythonCoreBaseEnum):
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class HybridPoolProviderType(PythonCoreBaseEnum):
    HDFS = "HDFS"
    MSSQL = "MSSQL"
    HANA = "HANA"


class ExecutionType(PythonCoreBaseEnum):
    SCHEDULE = "SCHEDULE"
    JOB = "JOB"
    TASK = "TASK"
    STEP = "STEP"


class ReplicationStatus(PythonCoreBaseEnum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    DEGRADED = "DEGRADED"
    ERROR_REPLICATING = "ERROR_REPLICATING"
    ERROR_INITIALIZING = "ERROR_INITIALIZING"


class ReplicationType(PythonCoreBaseEnum):
    SAP = "SAP"
    DATABASE = "DATABASE"
    SERVICENOW = "SERVICENOW"


class DataPoolProviderColumnType(PythonCoreBaseEnum):
    VARCHAR = "VARCHAR"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"
    DATETIME_ZONED = "DATETIME_ZONED"
    DATE = "DATE"
    TIME = "TIME"
    TIME_ZONED = "TIME_ZONED"
    BIGINT = "BIGINT"
    VARBINARY = "VARBINARY"
    UNMAPPED = "UNMAPPED"


class PoolProviderQueryType(PythonCoreBaseEnum):
    CREATE_TABLE = "CREATE_TABLE"
    SELECT_TABLE = "SELECT_TABLE"
    COPY_TABLE = "COPY_TABLE"


class SelectExpressionType(PythonCoreBaseEnum):
    SELECT_COLUMN = "SELECT_COLUMN"
    SELECT_AGGREGATE = "SELECT_AGGREGATE"


class DataQueryColumnType(PythonCoreBaseEnum):
    VARCHAR = "VARCHAR"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"
    DATE = "DATE"
    TIME = "TIME"
    BIGINT = "BIGINT"
    VARBINARY = "VARBINARY"
    UNMAPPED = "UNMAPPED"


class TransformationResourcePool(PythonCoreBaseEnum):
    LONG_RUNNING = "LONG_RUNNING"
    BULK = "BULK"


class DataModelEmailType(PythonCoreBaseEnum):
    DATA_MODEL_LOAD_SUCCESS_AFTER_FAILURE = "DATA_MODEL_LOAD_SUCCESS_AFTER_FAILURE"
    DATA_MODEL_LOAD_FAILED = "DATA_MODEL_LOAD_FAILED"


class CcmmTableType(PythonCoreBaseEnum):
    OBJECT = "OBJECT"
    EVENT = "EVENT"
    CHANGE = "CHANGE"


class TableType(PythonCoreBaseEnum):
    DEFAULT = "DEFAULT"
    ACTIVITY = "ACTIVITY"
    CASE = "CASE"


class AcceleratorSelectionKind(PythonCoreBaseEnum):
    SELECTION = "SELECTION"
    FILTER = "FILTER"


class AcceleratorSelectionType(PythonCoreBaseEnum):
    DATE = "DATE"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    THROUGHPUT = "THROUGHPUT"
    PROCESS = "PROCESS"
    REWORK = "REWORK"
    ERROR = "ERROR"
    GENERIC = "GENERIC"


class CloudTeamPrivacyType(PythonCoreBaseEnum):
    PUBLIC = "PUBLIC"
    PUBLIC_TO_DOMAIN = "PUBLIC_TO_DOMAIN"
    PRIVATE = "PRIVATE"


class DataConsumptionStage(PythonCoreBaseEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


class PermissionsManagementMode(PythonCoreBaseEnum):
    STANDARD = "STANDARD"
    RESTRICTED_TO_ADMINS = "RESTRICTED_TO_ADMINS"


class ChunkType(PythonCoreBaseEnum):
    UPSERT = "UPSERT"
    DELETE = "DELETE"


class DataLoadType(PythonCoreBaseEnum):
    FROM_CACHE = "FROM_CACHE"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class DataModelLoadStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    LOST_CONNECTION = "LOST_CONNECTION"
    CANCELED = "CANCELED"
    CANCELLING = "CANCELLING"


class StreamingExecutionType(PythonCoreBaseEnum):
    SUBSCRIPTION = "SUBSCRIPTION"
    TABLE = "TABLE"


class ColumnTypeOverrideSupport(PythonCoreBaseEnum):
    V1 = "V1"
    V2 = "V2"


class TableConfigurationParameterType(PythonCoreBaseEnum):
    NUMBER = "NUMBER"
    STRING = "STRING"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    BOOLEAN = "BOOLEAN"
    COLUMN_CHOICE = "COLUMN_CHOICE"
    SINGLE_COLUMN_SELECTION = "SINGLE_COLUMN_SELECTION"
    MULTIPLE_CHOICE_SELECTION = "MULTIPLE_CHOICE_SELECTION"


class ChangeLogTableStatus(PythonCoreBaseEnum):
    UNKNOWN = "UNKNOWN"
    NEITHER_INSTALLED = "NEITHER_INSTALLED"
    CHANGE_LOG = "CHANGE_LOG"
    CHANGE_LOG_AND_TRIGGER = "CHANGE_LOG_AND_TRIGGER"
    CHANGE_LOG_INVALID = "CHANGE_LOG_INVALID"


class DataPushDeleteStrategyOptions(PythonCoreBaseEnum):
    V1 = "V1"
    V2 = "V2"


class DataPushUpsertStrategyOptions(PythonCoreBaseEnum):
    V1 = "V1"


class ExtractionValidationTrigger(PythonCoreBaseEnum):
    VALIDATE_ALL_WHEN_EXTRACTION_CONFIGURATION_INITIALIZED = "VALIDATE_ALL_WHEN_EXTRACTION_CONFIGURATION_INITIALIZED"
    VALIDATE_ALL_WHEN_NEW_TABLE_ADDED = "VALIDATE_ALL_WHEN_NEW_TABLE_ADDED"
    VALIDATE_NEW_TABLE = "VALIDATE_NEW_TABLE"
    VALIDATE_TABLE_WHEN_TABLE_CONFIGURATION_INITIALIZED = "VALIDATE_TABLE_WHEN_TABLE_CONFIGURATION_INITIALIZED"
    VALIDATE_ALL_WHEN_EXTRACTION_CONFIGURATION_UPDATED = "VALIDATE_ALL_WHEN_EXTRACTION_CONFIGURATION_UPDATED"
    VALIDATE_UPDATED_TABLES = "VALIDATE_UPDATED_TABLES"


class DataModelTableLoadingStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    SKIP = "SKIP"


class LoadStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CANCELED = "CANCELED"


class ReplicationCockpitTableStatus(PythonCoreBaseEnum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    DEGRADED = "DEGRADED"
    ERROR_REPLICATING = "ERROR_REPLICATING"
    ERROR_INITIALIZING = "ERROR_INITIALIZING"


class DataPoolStatus(PythonCoreBaseEnum):
    CANCEL = "CANCEL"
    FAIL = "FAIL"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    UNCONFIGURED = "UNCONFIGURED"


class ConsumptionStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    DONE = "DONE"


class TransformationExecutionStatus(PythonCoreBaseEnum):
    NEW = "NEW"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    CANCEL = "CANCEL"
    FAIL = "FAIL"


class TransformationExecutionType(PythonCoreBaseEnum):
    EXECUTION_ITEM = "EXECUTION_ITEM"
    DATA_QUERY = "DATA_QUERY"


class DatabaseAuthenticationMethod(PythonCoreBaseEnum):
    USERNAME_PASSWORD = "USERNAME_PASSWORD"
    OAUTH = "OAUTH"
    ACTIVE_DIRECTORY = "ACTIVE_DIRECTORY"
    SERVICE_ACCOUNT_AUTHENTICATION = "SERVICE_ACCOUNT_AUTHENTICATION"
    APPLICATION_DEFAULT_CREDENTIALS = "APPLICATION_DEFAULT_CREDENTIALS"
    KEY_PAIR = "KEY_PAIR"
    PERSONAL_ACCESS_TOKEN = "PERSONAL_ACCESS_TOKEN"


class AutoCommit(PythonCoreBaseEnum):
    FALSE = "FALSE"
    SKIP = "SKIP"
    TRUE = "TRUE"


class BinaryHandlingOption(PythonCoreBaseEnum):
    UTF_8 = "UTF_8"
    HEX_NOTATION = "HEX_NOTATION"


class DatabaseMetadataSource(PythonCoreBaseEnum):
    DRIVER_METADATA = "DRIVER_METADATA"
    SAMPLE_QUERY = "SAMPLE_QUERY"
    INFORMATION_SCHEMA = "INFORMATION_SCHEMA"
    PG_CATALOG = "PG_CATALOG"


class LimitAndOffsetStatementSyntax(PythonCoreBaseEnum):
    LIMIT_WITHOUT_OFFSET = "LIMIT_WITHOUT_OFFSET"
    LIMIT_WITH_OFFSET = "LIMIT_WITH_OFFSET"
    TOP_WITHOUT_OFFSET = "TOP_WITHOUT_OFFSET"
    FETCH_FIRST_ROWS_ONLY_WITHOUT_OFFSET = "FETCH_FIRST_ROWS_ONLY_WITHOUT_OFFSET"
    FETCH_FIRST_ROWS_ONLY_WITHOUT_OFFSET_AND_WITH_ORDER = "FETCH_FIRST_ROWS_ONLY_WITHOUT_OFFSET_AND_WITH_ORDER"
    LIMIT_WITH_OFFSET_AND_ORDER = "LIMIT_WITH_OFFSET_AND_ORDER"


class DocExpansion(PythonCoreBaseEnum):
    NONE = "none"
    LIST = "list"
    FULL = "full"


class ModelRendering(PythonCoreBaseEnum):
    EXAMPLE = "example"
    MODEL = "model"


class OperationsSorter(PythonCoreBaseEnum):
    ALPHA = "alpha"
    METHOD = "method"


class TagsSorter(PythonCoreBaseEnum):
    ALPHA = "alpha"


class ExceptionReference(PythonCoreBaseModel):
    reference: Optional["str"] = Field(None, alias="reference")
    message: Optional["str"] = Field(None, alias="message")
    short_message: Optional["str"] = Field(None, alias="shortMessage")


class FrontendHandledBackendError(PythonCoreBaseModel):
    frontend_error_key: Optional["str"] = Field(None, alias="frontendErrorKey")
    error_information: Optional["Any"] = Field(None, alias="errorInformation")


class PoolVariableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    name: Optional["str"] = Field(None, alias="name")
    placeholder: Optional["str"] = Field(None, alias="placeholder")
    description: Optional["str"] = Field(None, alias="description")
    type_: Optional["VariableType"] = Field(None, alias="type")
    dynamic_variable_op_type: Optional["DynamicVariableOpType"] = Field(None, alias="dynamicVariableOpType")
    data_type: Optional["FilterParserDataType"] = Field(None, alias="dataType")
    dynamic_table: Optional["str"] = Field(None, alias="dynamicTable")
    dynamic_column: Optional["str"] = Field(None, alias="dynamicColumn")
    dynamic_data_source_id: Optional["str"] = Field(None, alias="dynamicDataSourceId")
    default_values: Optional["List[Optional[VariableValueTransport]]"] = Field(None, alias="defaultValues")
    default_settings: Optional["VariableSettingsTransport"] = Field(None, alias="defaultSettings")
    values: Optional["List[Optional[VariableValueTransport]]"] = Field(None, alias="values")
    settings: Optional["VariableSettingsTransport"] = Field(None, alias="settings")


class VariableSettingsTransport(PythonCoreBaseModel):
    pool_variable_id: Optional["str"] = Field(None, alias="poolVariableId")


class VariableValueTransport(PythonCoreBaseModel):
    value: Optional["str"] = Field(None, alias="value")
    task_instance_id: Optional["str"] = Field(None, alias="taskInstanceId")


class TaskTemplateTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    number_of_instances: Optional["int"] = Field(None, alias="numberOfInstances")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")


class TaskVariableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    name: Optional["str"] = Field(None, alias="name")
    placeholder: Optional["str"] = Field(None, alias="placeholder")
    description: Optional["str"] = Field(None, alias="description")
    type_: Optional["VariableType"] = Field(None, alias="type")
    dynamic_variable_op_type: Optional["DynamicVariableOpType"] = Field(None, alias="dynamicVariableOpType")
    data_type: Optional["FilterParserDataType"] = Field(None, alias="dataType")
    dynamic_table: Optional["str"] = Field(None, alias="dynamicTable")
    dynamic_column: Optional["str"] = Field(None, alias="dynamicColumn")
    dynamic_data_source_id: Optional["str"] = Field(None, alias="dynamicDataSourceId")
    parameter_type: Optional["ParameterType"] = Field(None, alias="parameterType")
    default_values: Optional["List[Optional[VariableValueTransport]]"] = Field(None, alias="defaultValues")
    default_settings: Optional["VariableSettingsTransport"] = Field(None, alias="defaultSettings")
    values: Optional["List[Optional[VariableValueTransport]]"] = Field(None, alias="values")
    settings: Optional["VariableSettingsTransport"] = Field(None, alias="settings")


class StreamingColumnTransport(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    anonymized: Optional["bool"] = Field(None, alias="anonymized")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    preferred_type: Optional["str"] = Field(None, alias="preferredType")
    date_format: Optional["str"] = Field(None, alias="dateFormat")


class StreamingTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    type_: Optional["StreamingType"] = Field(None, alias="type")
    columns: Optional["List[Optional[StreamingColumnTransport]]"] = Field(None, alias="columns")
    use_push_api: Optional["bool"] = Field(None, alias="usePushApi")


class SchedulingTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    enabled: Optional["bool"] = Field(None, alias="enabled")
    monitored: Optional["bool"] = Field(None, alias="monitored")
    mode: Optional["ExtractionMode"] = Field(None, alias="mode")
    execution_pattern: Optional["ExecutionPattern"] = Field(None, alias="executionPattern")
    frequency: Optional["str"] = Field(None, alias="frequency")
    minute: Optional["int"] = Field(None, alias="minute")
    every_x_hours: Optional["int"] = Field(None, alias="everyXHours")
    time: Optional["str"] = Field(None, alias="time")
    day: Optional["int"] = Field(None, alias="day")
    week_days_list: Optional["List[Optional[int]]"] = Field(None, alias="weekDaysList")
    month_pattern: Optional["MonthPattern"] = Field(None, alias="monthPattern")
    custom_cron: Optional["str"] = Field(None, alias="customCron")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    next_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="nextExecutionDate")
    number_of_jobs: Optional["int"] = Field(None, alias="numberOfJobs")
    reload_all_data_models_after_execution: Optional["bool"] = Field(None, alias="reloadAllDataModelsAfterExecution")
    type_: Optional["SchedulingType"] = Field(None, alias="type")
    user_creator_id: Optional["str"] = Field(None, alias="userCreatorId")
    user_creator_name: Optional["str"] = Field(None, alias="userCreatorName")
    last_execution_status: Optional["ExecutionStatus"] = Field(None, alias="lastExecutionStatus")


class DataPoolSchedulingOverviewFilterTransport(PythonCoreBaseModel):
    schedule_id: Optional["str"] = Field(None, alias="scheduleId")
    schedule_status: Optional["ExecutionStatus"] = Field(None, alias="scheduleStatus")
    offset_execution_milliseconds: Optional["int"] = Field(None, alias="offsetExecutionMilliseconds")


class DataPoolSchedulingOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    aggregated_execution_status: Optional["ExecutionStatus"] = Field(None, alias="aggregatedExecutionStatus")
    schedulings: Optional["List[Optional[SchedulingIdAndNameTransport]]"] = Field(None, alias="schedulings")


class SchedulingIdAndNameTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")


class TransformationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    job_id: Optional["str"] = Field(None, alias="jobId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    task_created_at: Optional["PythonCoreDatetime"] = Field(None, alias="taskCreatedAt")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    published: Optional["bool"] = Field(None, alias="published")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    legal_agreement_accepted: Optional["bool"] = Field(None, alias="legalAgreementAccepted")
    statement: Optional["str"] = Field(None, alias="statement")


class TaskUpdate(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")


class TaskInstanceTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    job_id: Optional["str"] = Field(None, alias="jobId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    task_created_at: Optional["PythonCoreDatetime"] = Field(None, alias="taskCreatedAt")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    published: Optional["bool"] = Field(None, alias="published")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    legal_agreement_accepted: Optional["bool"] = Field(None, alias="legalAgreementAccepted")


class DataModelExecutionTableItem(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    alias_or_name: Optional["str"] = Field(None, alias="aliasOrName")
    selected: Optional["bool"] = Field(None, alias="selected")


class DataModelExecutionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    data_model_name: Optional["str"] = Field(None, alias="dataModelName")
    tables: Optional["List[Optional[DataModelExecutionTableItem]]"] = Field(None, alias="tables")
    partial_load: Optional["bool"] = Field(None, alias="partialLoad")


class CalculatedColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    expression: Optional["str"] = Field(None, alias="expression")


class TableConfigurationParameterValue(PythonCoreBaseModel):
    key: Optional["TableConfigurationParameterKey"] = Field(None, alias="key")
    value: Optional["Any"] = Field(None, alias="value")


class TableExtractionColumnTransport(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    from_join: Optional["bool"] = Field(None, alias="fromJoin")
    anonymized: Optional["bool"] = Field(None, alias="anonymized")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    preferred_type: Optional["str"] = Field(None, alias="preferredType")
    date_format: Optional["str"] = Field(None, alias="dateFormat")


class TableExtractionJoinTransport(PythonCoreBaseModel):
    parent_schema: Optional["str"] = Field(None, alias="parentSchema")
    parent_table: Optional["str"] = Field(None, alias="parentTable")
    child_table: Optional["str"] = Field(None, alias="childTable")
    use_primary_keys: Optional["bool"] = Field(None, alias="usePrimaryKeys")
    custom_join_path: Optional["str"] = Field(None, alias="customJoinPath")
    join_filter: Optional["str"] = Field(None, alias="joinFilter")
    order: Optional["int"] = Field(None, alias="order")


class TableExtractionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    task_id: Optional["str"] = Field(None, alias="taskId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    table_execution_item_id: Optional["str"] = Field(None, alias="tableExecutionItemId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    rename_target_table: Optional["bool"] = Field(None, alias="renameTargetTable")
    target_table_name: Optional["str"] = Field(None, alias="targetTableName")
    columns: Optional["List[Optional[TableExtractionColumnTransport]]"] = Field(None, alias="columns")
    joins: Optional["List[Optional[TableExtractionJoinTransport]]"] = Field(None, alias="joins")
    dependent_tables: Optional["List[Optional[TableExtractionTransport]]"] = Field(None, alias="dependentTables")
    use_manual_p_ks: Optional["bool"] = Field(None, alias="useManualPKs")
    filter_definition: Optional["str"] = Field(None, alias="filterDefinition")
    delta_filter_definition: Optional["str"] = Field(None, alias="deltaFilterDefinition")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    creation_date_column: Optional["str"] = Field(None, alias="creationDateColumn")
    creation_date_value_start: Optional["str"] = Field(None, alias="creationDateValueStart")
    creation_date_value_end: Optional["str"] = Field(None, alias="creationDateValueEnd")
    creation_date_parameter_start: Optional["str"] = Field(None, alias="creationDateParameterStart")
    creation_date_parameter_end: Optional["str"] = Field(None, alias="creationDateParameterEnd")
    creation_date_value_today: Optional["bool"] = Field(None, alias="creationDateValueToday")
    change_date_column: Optional["str"] = Field(None, alias="changeDateColumn")
    change_date_offset: Optional["int"] = Field(None, alias="changeDateOffset")
    change_date_offset_type: Optional["ChangeDateOffsetType"] = Field(None, alias="changeDateOffsetType")
    table_extraction_type: Optional["TableExtractionType"] = Field(None, alias="tableExtractionType")
    parent_table: Optional["str"] = Field(None, alias="parentTable")
    depends_on: Optional["str"] = Field(None, alias="dependsOn")
    column_value_table: Optional["str"] = Field(None, alias="columnValueTable")
    column_value_column: Optional["str"] = Field(None, alias="columnValueColumn")
    column_value_target_column: Optional["str"] = Field(None, alias="columnValueTargetColumn")
    column_values_at_a_time: Optional["int"] = Field(None, alias="columnValuesAtATime")
    join_type: Optional["JoinType"] = Field(None, alias="joinType")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    connector_specific_configuration: Optional["List[Optional[TableConfigurationParameterValue]]"] = Field(
        None, alias="connectorSpecificConfiguration"
    )
    calculated_columns: Optional["List[Optional[CalculatedColumnTransport]]"] = Field(None, alias="calculatedColumns")
    end_date_disabled: Optional["bool"] = Field(None, alias="endDateDisabled")
    disable_change_log: Optional["bool"] = Field(None, alias="disableChangeLog")
    data_push_delete_strategy: Optional["DataPushDeleteStrategy"] = Field(None, alias="dataPushDeleteStrategy")
    customize_column_selection: Optional["bool"] = Field(None, alias="customizeColumnSelection")
    mirror_table_names: Optional["List[Optional[str]]"] = Field(None, alias="mirrorTableNames")
    selected_columns: Optional["List[Optional[str]]"] = Field(None, alias="selectedColumns")
    parent: Optional["bool"] = Field(None, alias="parent")


class ColumnTransport(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    column_type: Optional["ColumnType"] = Field(None, alias="columnType")
    field_length: Optional["int"] = Field(None, alias="fieldLength")
    decimals: Optional["int"] = Field(None, alias="decimals")
    pk_field: Optional["bool"] = Field(None, alias="pkField")


class ExtractionConfigurationValueTransport(PythonCoreBaseModel):
    data_push_upsert_strategy: Optional["DataPushUpsertStrategy"] = Field(None, alias="dataPushUpsertStrategy")
    debug_mode: Optional["bool"] = Field(None, alias="debugMode")
    delete_job: Optional["bool"] = Field(None, alias="deleteJob")
    connector_specific_configuration: Optional["List[Optional[TableConfigurationParameterValue]]"] = Field(
        None, alias="connectorSpecificConfiguration"
    )
    ignore_metadata_changes: Optional["bool"] = Field(None, alias="ignoreMetadataChanges")


class ExtractionWithTablesTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    job_id: Optional["str"] = Field(None, alias="jobId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    task_created_at: Optional["PythonCoreDatetime"] = Field(None, alias="taskCreatedAt")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    published: Optional["bool"] = Field(None, alias="published")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    legal_agreement_accepted: Optional["bool"] = Field(None, alias="legalAgreementAccepted")
    extraction_configuration_value_transport: Optional["ExtractionConfigurationValueTransport"] = Field(
        None, alias="extractionConfigurationValueTransport"
    )
    tables: Optional["List[Optional[TableExtractionTransport]]"] = Field(None, alias="tables")
    metadata_tables: Optional["List[Optional[TableTransport]]"] = Field(None, alias="metadataTables")
    extraction_configuration: Optional["ExtractionConfigurationValueTransport"] = Field(
        None, alias="extractionConfiguration"
    )


class TableTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    columns: Optional["List[Optional[ColumnTransport]]"] = Field(None, alias="columns")


class JobTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    time_stamp: Optional["PythonCoreDatetime"] = Field(None, alias="timeStamp")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    current_execution_id: Optional["str"] = Field(None, alias="currentExecutionId")
    dag_based_execution_enabled: Optional["bool"] = Field(None, alias="dagBasedExecutionEnabled")
    latest_execution_item_id: Optional["str"] = Field(None, alias="latestExecutionItemId")


class DataPoolDataJobOverviewFilterTransport(PythonCoreBaseModel):
    data_source_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataSourceIds")
    data_model_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataModelIds")
    scheduling_ids: Optional["List[Optional[str]]"] = Field(None, alias="schedulingIds")
    execution_status: Optional["ExecutionStatus"] = Field(None, alias="executionStatus")
    data_job_id: Optional["str"] = Field(None, alias="dataJobId")
    offset_execution_milliseconds: Optional["int"] = Field(None, alias="offsetExecutionMilliseconds")


class DataJobIdAndNameTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class DataPoolDataJobOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_jobs: Optional["List[Optional[DataJobIdAndNameTransport]]"] = Field(None, alias="dataJobs")
    count_data_model_loads: Optional["int"] = Field(None, alias="countDataModelLoads")
    count_extractions: Optional["int"] = Field(None, alias="countExtractions")
    count_transformations: Optional["int"] = Field(None, alias="countTransformations")


class JobSchedulingTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    schedule_id: Optional["str"] = Field(None, alias="scheduleId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    job_name: Optional["str"] = Field(None, alias="jobName")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")


class FileDataTable(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    file_name: Optional["str"] = Field(None, alias="fileName")
    type_: Optional["FileDataTableType"] = Field(None, alias="type")
    original_file_name: Optional["str"] = Field(None, alias="originalFileName")
    last_updated: Optional["PythonCoreDatetime"] = Field(None, alias="lastUpdated")
    has_header: Optional["bool"] = Field(None, alias="hasHeader")
    processing_start_date: Optional["PythonCoreDatetime"] = Field(None, alias="processingStartDate")
    processing_end_date: Optional["PythonCoreDatetime"] = Field(None, alias="processingEndDate")
    has_column_type_error: Optional["bool"] = Field(None, alias="hasColumnTypeError")
    processing_error: Optional["str"] = Field(None, alias="processingError")
    display_error: Optional["str"] = Field(None, alias="displayError")
    processing_files_deleted: Optional["bool"] = Field(None, alias="processingFilesDeleted")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    sheet_name: Optional["str"] = Field(None, alias="sheetName")
    escape_sequence: Optional["str"] = Field(None, alias="escapeSequence")
    quote_sequence: Optional["str"] = Field(None, alias="quoteSequence")
    separator_sequence: Optional["str"] = Field(None, alias="separatorSequence")
    line_ending: Optional["str"] = Field(None, alias="lineEnding")
    char_set: Optional["str"] = Field(None, alias="charSet")
    decimal_separator: Optional["str"] = Field(None, alias="decimalSeparator")
    thousand_separator: Optional["str"] = Field(None, alias="thousandSeparator")
    normalized_newline: Optional["str"] = Field(None, alias="normalizedNewline")
    password_required: Optional["bool"] = Field(None, alias="passwordRequired")
    execution_canceled: Optional["bool"] = Field(None, alias="executionCanceled")
    sanitized_original_file_name: Optional["str"] = Field(None, alias="sanitizedOriginalFileName")
    sanitized_sheet_name: Optional["str"] = Field(None, alias="sanitizedSheetName")
    processing: Optional["bool"] = Field(None, alias="processing")
    target_table_name: Optional["str"] = Field(None, alias="targetTableName")
    processed: Optional["bool"] = Field(None, alias="processed")
    name: Optional["str"] = Field(None, alias="name")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class FileDataColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    string_length: Optional["int"] = Field(None, alias="stringLength")
    file_data_table_id: Optional["str"] = Field(None, alias="fileDataTableId")
    index: Optional["int"] = Field(None, alias="index")
    sanitized_name: Optional["str"] = Field(None, alias="sanitizedName")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class CustomExtractorAuthenticationConfiguration(PythonCoreBaseModel):
    api_key_header: Optional["str"] = Field(None, alias="apiKeyHeader")
    authentication_method: Optional["CustomExtractorAuthenticationMethod"] = Field(None, alias="authenticationMethod")
    authorize_endpoint: Optional["str"] = Field(None, alias="authorizeEndpoint")
    token_endpoint: Optional["str"] = Field(None, alias="tokenEndpoint")
    grant_type: Optional["str"] = Field(None, alias="grantType")
    scopes: Optional["str"] = Field(None, alias="scopes")
    content_type: Optional["str"] = Field(None, alias="contentType")
    allow_using_celonis_client_and_secret: Optional["bool"] = Field(None, alias="allowUsingCelonisClientAndSecret")
    assertion_label: Optional["str"] = Field(None, alias="assertionLabel")
    audience_label: Optional["str"] = Field(None, alias="audienceLabel")
    audience_label_required: Optional["bool"] = Field(None, alias="audienceLabelRequired")
    subject_label: Optional["str"] = Field(None, alias="subjectLabel")
    subject_label_required: Optional["bool"] = Field(None, alias="subjectLabelRequired")
    issuer_label: Optional["str"] = Field(None, alias="issuerLabel")
    issuer_label_required: Optional["bool"] = Field(None, alias="issuerLabelRequired")
    default_audience: Optional["str"] = Field(None, alias="defaultAudience")
    enable_custom_jwt_headers: Optional["bool"] = Field(None, alias="enableCustomJwtHeaders")
    custom_jwt_headers: Optional["List[Optional[CustomFieldParameter]]"] = Field(None, alias="customJwtHeaders")
    enable_custom_jwt_claims: Optional["bool"] = Field(None, alias="enableCustomJwtClaims")
    custom_jwt_claims: Optional["List[Optional[CustomFieldParameter]]"] = Field(None, alias="customJwtClaims")
    signature_algorithm: Optional["JwtSignatureAlgorithm"] = Field(None, alias="signatureAlgorithm")
    use_body_for_o_auth: Optional["bool"] = Field(None, alias="useBodyForOAuth")
    enable_custom_field: Optional["bool"] = Field(None, alias="enableCustomField")
    custom_fields: Optional["List[Optional[CustomFieldParameter]]"] = Field(None, alias="customFields")


class CustomExtractorColumn(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    path: Optional["List[Optional[str]]"] = Field(None, alias="path")
    type_: Optional["CustomExtractorColumnType"] = Field(None, alias="type")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    foreign_key: Optional["bool"] = Field(None, alias="foreignKey")
    type_overwritten: Optional["bool"] = Field(None, alias="typeOverwritten")
    date_format: Optional["str"] = Field(None, alias="dateFormat")


class CustomExtractorConfiguration(PythonCoreBaseModel):
    supported_authentication_configurations: Optional[
        "List[Optional[CustomExtractorAuthenticationConfiguration]]"
    ] = Field(None, alias="supportedAuthenticationConfigurations")
    connection_parameters: Optional["List[Optional[CustomExtractorConnectionParameter]]"] = Field(
        None, alias="connectionParameters"
    )
    supported_filtering_syntaxes: Optional["List[Optional[CustomExtractorFilteringSyntax]]"] = Field(
        None, alias="supportedFilteringSyntaxes"
    )
    endpoints: Optional["List[Optional[CustomExtractorEndpoint]]"] = Field(None, alias="endpoints")
    supported_authentication_methods: Optional["List[Optional[CustomExtractorAuthenticationMethod]]"] = Field(
        None, alias="supportedAuthenticationMethods"
    )


class CustomExtractorConnectionParameter(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    placeholder: Optional["str"] = Field(None, alias="placeholder")
    default_value: Optional["str"] = Field(None, alias="defaultValue")
    confidential: Optional["bool"] = Field(None, alias="confidential")
    mandatory: Optional["bool"] = Field(None, alias="mandatory")


class CustomExtractorEndpoint(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    depends_on: Optional["str"] = Field(None, alias="dependsOn")
    depends_on_column: Optional["str"] = Field(None, alias="dependsOnColumn")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["CustomExtractorApiType"] = Field(None, alias="type")
    url: Optional["str"] = Field(None, alias="url")
    request_parameters: Optional["List[Optional[CustomExtractorRequestParameter]]"] = Field(
        None, alias="requestParameters"
    )
    headers: Optional["Dict[str, Optional[str]]"] = Field(None, alias="headers")
    pagination: Optional["CustomExtractorPagination"] = Field(None, alias="pagination")
    response: Optional["CustomExtractorEndpointResponse"] = Field(None, alias="response")
    error_handling_rules: Optional["List[Optional[CustomExtractorErrorHandlingRule]]"] = Field(
        None, alias="errorHandlingRules"
    )
    use_for_connection_test: Optional["bool"] = Field(None, alias="useForConnectionTest")
    is_deactivated: Optional["bool"] = Field(None, alias="isDeactivated")


class CustomExtractorEndpointResponse(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    definition_input: Optional["str"] = Field(None, alias="definitionInput")
    response_root: Optional["List[Optional[str]]"] = Field(None, alias="responseRoot")
    response_type: Optional["CustomExtractorResponseType"] = Field(None, alias="responseType")
    columns: Optional["List[Optional[CustomExtractorColumn]]"] = Field(None, alias="columns")
    nested_tables: Optional["List[Optional[CustomExtractorNestedTable]]"] = Field(None, alias="nestedTables")


class CustomExtractorErrorHandlingRule(PythonCoreBaseModel):
    option: Optional["CustomExtractorErrorHandlingOption"] = Field(None, alias="option")
    operator: Optional["CustomExtractorErrorHandlingOperator"] = Field(None, alias="operator")
    value: Optional["str"] = Field(None, alias="value")
    json_field_in_response: Optional["str"] = Field(None, alias="jsonFieldInResponse")


class CustomExtractorFilteringSyntax(PythonCoreBaseModel):
    type_code: Optional["str"] = Field(None, alias="typeCode")
    display_name: Optional["str"] = Field(None, alias="displayName")
    available_parameters_in_syntax: Optional["List[Optional[str]]"] = Field(None, alias="availableParametersInSyntax")


class CustomExtractorNestedTable(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    path: Optional["List[Optional[str]]"] = Field(None, alias="path")
    columns: Optional["List[Optional[CustomExtractorColumn]]"] = Field(None, alias="columns")
    primitive_array: Optional["bool"] = Field(None, alias="primitiveArray")


class CustomExtractorPagination(PythonCoreBaseModel):
    pagination_method: Optional["CustomExtractorPaginationMethod"] = Field(None, alias="paginationMethod")
    pagination_data: Optional["CustomExtractorPaginationData"] = Field(None, alias="paginationData")


class CustomExtractorPaginationData(PythonCoreBaseModel):
    page_parameter: Optional["str"] = Field(None, alias="pageParameter")
    page_size: Optional["str"] = Field(None, alias="pageSize")
    default_page_size: Optional["int"] = Field(None, alias="defaultPageSize")
    default_first_page_index: Optional["int"] = Field(None, alias="defaultFirstPageIndex")
    total_pages_field: Optional["List[Optional[str]]"] = Field(None, alias="totalPagesField")
    limit: Optional["str"] = Field(None, alias="limit")
    offset: Optional["str"] = Field(None, alias="offset")
    default_limit: Optional["int"] = Field(None, alias="defaultLimit")
    total_size_field: Optional["List[Optional[str]]"] = Field(None, alias="totalSizeField")
    next_token_parameter: Optional["str"] = Field(None, alias="nextTokenParameter")
    next_token_path: Optional["List[Optional[str]]"] = Field(None, alias="nextTokenPath")
    next_url_path: Optional["List[Optional[str]]"] = Field(None, alias="nextUrlPath")
    upper_boundary_parameter: Optional["str"] = Field(None, alias="upperBoundaryParameter")
    lower_boundary_parameter: Optional["str"] = Field(None, alias="lowerBoundaryParameter")
    parameter_type: Optional["CustomExtractorColumnType"] = Field(None, alias="parameterType")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    increment_amount: Optional["int"] = Field(None, alias="incrementAmount")


class CustomExtractorRequestParameter(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    use_as_filter: Optional["bool"] = Field(None, alias="useAsFilter")
    value: Optional["str"] = Field(None, alias="value")
    filter_type: Optional["str"] = Field(None, alias="filterType")
    date_format: Optional["str"] = Field(None, alias="dateFormat")


class CustomExtractorTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    description: Optional["str"] = Field(None, alias="description")
    customized_from: Optional["str"] = Field(None, alias="customizedFrom")
    configuration: Optional["CustomExtractorConfiguration"] = Field(None, alias="configuration")


class CustomFieldParameter(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    value: Optional["str"] = Field(None, alias="value")


class CustomExtractorAuthenticationTransport(PythonCoreBaseModel):
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    authentication_configurations: Optional["List[Optional[CustomExtractorAuthenticationConfiguration]]"] = Field(
        None, alias="authenticationConfigurations"
    )


class DataTransferExportCreateEditTransport(PythonCoreBaseModel):
    data_transfer_export_id: Optional["str"] = Field(None, alias="dataTransferExportId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_transfer_export_type: Optional["DataTransferExportType"] = Field(None, alias="dataTransferExportType")
    selected_data_pool_ids: Optional["List[Optional[str]]"] = Field(None, alias="selectedDataPoolIds")
    export_subset: Optional["bool"] = Field(None, alias="exportSubset")
    data_transfer_export_tables: Optional["List[Optional[DataTransferExportTableTransport]]"] = Field(
        None, alias="dataTransferExportTables"
    )


class DataTransferExportTableTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")


class DataTransferExportSlimTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    data_transfer_export_type: Optional["DataTransferExportType"] = Field(None, alias="dataTransferExportType")
    nb_of_allowed_data_pools: Optional["int"] = Field(None, alias="nbOfAllowedDataPools")
    nb_of_importing_data_pools: Optional["int"] = Field(None, alias="nbOfImportingDataPools")
    nb_of_exported_tables: Optional["int"] = Field(None, alias="nbOfExportedTables")
    export_subset: Optional["bool"] = Field(None, alias="exportSubset")


class DataPoolDataSourceOverviewFilterTransport(PythonCoreBaseModel):
    data_source_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataSourceIds")
    reachable_and_valid_option: Optional["ReachableAndValidOption"] = Field(None, alias="reachableAndValidOption")


class DataPoolDataSourceOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_sources: Optional["List[Optional[DataSourceOverviewTransport]]"] = Field(None, alias="dataSources")
    aggregated_reachable_and_valid_status: Optional["bool"] = Field(None, alias="aggregatedReachableAndValidStatus")


class DataSourceOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["str"] = Field(None, alias="type")
    source_data_source_type: Optional["str"] = Field(None, alias="sourceDataSourceType")
    source_data_source_reachable_and_valid: Optional["bool"] = Field(None, alias="sourceDataSourceReachableAndValid")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    supports_realtime: Optional["bool"] = Field(None, alias="supportsRealtime")


class DataModelColumnTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")


class DataModelConfigurationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    activity_table_id: Optional["str"] = Field(None, alias="activityTableId")
    case_table_id: Optional["str"] = Field(None, alias="caseTableId")
    default_configuration: Optional["bool"] = Field(None, alias="defaultConfiguration")
    case_id_column: Optional["str"] = Field(None, alias="caseIdColumn")
    activity_column: Optional["str"] = Field(None, alias="activityColumn")
    timestamp_column: Optional["str"] = Field(None, alias="timestampColumn")
    sorting_column: Optional["str"] = Field(None, alias="sortingColumn")
    end_timestamp_column: Optional["str"] = Field(None, alias="endTimestampColumn")
    cost_column: Optional["str"] = Field(None, alias="costColumn")
    user_column: Optional["str"] = Field(None, alias="userColumn")
    use_parallel_process: Optional["bool"] = Field(None, alias="useParallelProcess")
    parallel_process_parent_column: Optional["str"] = Field(None, alias="parallelProcessParentColumn")
    parallel_process_child_column: Optional["str"] = Field(None, alias="parallelProcessChildColumn")


class DataModelCustomCalendarEntryTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    day: Optional["CalendarDay"] = Field(None, alias="day")
    working_day: Optional["bool"] = Field(None, alias="workingDay")
    start_time: Optional["int"] = Field(None, alias="startTime")
    end_time: Optional["int"] = Field(None, alias="endTime")


class DataModelCustomCalendarTransport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    entries: Optional["List[Optional[DataModelCustomCalendarEntryTransport]]"] = Field(None, alias="entries")


class DataModelFactoryCalendarTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")


class DataModelForeignKeyColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    source_column_name: Optional["str"] = Field(None, alias="sourceColumnName")
    target_column_name: Optional["str"] = Field(None, alias="targetColumnName")


class DataModelForeignKeyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    source_table_id: Optional["str"] = Field(None, alias="sourceTableId")
    target_table_id: Optional["str"] = Field(None, alias="targetTableId")
    columns: Optional["List[Optional[DataModelForeignKeyColumnTransport]]"] = Field(None, alias="columns")


class DataModelTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    alias: Optional["str"] = Field(None, alias="alias")
    columns: Optional["List[Optional[DataModelColumnTransport]]"] = Field(None, alias="columns")
    use_direct_storage: Optional["bool"] = Field(None, alias="useDirectStorage")
    primary_keys: Optional["List[Optional[str]]"] = Field(None, alias="primaryKeys")
    alias_or_name: Optional["str"] = Field(None, alias="aliasOrName")


class DataModelTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    create_date: Optional["PythonCoreDatetime"] = Field(None, alias="createDate")
    changed_date: Optional["PythonCoreDatetime"] = Field(None, alias="changedDate")
    configuration_skipped: Optional["bool"] = Field(None, alias="configurationSkipped")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    unavailable: Optional["bool"] = Field(None, alias="unavailable")
    editable: Optional["bool"] = Field(None, alias="editable")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    tables: Optional["List[Optional[DataModelTableTransport]]"] = Field(None, alias="tables")
    foreign_keys: Optional["List[Optional[DataModelForeignKeyTransport]]"] = Field(None, alias="foreignKeys")
    process_configurations: Optional["List[Optional[DataModelConfigurationTransport]]"] = Field(
        None, alias="processConfigurations"
    )
    data_model_calendar_type: Optional["DataModelCalendarType"] = Field(None, alias="dataModelCalendarType")
    factory_calendar: Optional["DataModelFactoryCalendarTransport"] = Field(None, alias="factoryCalendar")
    custom_calendar: Optional["DataModelCustomCalendarTransport"] = Field(None, alias="customCalendar")
    original_id: Optional["str"] = Field(None, alias="originalId")
    eventlog_automerge_enabled: Optional["bool"] = Field(None, alias="eventlogAutomergeEnabled")
    auto_merge_execution_mode: Optional["AutoMergeExecutionMode"] = Field(None, alias="autoMergeExecutionMode")
    linearization_enabled: Optional["bool"] = Field(None, alias="linearizationEnabled")
    event_log_count: Optional["int"] = Field(None, alias="eventLogCount")
    object_id: Optional["str"] = Field(None, alias="objectId")


class DataModelSignalLinkColumnNameTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_signal_link_column_id: Optional["str"] = Field(None, alias="dataModelSignalLinkColumnId")
    column_name: Optional["str"] = Field(None, alias="columnName")


class DataModelSignalLinkColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_signal_link_id: Optional["str"] = Field(None, alias="dataModelSignalLinkId")
    data_model_signal_link_mapping_id: Optional["str"] = Field(None, alias="dataModelSignalLinkMappingId")
    table_id: Optional["str"] = Field(None, alias="tableId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    type_: Optional["DataModelSignalLinkColumnDirection"] = Field(None, alias="type")
    priority: Optional["int"] = Field(None, alias="priority")
    column_name: Optional["str"] = Field(None, alias="columnName")
    column_names: Optional["List[Optional[DataModelSignalLinkColumnNameTransport]]"] = Field(None, alias="columnNames")


class DataModelSignalLinkMappingColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_signal_link_mapping_id: Optional["str"] = Field(None, alias="dataModelSignalLinkMappingId")
    type_: Optional["DataModelSignalLinkColumnDirection"] = Field(None, alias="type")
    column_name: Optional["str"] = Field(None, alias="columnName")


class DataModelSignalLinkMappingTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_signal_link_id: Optional["str"] = Field(None, alias="dataModelSignalLinkId")
    mapping_table: Optional["str"] = Field(None, alias="mappingTable")
    out_columns: Optional["List[Optional[DataModelSignalLinkMappingColumnTransport]]"] = Field(None, alias="outColumns")
    in_columns: Optional["List[Optional[DataModelSignalLinkMappingColumnTransport]]"] = Field(None, alias="inColumns")
    connections: Optional["List[Optional[DataModelSignalLinkColumnTransport]]"] = Field(None, alias="connections")


class DataModelSignalLinkTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    outgoing_columns: Optional["List[Optional[DataModelSignalLinkColumnTransport]]"] = Field(
        None, alias="outgoingColumns"
    )
    incoming_columns: Optional["List[Optional[DataModelSignalLinkColumnTransport]]"] = Field(
        None, alias="incomingColumns"
    )
    mapping_description: Optional["DataModelSignalLinkMappingTransport"] = Field(None, alias="mappingDescription")


class DataModelConfiguration(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    activity_table_id: Optional["str"] = Field(None, alias="activityTableId")
    case_table_id: Optional["str"] = Field(None, alias="caseTableId")
    default_configuration: Optional["bool"] = Field(None, alias="defaultConfiguration")
    case_id_column: Optional["str"] = Field(None, alias="caseIdColumn")
    activity_column: Optional["str"] = Field(None, alias="activityColumn")
    timestamp_column: Optional["str"] = Field(None, alias="timestampColumn")
    sorting_column: Optional["str"] = Field(None, alias="sortingColumn")
    end_timestamp_column: Optional["str"] = Field(None, alias="endTimestampColumn")
    cost_column: Optional["str"] = Field(None, alias="costColumn")
    user_column: Optional["str"] = Field(None, alias="userColumn")
    use_parallel_process: Optional["bool"] = Field(None, alias="useParallelProcess")
    parallel_process_parent_column: Optional["str"] = Field(None, alias="parallelProcessParentColumn")
    parallel_process_child_column: Optional["str"] = Field(None, alias="parallelProcessChildColumn")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class ParallelProcessConfiguration(PythonCoreBaseModel):
    use_parallel_process: Optional["bool"] = Field(None, alias="useParallelProcess")
    parallel_process_parent_column: Optional["str"] = Field(None, alias="parallelProcessParentColumn")
    parallel_process_child_column: Optional["str"] = Field(None, alias="parallelProcessChildColumn")


class DataModelGraphPositioningTransport(PythonCoreBaseModel):
    editing_mode: Optional["int"] = Field(None, alias="editingMode")
    table_positions: Optional["List[Optional[DataModelTablePosition]]"] = Field(None, alias="tablePositions")


class DataModelTablePosition(PythonCoreBaseModel):
    table_id: Optional["str"] = Field(None, alias="tableId")
    x: Optional["int"] = Field(None, alias="x")
    y: Optional["int"] = Field(None, alias="y")


class DataPermission(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    enabled: Optional["bool"] = Field(None, alias="enabled")
    type_: Optional["DataPermissionType"] = Field(None, alias="type")
    active: Optional["bool"] = Field(None, alias="active")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    advanced_data_permission_mode: Optional["AdvancedDataPermissionMode"] = Field(
        None, alias="advancedDataPermissionMode"
    )
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataPermissionSyncTableTransport(PythonCoreBaseModel):
    data_permission_table_id: Optional["str"] = Field(None, alias="dataPermissionTableId")
    sync_status: Optional["DataPermissionSyncStatus"] = Field(None, alias="syncStatus")
    sync_date: Optional["PythonCoreDatetime"] = Field(None, alias="syncDate")
    messages: Optional["List[Optional[str]]"] = Field(None, alias="messages")


class DataPermissionTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_permission_id: Optional["str"] = Field(None, alias="dataPermissionId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    table_name: Optional["str"] = Field(None, alias="tableName")
    user_column: Optional["str"] = Field(None, alias="userColumn")
    group_column: Optional["str"] = Field(None, alias="groupColumn")
    table_column: Optional["str"] = Field(None, alias="tableColumn")
    use_table_alias: Optional["bool"] = Field(None, alias="useTableAlias")
    column_column: Optional["str"] = Field(None, alias="columnColumn")
    value_column: Optional["str"] = Field(None, alias="valueColumn")
    unlimited_column: Optional["str"] = Field(None, alias="unlimitedColumn")
    assignment_type: Optional["DataPermissionAssignmentType"] = Field(None, alias="assignmentType")
    table_type: Optional["DataPermissionTableType"] = Field(None, alias="tableType")
    last_modified: Optional["PythonCoreDatetime"] = Field(None, alias="lastModified")
    sync_table_transport: Optional["DataPermissionSyncTableTransport"] = Field(None, alias="syncTableTransport")


class DataPermissionAssignmentTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_permission_id: Optional["str"] = Field(None, alias="dataPermissionId")
    user_id: Optional["str"] = Field(None, alias="userId")
    group_id: Optional["str"] = Field(None, alias="groupId")
    unlimited: Optional["bool"] = Field(None, alias="unlimited")
    user: Optional["UserTransport"] = Field(None, alias="user")
    group: Optional["GroupTransport"] = Field(None, alias="group")
    group_not_found: Optional["bool"] = Field(None, alias="groupNotFound")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class GroupTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    team_role: Optional["int"] = Field(None, alias="teamRole")
    pushed: Optional["bool"] = Field(None, alias="pushed")
    original_id: Optional["str"] = Field(None, alias="originalId")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    members_count: Optional["int"] = Field(None, alias="membersCount")


class UserTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    email: Optional["str"] = Field(None, alias="email")
    name: Optional["str"] = Field(None, alias="name")
    team_name: Optional["str"] = Field(None, alias="teamName")
    team_id: Optional["str"] = Field(None, alias="teamId")
    team_domain: Optional["str"] = Field(None, alias="teamDomain")
    api_token: Optional["str"] = Field(None, alias="apiToken")
    active: Optional["bool"] = Field(None, alias="active")
    token: Optional["str"] = Field(None, alias="token")
    account_created: Optional["bool"] = Field(None, alias="accountCreated")
    current: Optional["bool"] = Field(None, alias="current")
    language: Optional["str"] = Field(None, alias="language")
    avatar_url: Optional["str"] = Field(None, alias="avatarUrl")
    enable_notifications: Optional["bool"] = Field(None, alias="enableNotifications")
    notifications_time: Optional["str"] = Field(None, alias="notificationsTime")
    time_zone: Optional["str"] = Field(None, alias="timeZone")
    role: Optional["int"] = Field(None, alias="role")
    effective_role: Optional["int"] = Field(None, alias="effectiveRole")
    contentstore_admin: Optional["bool"] = Field(None, alias="contentstoreAdmin")
    backend_access: Optional["bool"] = Field(None, alias="backendAccess")
    last_log_in_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastLogInDate")
    is_first_log_in: Optional["bool"] = Field(None, alias="isFirstLogIn")
    is_celonis_user: Optional["bool"] = Field(None, alias="isCelonisUser")
    full_template_access: Optional["bool"] = Field(None, alias="fullTemplateAccess")
    group_ids: Optional["List[Optional[str]]"] = Field(None, alias="groupIds")
    name_and_email: Optional["str"] = Field(None, alias="nameAndEmail")
    name_or_email: Optional["str"] = Field(None, alias="nameOrEmail")
    member: Optional["bool"] = Field(None, alias="member")
    analyst: Optional["bool"] = Field(None, alias="analyst")
    admin: Optional["bool"] = Field(None, alias="admin")


class DataPermissionAssignmentRuleTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    assignment_id: Optional["str"] = Field(None, alias="assignmentId")
    table_id: Optional["str"] = Field(None, alias="tableId")
    column_name: Optional["str"] = Field(None, alias="columnName")
    created_date: Optional["PythonCoreDatetime"] = Field(None, alias="createdDate")
    values: Optional["List[Optional[DataPermissionAssignmentRuleValue]]"] = Field(None, alias="values")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataPermissionAssignmentRuleValue(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    rule_id: Optional["str"] = Field(None, alias="ruleId")
    value: Optional["str"] = Field(None, alias="value")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelListItemTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    total_loaded_rows: Optional["int"] = Field(None, alias="totalLoadedRows")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    permissions_configured: Optional["bool"] = Field(None, alias="permissionsConfigured")
    multi_event_log: Optional["bool"] = Field(None, alias="multiEventLog")


class DataPoolTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    time_stamp: Optional["PythonCoreDatetime"] = Field(None, alias="timeStamp")
    configuration_status: Optional["PoolConfigurationStatus"] = Field(None, alias="configurationStatus")
    locked: Optional["bool"] = Field(None, alias="locked")
    content_id: Optional["str"] = Field(None, alias="contentId")
    content_version: Optional["int"] = Field(None, alias="contentVersion")
    tags: Optional["List[Optional[Tag]]"] = Field(None, alias="tags")
    original_id: Optional["str"] = Field(None, alias="originalId")
    monitoring_target: Optional["bool"] = Field(None, alias="monitoringTarget")
    custom_monitoring_target: Optional["bool"] = Field(None, alias="customMonitoringTarget")
    custom_monitoring_target_active: Optional["bool"] = Field(None, alias="customMonitoringTargetActive")
    exported: Optional["bool"] = Field(None, alias="exported")
    monitoring_message_columns_migrated: Optional["bool"] = Field(None, alias="monitoringMessageColumnsMigrated")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    object_id: Optional["str"] = Field(None, alias="objectId")


class Tag(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")


class DataPoolUpdateStatusTransport(PythonCoreBaseModel):
    new_status: Optional["PoolConfigurationStatus"] = Field(None, alias="newStatus")


class CustomDataPoolConfigurationTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    name: Optional["str"] = Field(None, alias="name")
    config: Optional["DatabaseConnectionConfigurationTransport"] = Field(None, alias="config")
    object_id: Optional["str"] = Field(None, alias="objectId")


class DatabaseConnectionConfigurationTransport(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")
    template_id: Optional["str"] = Field(None, alias="templateId")
    server_name: Optional["str"] = Field(None, alias="serverName")
    port: Optional["int"] = Field(None, alias="port")
    database_name: Optional["str"] = Field(None, alias="databaseName")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    warehouse_name: Optional["str"] = Field(None, alias="warehouseName")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    connection_string_additional: Optional["str"] = Field(None, alias="connectionStringAdditional")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    use_custom_string: Optional["bool"] = Field(None, alias="useCustomString")
    custom_string: Optional["str"] = Field(None, alias="customString")
    custom_driver_class: Optional["str"] = Field(None, alias="customDriverClass")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    connection_timeout: Optional["int"] = Field(None, alias="connectionTimeout")
    certificate_validation_enabled: Optional["bool"] = Field(None, alias="certificateValidationEnabled")
    region: Optional["str"] = Field(None, alias="region")
    output_location: Optional["str"] = Field(None, alias="outputLocation")
    live_data_connection: Optional["bool"] = Field(None, alias="liveDataConnection")
    extract_row_id: Optional["bool"] = Field(None, alias="extractRowId")
    authentication_method: Optional["str"] = Field(None, alias="authenticationMethod")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    principal_id: Optional["str"] = Field(None, alias="principalId")
    principal_secret: Optional["str"] = Field(None, alias="principalSecret")
    service_account_email_id: Optional["str"] = Field(None, alias="serviceAccountEmailId")
    service_account_credentials: Optional["str"] = Field(None, alias="serviceAccountCredentials")
    database_validate_certificate: Optional["str"] = Field(None, alias="databaseValidateCertificate")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    encrypted_key: Optional["bool"] = Field(None, alias="encryptedKey")
    private_key_file_path: Optional["bool"] = Field(None, alias="privateKeyFilePath")
    private_key_passphrase: Optional["str"] = Field(None, alias="privateKeyPassphrase")
    private_key: Optional["str"] = Field(None, alias="privateKey")
    http_path: Optional["str"] = Field(None, alias="httpPath")
    personal_access_token: Optional["str"] = Field(None, alias="personalAccessToken")


class PoolProviderTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    id: Optional["str"] = Field(None, alias="id")
    pool_provider_type: Optional["PoolProviderType"] = Field(None, alias="poolProviderType")


class ObjectStorageBucketTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    bucket_uri: Optional["str"] = Field(None, alias="bucketURI")
    default_bucket: Optional["bool"] = Field(None, alias="defaultBucket")


class ZendeskDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["ZendeskConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class WorkdayDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["WorkdayConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class WorkdayReportConfiguration(PythonCoreBaseModel):
    report_name: Optional["str"] = Field(None, alias="reportName")
    report_url: Optional["str"] = Field(None, alias="reportUrl")


class UiPathDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["UiPathConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class SuccessFactorsDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SuccessFactorsConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class SnowflakeRestDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SnowflakeRestConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class ServiceNowCustomBatchSize(PythonCoreBaseModel):
    table: Optional["str"] = Field(None, alias="table")
    batch_size: Optional["int"] = Field(None, alias="batchSize")
    rolling_page_size: Optional["int"] = Field(None, alias="rollingPageSize")


class ServiceNowDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["ServiceNowConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class ServiceNowExecutionConfiguration(PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_batch_sizes: Optional["List[Optional[ServiceNowCustomBatchSize]]"] = Field(None, alias="customBatchSizes")


class SapSnsDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SapSnsConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class SapConnectionConfigurationTransport(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")
    host: Optional["str"] = Field(None, alias="host")
    system_number: Optional["str"] = Field(None, alias="systemNumber")
    client: Optional["str"] = Field(None, alias="client")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    compression_type: Optional["CompressionType"] = Field(None, alias="compressionType")
    use_snc: Optional["bool"] = Field(None, alias="useSnc")
    run_anywhere: Optional["bool"] = Field(None, alias="runAnywhere")
    snc_partner_name: Optional["str"] = Field(None, alias="sncPartnerName")
    use_change_logs: Optional["bool"] = Field(None, alias="useChangeLogs")
    include_change_log_columns: Optional["bool"] = Field(None, alias="includeChangeLogColumns")
    try_sync_change_log_extraction: Optional["bool"] = Field(None, alias="trySyncChangeLogExtraction")
    job_prefix: Optional["str"] = Field(None, alias="jobPrefix")
    advanced_settings: Optional["bool"] = Field(None, alias="advancedSettings")
    middleware: Optional["Middleware"] = Field(None, alias="middleware")
    group_name: Optional["str"] = Field(None, alias="groupName")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    pi_po_adapter: Optional["PiPoAdapter"] = Field(None, alias="piPoAdapter")
    gateway_port: Optional["str"] = Field(None, alias="gatewayPort")
    program_id: Optional["str"] = Field(None, alias="programId")
    use_tls: Optional["bool"] = Field(None, alias="useTls")
    wsdl_dir: Optional["str"] = Field(None, alias="wsdlDir")
    chunk_size: Optional["int"] = Field(None, alias="chunkSize")
    package_size: Optional["int"] = Field(None, alias="packageSize")
    package_size_header: Optional["int"] = Field(None, alias="packageSizeHeader")
    change_log_package_size: Optional["int"] = Field(None, alias="changeLogPackageSize")
    buffer_retry: Optional["bool"] = Field(None, alias="bufferRetry")
    retry_times: Optional["int"] = Field(None, alias="retryTimes")
    retry_secs: Optional["int"] = Field(None, alias="retrySecs")
    client_dependent: Optional["bool"] = Field(None, alias="clientDependent")
    sap_version: Optional["SapVersion"] = Field(None, alias="sapVersion")


class SapDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SapConnectionConfigurationTransport"] = Field(None, alias="config")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class SapMarketingCloudDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SapMarketingCloudConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class SalesforceDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["SalesforceConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class RossumV2DataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["RossumConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class PythonConnectorConnectionConfigurationParameter(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    value: Optional["str"] = Field(None, alias="value")
    confidential_value: Optional["str"] = Field(None, alias="confidentialValue")
    confidential: Optional["bool"] = Field(None, alias="confidential")


class PythonConnectorDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["PythonConnectorConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class OracleCloudDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["OracleCloudConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class MicrosoftDynamics365DataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["MicrosoftDynamics365ConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class KafkaDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["KafkaConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class KafkaTopicConfiguration(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    group_id: Optional["str"] = Field(None, alias="groupId")
    host: Optional["str"] = Field(None, alias="host")
    port: Optional["str"] = Field(None, alias="port")


class JiraDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["JiraConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class HappyFoxDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["HappyFoxConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class GoogleSheetsDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["GoogleSheetsConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class FieldglassDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["FieldglassConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class EventHubConfiguration(PythonCoreBaseModel):
    event_hub_name: Optional["str"] = Field(None, alias="eventHubName")
    consumer_group: Optional["str"] = Field(None, alias="consumerGroup")
    connection_string: Optional["str"] = Field(None, alias="connectionString")


class EventHubDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["EventHubConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class DatabaseDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["DatabaseConnectionConfigurationTransport"] = Field(None, alias="config")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class DataPushDataSourceTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class CustomDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["CustomConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class CustomExtractorConnectionConnfigurationParameter(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    value: Optional["str"] = Field(None, alias="value")
    confidential_value: Optional["str"] = Field(None, alias="confidentialValue")
    confidential: Optional["bool"] = Field(None, alias="confidential")


class CustomExtractorDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["CustomExtractorConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class CoupaDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["CoupaConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class CelonisActionEngineDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["CelonisActionEngineConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class BiPublisherDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["BiPublisherConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class BiPublisherReportConfiguration(PythonCoreBaseModel):
    report_path: Optional["str"] = Field(None, alias="reportPath")


class AzureServiceBusDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["AzureServiceBusConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class AzureServiceBusSubscriptionConfiguration(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    namespace: Optional["str"] = Field(None, alias="namespace")
    entity_path: Optional["str"] = Field(None, alias="entityPath")
    shared_access_signature: Optional["str"] = Field(None, alias="sharedAccessSignature")


class AutomationAnywhereDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["AutomationAnywhereConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class AribaDataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["AribaConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class AribaTableExecutionConfiguration(PythonCoreBaseModel):
    table: Optional["str"] = Field(None, alias="table")
    template_type: Optional["AribaTemplateType"] = Field(None, alias="templateType")
    ignore_records_with_error: Optional["bool"] = Field(None, alias="ignoreRecordsWithError")
    view_template_name: Optional["str"] = Field(None, alias="viewTemplateName")


class AmazonS3DataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    config: Optional["AmazonS3ConnectionConfiguration"] = Field(None, alias="config")
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class CopyVersionRequest(PythonCoreBaseModel):
    source_pool_id: Optional["str"] = Field(None, alias="sourcePoolId")
    target_team_domain: Optional["str"] = Field(None, alias="targetTeamDomain")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    target_pool_id: Optional["str"] = Field(None, alias="targetPoolId")
    activate: Optional["bool"] = Field(None, alias="activate")
    data_source_mapping: Optional["Dict[str, Optional[str]]"] = Field(None, alias="dataSourceMapping")
    data_model_mapping: Optional["Dict[str, Optional[str]]"] = Field(None, alias="dataModelMapping")
    job_mapping: Optional["Dict[str, Optional[str]]"] = Field(None, alias="jobMapping")


class DraftTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    object_id: Optional["str"] = Field(None, alias="objectId")
    object_type: Optional["str"] = Field(None, alias="objectType")
    object_name: Optional["str"] = Field(None, alias="objectName")
    object_base_reference: Optional["str"] = Field(None, alias="objectBaseReference")
    object_base_version: Optional["str"] = Field(None, alias="objectBaseVersion")
    object_base_external: Optional["bool"] = Field(None, alias="objectBaseExternal")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    checkpoint: Optional["bool"] = Field(None, alias="checkpoint")
    extra_metadata: Optional["str"] = Field(None, alias="extraMetadata")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    serialization_type: Optional["SerializationType"] = Field(None, alias="serializationType")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    published: Optional["bool"] = Field(None, alias="published")
    active: Optional["bool"] = Field(None, alias="active")
    version: Optional["str"] = Field(None, alias="version")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")
    update_date: Optional["PythonCoreDatetime"] = Field(None, alias="updateDate")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    publish_date: Optional["PythonCoreDatetime"] = Field(None, alias="publishDate")
    updated_or_created_by: Optional["str"] = Field(None, alias="updatedOrCreatedBy")


class CsvColumnParsingOptions(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    thousands_separator: Optional["str"] = Field(None, alias="thousandsSeparator")
    decimal_separator: Optional["str"] = Field(None, alias="decimalSeparator")


class CsvParsingOptions(PythonCoreBaseModel):
    escape_sequence: Optional["str"] = Field(None, alias="escapeSequence")
    quote_sequence: Optional["str"] = Field(None, alias="quoteSequence")
    separator_sequence: Optional["str"] = Field(None, alias="separatorSequence")
    line_ending: Optional["str"] = Field(None, alias="lineEnding")
    char_set: Optional["str"] = Field(None, alias="charSet")
    decimal_separator: Optional["str"] = Field(None, alias="decimalSeparator")
    thousand_separator: Optional["str"] = Field(None, alias="thousandSeparator")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    additional_column_options: Optional["List[Optional[CsvColumnParsingOptions]]"] = Field(
        None, alias="additionalColumnOptions"
    )


class DataPushJob(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    target_name: Optional["str"] = Field(None, alias="targetName")
    last_modified: Optional["PythonCoreDatetime"] = Field(None, alias="lastModified")
    last_ping: Optional["PythonCoreDatetime"] = Field(None, alias="lastPing")
    status: Optional["JobStatus"] = Field(None, alias="status")
    type_: Optional["JobType"] = Field(None, alias="type")
    file_type: Optional["UploadFileType"] = Field(None, alias="fileType")
    target_schema: Optional["str"] = Field(None, alias="targetSchema")
    upsert_strategy: Optional["DataPushUpsertStrategy"] = Field(None, alias="upsertStrategy")
    fallback_varchar_length: Optional["int"] = Field(None, alias="fallbackVarcharLength")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    connection_id: Optional["str"] = Field(None, alias="connectionId")
    post_execution_query: Optional["str"] = Field(None, alias="postExecutionQuery")
    sanitized_post_execution_query: Optional["str"] = Field(None, alias="sanitizedPostExecutionQuery")
    allow_duplicate: Optional["bool"] = Field(None, alias="allowDuplicate")
    foreign_keys: Optional["str"] = Field(None, alias="foreignKeys")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    mirror_target_names: Optional["List[Optional[str]]"] = Field(None, alias="mirrorTargetNames")
    table_schema: Optional["TableTransport"] = Field(None, alias="tableSchema")
    csv_parsing_options: Optional["CsvParsingOptions"] = Field(None, alias="csvParsingOptions")
    keys: Optional["List[Optional[str]]"] = Field(None, alias="keys")
    logs: Optional["List[Optional[str]]"] = Field(None, alias="logs")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class UploadDirectStorageTableChunkRequest(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    file: Optional["BytesIO"] = Field(None, alias="file")


class DirectStorageTableChunkTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    file_name: Optional["str"] = Field(None, alias="fileName")


class DataCommand(PythonCoreBaseModel):
    cube_id: Optional["str"] = Field(None, alias="cubeId")
    commands: Optional["List[Optional[DataQuery]]"] = Field(None, alias="commands")


class DataExportRequest(PythonCoreBaseModel):
    query_environment: Optional["QueryEnvironment"] = Field(None, alias="queryEnvironment")
    data_command: Optional["DataCommand"] = Field(None, alias="dataCommand")
    export_type: Optional["ExportType"] = Field(None, alias="exportType")


class DataPermissionRule(PythonCoreBaseModel):
    values: Optional["List[Optional[str]]"] = Field(None, alias="values")
    column_id: Optional["str"] = Field(None, alias="columnId")
    table_id: Optional["str"] = Field(None, alias="tableId")


class DataQuery(PythonCoreBaseModel):
    computation_id: Optional["int"] = Field(None, alias="computationId")
    queries: Optional["List[Optional[str]]"] = Field(None, alias="queries")
    is_transient: Optional["bool"] = Field(None, alias="isTransient")


class Kpi(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    template: Optional["str"] = Field(None, alias="template")
    parameter_count: Optional["int"] = Field(None, alias="parameterCount")
    error: Optional["str"] = Field(None, alias="error")
    formula: Optional["str"] = Field(None, alias="formula")


class KpiInformation(PythonCoreBaseModel):
    kpis: Optional["Dict[str, Optional[Kpi]]"] = Field(None, alias="kpis")


class QueryEnvironment(PythonCoreBaseModel):
    accelerator_session_id: Optional["str"] = Field(None, alias="acceleratorSessionId")
    process_id: Optional["str"] = Field(None, alias="processId")
    user_id: Optional["str"] = Field(None, alias="userId")
    user_name: Optional["str"] = Field(None, alias="userName")
    load_script: Optional["str"] = Field(None, alias="loadScript")
    kpi_infos: Optional["KpiInformation"] = Field(None, alias="kpiInfos")
    data_permission_rules: Optional["List[Optional[DataPermissionRule]]"] = Field(None, alias="dataPermissionRules")
    data_permission_strategy: Optional["DataPermissionStrategy"] = Field(None, alias="dataPermissionStrategy")


class DataExportStatusResponse(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    export_status: Optional["ExportStatus"] = Field(None, alias="exportStatus")
    created: Optional["PythonCoreDatetime"] = Field(None, alias="created")
    message: Optional["str"] = Field(None, alias="message")
    export_type: Optional["ExportType"] = Field(None, alias="exportType")
    export_chunks: Optional["int"] = Field(None, alias="exportChunks")


class UplinkRegistrationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    client_id: Optional["str"] = Field(None, alias="clientId")
    last_connected: Optional["PythonCoreDatetime"] = Field(None, alias="lastConnected")
    locked: Optional["bool"] = Field(None, alias="locked")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    connected: Optional["bool"] = Field(None, alias="connected")
    connector_version: Optional["str"] = Field(None, alias="connectorVersion")
    type_: Optional["UplinkRegistrationType"] = Field(None, alias="type")


class CreateApplicationKeyTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")


class ApplicationKeyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    key: Optional["str"] = Field(None, alias="key")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    last_used_at: Optional["PythonCoreDatetime"] = Field(None, alias="lastUsedAt")
    original_id: Optional["str"] = Field(None, alias="originalId")
    team_role: Optional["int"] = Field(None, alias="teamRole")


class CreateSubscriptionTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    source: Optional["str"] = Field(None, alias="source")
    object_type: Optional["str"] = Field(None, alias="objectType")


class SubscriptionTransport(PythonCoreBaseModel):
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    id: Optional["str"] = Field(None, alias="id")
    object_id: Optional["str"] = Field(None, alias="objectId")
    source: Optional["str"] = Field(None, alias="source")
    object_type: Optional["str"] = Field(None, alias="objectType")
    user_id: Optional["str"] = Field(None, alias="userId")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    muted: Optional["bool"] = Field(None, alias="muted")


class ExecutionLogTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")
    exception: Optional["Dict[str, Any]"] = Field(None, alias="exception")
    exception_type: Optional["ExceptionType"] = Field(None, alias="exceptionType")
    exception_stacktrace: Optional["str"] = Field(None, alias="exceptionStacktrace")
    log_translation_code: Optional["ExecutionMessageCode"] = Field(None, alias="logTranslationCode")
    log_translation_parameters: Optional["List[Optional[LogTranslationParameter]]"] = Field(
        None, alias="logTranslationParameters"
    )
    message_type: Optional["ExecutionLogMessageType"] = Field(None, alias="messageType")
    extractor: Optional["bool"] = Field(None, alias="extractor")


class LogTranslationParameter(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    value: Optional["str"] = Field(None, alias="value")


class DataPushJobTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    target_name: Optional["str"] = Field(None, alias="targetName")
    mirror_target_names: Optional["List[Optional[str]]"] = Field(None, alias="mirrorTargetNames")
    status: Optional["JobStatus"] = Field(None, alias="status")
    type_: Optional["JobType"] = Field(None, alias="type")
    file_type: Optional["UploadFileType"] = Field(None, alias="fileType")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    connection_id: Optional["str"] = Field(None, alias="connectionId")
    logs: Optional["List[Optional[str]]"] = Field(None, alias="logs")
    keys: Optional["List[Optional[str]]"] = Field(None, alias="keys")
    table_schema: Optional["TableTransport"] = Field(None, alias="tableSchema")
    csv_parsing_options: Optional["CsvParsingOptions"] = Field(None, alias="csvParsingOptions")
    upsert_strategy: Optional["DataPushUpsertStrategy"] = Field(None, alias="upsertStrategy")
    fallback_varchar_length: Optional["int"] = Field(None, alias="fallbackVarcharLength")
    pool_provider_session_id: Optional["str"] = Field(None, alias="poolProviderSessionId")
    target_schema: Optional["str"] = Field(None, alias="targetSchema")
    post_execution_query: Optional["str"] = Field(None, alias="postExecutionQuery")
    sanitized_post_execution_query: Optional["str"] = Field(None, alias="sanitizedPostExecutionQuery")
    allow_duplicate: Optional["bool"] = Field(None, alias="allowDuplicate")
    foreign_keys: Optional["str"] = Field(None, alias="foreignKeys")
    foreign_keys_as_list: Optional["List[Optional[str]]"] = Field(None, alias="foreignKeysAsList")


class DuplicateRemovalOptions(PythonCoreBaseModel):
    remove_duplicates: Optional["bool"] = Field(None, alias="removeDuplicates")
    duplicate_removal_order_column: Optional["str"] = Field(None, alias="duplicateRemovalOrderColumn")
    filter_deletions_on_order_column: Optional["bool"] = Field(None, alias="filterDeletionsOnOrderColumn")


class ExtractionExecutionTransport(PythonCoreBaseModel):
    tables: Optional["List[Optional[TableTransport]]"] = Field(None, alias="tables")
    result: Optional["JobResult"] = Field(None, alias="result")


class UpdateTaskTemplateStatusTransport(PythonCoreBaseModel):
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")


class BulkUpdateTaskTemplateStatusRequest(PythonCoreBaseModel):
    template_ids: Optional["List[Optional[str]]"] = Field(None, alias="templateIds")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")


class BulkTaskTemplateRequestBase(PythonCoreBaseModel):
    template_ids: Optional["List[Optional[str]]"] = Field(None, alias="templateIds")


class NewTaskTemplateTransport(PythonCoreBaseModel):
    task_instance_id: Optional["str"] = Field(None, alias="taskInstanceId")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")


class StreamingSubscriptionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    display_name: Optional["str"] = Field(None, alias="displayName")
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    type_: Optional["StreamingType"] = Field(None, alias="type")
    started: Optional["bool"] = Field(None, alias="started")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")


class StreamingConfigurationTransport(PythonCoreBaseModel):
    tables: Optional["List[Optional[StreamingTableTransport]]"] = Field(None, alias="tables")
    subscriptions: Optional["List[Optional[StreamingSubscriptionTransport]]"] = Field(None, alias="subscriptions")


class SchedulingTriggersTransport(PythonCoreBaseModel):
    scheduling_id: Optional["str"] = Field(None, alias="schedulingId")
    triggering_scheduling_ids: Optional["List[Optional[str]]"] = Field(None, alias="triggeringSchedulingIds")
    triggered_scheduling_ids: Optional["List[Optional[str]]"] = Field(None, alias="triggeredSchedulingIds")


class WorkbenchReplRequest(PythonCoreBaseModel):
    job_id: Optional["str"] = Field(None, alias="jobId")
    transformation_id: Optional["str"] = Field(None, alias="transformationId")
    statement: Optional["str"] = Field(None, alias="statement")


class WorkbenchQueryStatusTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    query: Optional["str"] = Field(None, alias="query")


class NewTaskInstanceTransport(PythonCoreBaseModel):
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    task_id: Optional["str"] = Field(None, alias="taskId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")


class TableExtractionValidationTransport(PythonCoreBaseModel):
    extraction_id: Optional["str"] = Field(None, alias="extractionId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    validation_type: Optional["TableExtractionValidationType"] = Field(None, alias="validationType")
    message: Optional["TranslatedConnectorMessage"] = Field(None, alias="message")


class TranslatedConnectorMessage(PythonCoreBaseModel):
    message_translation_code: Optional["ExecutionMessageCode"] = Field(None, alias="messageTranslationCode")
    log_translation_parameters: Optional["List[Optional[LogTranslationParameter]]"] = Field(
        None, alias="logTranslationParameters"
    )


class ExtractionPreviewLogs(PythonCoreBaseModel):
    log_level: Optional["LogLevel"] = Field(None, alias="logLevel")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    execution_log: Optional["ExecutionLogTransport"] = Field(None, alias="executionLog")


class ExtractionPreviewResponse(PythonCoreBaseModel):
    successful: Optional["bool"] = Field(None, alias="successful")
    columns: Optional["List[Optional[str]]"] = Field(None, alias="columns")
    records: Optional["List[Optional[List[Optional[str]]]]"] = Field(None, alias="records")
    logs: Optional["List[Optional[ExtractionPreviewLogs]]"] = Field(None, alias="logs")


class DataModelExecutionConfiguration(PythonCoreBaseModel):
    data_model_execution_id: Optional["str"] = Field(None, alias="dataModelExecutionId")
    tables: Optional["List[Optional[str]]"] = Field(None, alias="tables")


class ExtractionConfiguration(PythonCoreBaseModel):
    extraction_id: Optional["str"] = Field(None, alias="extractionId")
    load_only_subset_of_tables: Optional["bool"] = Field(None, alias="loadOnlySubsetOfTables")
    tables: Optional["List[Optional[str]]"] = Field(None, alias="tables")


class JobExecutionConfiguration(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    execution_id: Optional["str"] = Field(None, alias="executionId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    mode: Optional["ExtractionMode"] = Field(None, alias="mode")
    execute_only_subset_of_transformations: Optional["bool"] = Field(None, alias="executeOnlySubsetOfTransformations")
    transformations: Optional["List[Optional[str]]"] = Field(None, alias="transformations")
    execute_only_subset_of_extractions: Optional["bool"] = Field(None, alias="executeOnlySubsetOfExtractions")
    extractions: Optional["List[Optional[ExtractionConfiguration]]"] = Field(None, alias="extractions")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    load_only_subset_of_data_models: Optional["bool"] = Field(None, alias="loadOnlySubsetOfDataModels")
    data_models: Optional["List[Optional[DataModelExecutionConfiguration]]"] = Field(None, alias="dataModels")


class JobCopyRequestTransport(PythonCoreBaseModel):
    destination_team_domain: Optional["str"] = Field(None, alias="destinationTeamDomain")
    destination_pool_id: Optional["str"] = Field(None, alias="destinationPoolId")
    destination_data_source_id: Optional["str"] = Field(None, alias="destinationDataSourceId")


class JobAutoCancellationConfigurationTransport(PythonCoreBaseModel):
    enabled: Optional["bool"] = Field(None, alias="enabled")
    job_id: Optional["str"] = Field(None, alias="jobId")
    cancel_if_data_job_execution_time_longer_than: Optional["int"] = Field(
        None, alias="cancelIfDataJobExecutionTimeLongerThan"
    )


class JobAlertConfigurationTransport(PythonCoreBaseModel):
    enabled: Optional["bool"] = Field(None, alias="enabled")
    job_id: Optional["str"] = Field(None, alias="jobId")
    notify_ifdata_job_fails: Optional["bool"] = Field(None, alias="notifyIfdataJobFails")
    notify_ifdata_job_finishes_successfully: Optional["DataJobSuccessfulNotificationType"] = Field(
        None, alias="notifyIfdataJobFinishesSuccessfully"
    )
    notify_ifdata_job_finishes_skipped: Optional["DataJobSkippedNotificationType"] = Field(
        None, alias="notifyIfdataJobFinishesSkipped"
    )
    notify_ifdata_job_execution_time_longer_than: Optional["int"] = Field(
        None, alias="notifyIfdataJobExecutionTimeLongerThan"
    )


class PoolColumn(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    length: Optional["int"] = Field(None, alias="length")
    type_: Optional["PoolColumnType"] = Field(None, alias="type")


class PoolSchema(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    tables: Optional["List[Optional[PoolTable]]"] = Field(None, alias="tables")
    schema_name: Optional["str"] = Field(None, alias="schemaName")


class PoolTable(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    loader_source: Optional["str"] = Field(None, alias="loaderSource")
    available: Optional["bool"] = Field(None, alias="available")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    columns: Optional["List[Optional[PoolColumn]]"] = Field(None, alias="columns")
    type_: Optional["PropertyType"] = Field(None, alias="type")
    schema_name: Optional["str"] = Field(None, alias="schemaName")


class DataColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    duplicate_name: Optional["bool"] = Field(None, alias="duplicateName")
    uses_reserved_name: Optional["bool"] = Field(None, alias="usesReservedName")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    thousand_separator: Optional["str"] = Field(None, alias="thousandSeparator")
    decimal_separator: Optional["str"] = Field(None, alias="decimalSeparator")
    string_length: Optional["int"] = Field(None, alias="stringLength")


class DataStorePreviewData(PythonCoreBaseModel):
    columns: Optional["List[Optional[DataColumn]]"] = Field(None, alias="columns")
    columns_with_sanitized_name: Optional["List[Optional[DataColumn]]"] = Field(None, alias="columnsWithSanitizedName")
    data_columns: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="dataColumns")
    display_error: Optional["str"] = Field(None, alias="displayError")


class InferFromSampleResponse(PythonCoreBaseModel):
    successful: Optional["bool"] = Field(None, alias="successful")
    error_message: Optional["TranslatedConnectorMessage"] = Field(None, alias="errorMessage")
    configuration: Optional["CustomExtractorEndpointResponse"] = Field(None, alias="configuration")
    representation_response: Optional["RepresentationResponse"] = Field(None, alias="representationResponse")
    response_root_candidates: Optional["List[Optional[List[Optional[str]]]]"] = Field(
        None, alias="responseRootCandidates"
    )
    all_fields_not_in_array: Optional["List[Optional[List[Optional[str]]]]"] = Field(None, alias="allFieldsNotInArray")


class RepresentationResponse(PythonCoreBaseModel):
    representation: Optional["str"] = Field(None, alias="representation")


class InferFromSampleRequest(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    custom_extractor_configuration: Optional["CustomExtractorConfiguration"] = Field(
        None, alias="customExtractorConfiguration"
    )
    endpoint: Optional["CustomExtractorEndpoint"] = Field(None, alias="endpoint")
    response_type: Optional["CustomExtractorResponseType"] = Field(None, alias="responseType")
    samples: Optional["List[Optional[str]]"] = Field(None, alias="samples")
    response_root: Optional["List[Optional[str]]"] = Field(None, alias="responseRoot")
    generate_configuration: Optional["bool"] = Field(None, alias="generateConfiguration")
    generate_representation: Optional["bool"] = Field(None, alias="generateRepresentation")


class DataTransferImportTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    source_data_pool_id: Optional["str"] = Field(None, alias="sourceDataPoolId")
    target_data_pool_id: Optional["str"] = Field(None, alias="targetDataPoolId")
    source_data_source_id: Optional["str"] = Field(None, alias="sourceDataSourceId")
    target_data_source_id: Optional["str"] = Field(None, alias="targetDataSourceId")
    source_data_pool_name: Optional["str"] = Field(None, alias="sourceDataPoolName")
    source_data_source_name: Optional["str"] = Field(None, alias="sourceDataSourceName")
    source_data_source_type: Optional["str"] = Field(None, alias="sourceDataSourceType")
    target_data_source_name: Optional["str"] = Field(None, alias="targetDataSourceName")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")


class ImportedDataSourceTableSyncTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    source_data_pool_id: Optional["str"] = Field(None, alias="sourceDataPoolId")
    source_data_source_id: Optional["str"] = Field(None, alias="sourceDataSourceId")


class TableSyncResultTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    error_code: Optional["str"] = Field(None, alias="errorCode")
    failed: Optional["bool"] = Field(None, alias="failed")


class DataSourceTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    connected: Optional["bool"] = Field(None, alias="connected")
    locked: Optional["bool"] = Field(None, alias="locked")
    uplink_name: Optional["str"] = Field(None, alias="uplinkName")
    signature: Optional["str"] = Field(None, alias="signature")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_selected: Optional["bool"] = Field(None, alias="internalSystemSelected")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    export_available: Optional["bool"] = Field(None, alias="exportAvailable")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    creator_username: Optional["str"] = Field(None, alias="creatorUsername")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    normalized_name: Optional["str"] = Field(None, alias="normalizedName")
    configured: Optional["bool"] = Field(None, alias="configured")
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    imported: Optional["bool"] = Field(None, alias="imported")


class ColumnNameMappingFromPoolConfig(PythonCoreBaseModel):
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    table_name: Optional["str"] = Field(None, alias="tableName")
    table_names_column: Optional["str"] = Field(None, alias="tableNamesColumn")
    technical_names_column: Optional["str"] = Field(None, alias="technicalNamesColumn")
    pretty_names_column: Optional["str"] = Field(None, alias="prettyNamesColumn")
    language_key_column: Optional["str"] = Field(None, alias="languageKeyColumn")


class NameMappingFromPoolConfig(PythonCoreBaseModel):
    table_mapping_config: Optional["TableNameMappingFromPoolConfig"] = Field(None, alias="tableMappingConfig")
    column_mapping_config: Optional["ColumnNameMappingFromPoolConfig"] = Field(None, alias="columnMappingConfig")


class TableNameMappingFromPoolConfig(PythonCoreBaseModel):
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    table_name: Optional["str"] = Field(None, alias="tableName")
    technical_names_column: Optional["str"] = Field(None, alias="technicalNamesColumn")
    pretty_names_column: Optional["str"] = Field(None, alias="prettyNamesColumn")
    language_key_column: Optional["str"] = Field(None, alias="languageKeyColumn")


class NameMappingAggregated(PythonCoreBaseModel):
    count: Optional["int"] = Field(None, alias="count")
    type_: Optional["str"] = Field(None, alias="type")
    language: Optional["str"] = Field(None, alias="language")


class NameMappingLoadReport(PythonCoreBaseModel):
    nb_of_tables_in_data_model: Optional["int"] = Field(None, alias="nbOfTablesInDataModel")
    nb_of_table_mappings: Optional["int"] = Field(None, alias="nbOfTableMappings")
    nb_of_column_mappings: Optional["int"] = Field(None, alias="nbOfColumnMappings")
    name_mappings_aggregated: Optional["List[Optional[NameMappingAggregated]]"] = Field(
        None, alias="nameMappingsAggregated"
    )


class DataModelFactoryCalendar(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class AnonymizationSaltTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    salt: Optional["str"] = Field(None, alias="salt")


class DataModel(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    create_date: Optional["PythonCoreDatetime"] = Field(None, alias="createDate")
    changed_date: Optional["PythonCoreDatetime"] = Field(None, alias="changedDate")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    automatic_reloads: Optional["bool"] = Field(None, alias="automaticReloads")
    configuration_skipped: Optional["bool"] = Field(None, alias="configurationSkipped")
    data_model_calendar_type: Optional["DataModelCalendarType"] = Field(None, alias="dataModelCalendarType")
    preferred_load_state: Optional["LoadState"] = Field(None, alias="preferredLoadState")
    eventlog_automerge_enabled: Optional["bool"] = Field(None, alias="eventlogAutomergeEnabled")
    auto_merge_execution_mode: Optional["AutoMergeExecutionMode"] = Field(None, alias="autoMergeExecutionMode")
    linearization_enabled: Optional["bool"] = Field(None, alias="linearizationEnabled")
    renamed: Optional["bool"] = Field(None, alias="renamed")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    original_id: Optional["str"] = Field(None, alias="originalId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelCustomCalendarEntry(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    day: Optional["CalendarDay"] = Field(None, alias="day")
    working_day: Optional["bool"] = Field(None, alias="workingDay")
    start_time: Optional["int"] = Field(None, alias="startTime")
    end_time: Optional["int"] = Field(None, alias="endTime")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelExecution(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    partial_load: Optional["bool"] = Field(None, alias="partialLoad")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelExecutionTable(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_execution_id: Optional["str"] = Field(None, alias="dataModelExecutionId")
    data_model_table_id: Optional["str"] = Field(None, alias="dataModelTableId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelForeignKey(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    source_table_id: Optional["str"] = Field(None, alias="sourceTableId")
    target_table_id: Optional["str"] = Field(None, alias="targetTableId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelForeignKeyColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    foreign_key_id: Optional["str"] = Field(None, alias="foreignKeyId")
    source_column_name: Optional["str"] = Field(None, alias="sourceColumnName")
    target_column_name: Optional["str"] = Field(None, alias="targetColumnName")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelSignalLink(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelSignalLinkColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_signal_link_id: Optional["str"] = Field(None, alias="dataModelSignalLinkId")
    data_model_signal_link_mapping_id: Optional["str"] = Field(None, alias="dataModelSignalLinkMappingId")
    table_id: Optional["str"] = Field(None, alias="tableId")
    column_name: Optional["str"] = Field(None, alias="columnName")
    type_: Optional["DataModelSignalLinkColumnDirection"] = Field(None, alias="type")
    priority: Optional["int"] = Field(None, alias="priority")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelTable(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    alias: Optional["str"] = Field(None, alias="alias")
    use_direct_storage: Optional["bool"] = Field(None, alias="useDirectStorage")
    alias_or_name: Optional["str"] = Field(None, alias="aliasOrName")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataModelTableColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    table_id: Optional["str"] = Field(None, alias="tableId")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    order: Optional["int"] = Field(None, alias="order")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataPool(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    content_id: Optional["str"] = Field(None, alias="contentId")
    content_version: Optional["int"] = Field(None, alias="contentVersion")
    configuration_status: Optional["PoolConfigurationStatus"] = Field(None, alias="configurationStatus")
    locked: Optional["bool"] = Field(None, alias="locked")
    time_stamp: Optional["PythonCoreDatetime"] = Field(None, alias="timeStamp")
    tags: Optional["str"] = Field(None, alias="tags")
    monitoring_target: Optional["bool"] = Field(None, alias="monitoringTarget")
    custom_monitoring_target: Optional["bool"] = Field(None, alias="customMonitoringTarget")
    custom_monitoring_target_active: Optional["bool"] = Field(None, alias="customMonitoringTargetActive")
    exported: Optional["bool"] = Field(None, alias="exported")
    original_id: Optional["str"] = Field(None, alias="originalId")
    monitoring_message_columns_migrated: Optional["bool"] = Field(None, alias="monitoringMessageColumnsMigrated")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DataPoolVersion(PythonCoreBaseModel):
    schema_version: Optional["str"] = Field(None, alias="schemaVersion")
    jobs: Optional["List[Optional[Job]]"] = Field(None, alias="jobs")
    job_schedulings: Optional["List[Optional[JobScheduling]]"] = Field(None, alias="jobSchedulings")
    schedulings: Optional["List[Optional[Scheduling]]"] = Field(None, alias="schedulings")
    scheduling_triggers: Optional["List[Optional[SchedulingTrigger]]"] = Field(None, alias="schedulingTriggers")
    table_extractions: Optional["List[Optional[TableExtraction]]"] = Field(None, alias="tableExtractions")
    table_extraction_calculated_columns: Optional["List[Optional[TableExtractionCalculatedColumn]]"] = Field(
        None, alias="tableExtractionCalculatedColumns"
    )
    table_extraction_columns: Optional["List[Optional[TableExtractionColumn]]"] = Field(
        None, alias="tableExtractionColumns"
    )
    table_extraction_joins: Optional["List[Optional[TableExtractionJoin]]"] = Field(None, alias="tableExtractionJoins")
    data_model_executions: Optional["List[Optional[DataModelExecution]]"] = Field(None, alias="dataModelExecutions")
    data_model_execution_tables: Optional["List[Optional[DataModelExecutionTable]]"] = Field(
        None, alias="dataModelExecutionTables"
    )
    tasks: Optional["List[Optional[Task]]"] = Field(None, alias="tasks")
    task_instances: Optional["List[Optional[TaskInstance]]"] = Field(None, alias="taskInstances")
    variables: Optional["List[Optional[Variable]]"] = Field(None, alias="variables")
    variable_default_settings: Optional["List[Optional[VariableDefaultSettings]]"] = Field(
        None, alias="variableDefaultSettings"
    )
    variable_default_values: Optional["List[Optional[VariableDefaultValue]]"] = Field(
        None, alias="variableDefaultValues"
    )
    variable_settings: Optional["List[Optional[VariableSettings]]"] = Field(None, alias="variableSettings")
    variable_values: Optional["List[Optional[VariableValue]]"] = Field(None, alias="variableValues")
    data_models: Optional["List[Optional[DataModel]]"] = Field(None, alias="dataModels")
    data_model_configurations: Optional["List[Optional[DataModelConfiguration]]"] = Field(
        None, alias="dataModelConfigurations"
    )
    data_model_custom_calendar_entries: Optional["List[Optional[DataModelCustomCalendarEntry]]"] = Field(
        None, alias="dataModelCustomCalendarEntries"
    )
    data_model_factory_calendars: Optional["List[Optional[DataModelFactoryCalendar]]"] = Field(
        None, alias="dataModelFactoryCalendars"
    )
    data_model_foreign_keys: Optional["List[Optional[DataModelForeignKey]]"] = Field(None, alias="dataModelForeignKeys")
    data_model_foreign_key_columns: Optional["List[Optional[DataModelForeignKeyColumn]]"] = Field(
        None, alias="dataModelForeignKeyColumns"
    )
    data_model_signal_links: Optional["List[Optional[DataModelSignalLink]]"] = Field(None, alias="dataModelSignalLinks")
    data_model_signal_link_columns: Optional["List[Optional[DataModelSignalLinkColumn]]"] = Field(
        None, alias="dataModelSignalLinkColumns"
    )
    data_model_tables: Optional["List[Optional[DataModelTable]]"] = Field(None, alias="dataModelTables")
    data_model_table_columns: Optional["List[Optional[DataModelTableColumn]]"] = Field(
        None, alias="dataModelTableColumns"
    )
    replication_cockpit_data: Optional["VersionedObject"] = Field(None, alias="replicationCockpitData")
    data_pool: Optional["DataPool"] = Field(None, alias="dataPool")
    data_sources: Optional["List[Optional[DataSource]]"] = Field(None, alias="dataSources")


class DataSource(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    type_: Optional["str"] = Field(None, alias="type")
    signature: Optional["str"] = Field(None, alias="signature")
    configuration: Optional["List[Optional[Any]]"] = Field(None, alias="configuration")
    metadata: Optional["str"] = Field(None, alias="metadata")
    uplink_id: Optional["str"] = Field(None, alias="uplinkId")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    exported: Optional["bool"] = Field(None, alias="exported")
    extractor_port: Optional["int"] = Field(None, alias="extractorPort")
    anonymization_algorithm: Optional["AnonymizationAlgorithm"] = Field(None, alias="anonymizationAlgorithm")
    salt_id: Optional["str"] = Field(None, alias="saltId")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    reachable_and_valid: Optional["bool"] = Field(None, alias="reachableAndValid")
    imported: Optional["bool"] = Field(None, alias="imported")
    configured: Optional["bool"] = Field(None, alias="configured")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class Job(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    time_stamp: Optional["PythonCoreDatetime"] = Field(None, alias="timeStamp")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    current_execution_id: Optional["str"] = Field(None, alias="currentExecutionId")
    dag_based_execution_enabled: Optional["bool"] = Field(None, alias="dagBasedExecutionEnabled")
    latest_execution_item_id: Optional["str"] = Field(None, alias="latestExecutionItemId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class JobScheduling(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    schedule_id: Optional["str"] = Field(None, alias="scheduleId")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class Scheduling(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    enabled: Optional["bool"] = Field(None, alias="enabled")
    monitored: Optional["bool"] = Field(None, alias="monitored")
    mode: Optional["ExtractionMode"] = Field(None, alias="mode")
    execution_pattern: Optional["ExecutionPattern"] = Field(None, alias="executionPattern")
    minute: Optional["int"] = Field(None, alias="minute")
    every_x_hours: Optional["int"] = Field(None, alias="everyXHours")
    time: Optional["str"] = Field(None, alias="time")
    day: Optional["int"] = Field(None, alias="day")
    week_days: Optional["str"] = Field(None, alias="weekDays")
    month_pattern: Optional["MonthPattern"] = Field(None, alias="monthPattern")
    custom_cron: Optional["str"] = Field(None, alias="customCron")
    next_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="nextExecutionDate")
    reload_all_data_models_after_execution: Optional["bool"] = Field(None, alias="reloadAllDataModelsAfterExecution")
    type_: Optional["SchedulingType"] = Field(None, alias="type")
    user_creator_id: Optional["str"] = Field(None, alias="userCreatorId")
    latest_execution_item_id: Optional["str"] = Field(None, alias="latestExecutionItemId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class SchedulingTrigger(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    scheduling_id: Optional["str"] = Field(None, alias="schedulingId")
    triggering_scheduling_id: Optional["str"] = Field(None, alias="triggeringSchedulingId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class TableExtraction(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    use_join: Optional["bool"] = Field(None, alias="useJoin")
    use_manual_p_ks: Optional["bool"] = Field(None, alias="useManualPKs")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    rename_target_table: Optional["bool"] = Field(None, alias="renameTargetTable")
    target_table_name: Optional["str"] = Field(None, alias="targetTableName")
    filter_definition: Optional["str"] = Field(None, alias="filterDefinition")
    delta_filter_definition: Optional["str"] = Field(None, alias="deltaFilterDefinition")
    join_filter_definition: Optional["str"] = Field(None, alias="joinFilterDefinition")
    creation_date_column: Optional["str"] = Field(None, alias="creationDateColumn")
    creation_date_value_start: Optional["str"] = Field(None, alias="creationDateValueStart")
    creation_date_value_end: Optional["str"] = Field(None, alias="creationDateValueEnd")
    creation_date_parameter_start: Optional["str"] = Field(None, alias="creationDateParameterStart")
    creation_date_parameter_end: Optional["str"] = Field(None, alias="creationDateParameterEnd")
    creation_date_value_today: Optional["bool"] = Field(None, alias="creationDateValueToday")
    change_date_column: Optional["str"] = Field(None, alias="changeDateColumn")
    change_date_offset: Optional["int"] = Field(None, alias="changeDateOffset")
    change_date_offset_type: Optional["ChangeDateOffsetType"] = Field(None, alias="changeDateOffsetType")
    parent_table: Optional["str"] = Field(None, alias="parentTable")
    depends_on: Optional["str"] = Field(None, alias="dependsOn")
    use_column_value_filter: Optional["bool"] = Field(None, alias="useColumnValueFilter")
    column_value_table: Optional["str"] = Field(None, alias="columnValueTable")
    column_value_column: Optional["str"] = Field(None, alias="columnValueColumn")
    column_value_target_column: Optional["str"] = Field(None, alias="columnValueTargetColumn")
    column_values_at_a_time: Optional["int"] = Field(None, alias="columnValuesAtATime")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    end_date_disabled: Optional["bool"] = Field(None, alias="endDateDisabled")
    disable_change_log: Optional["bool"] = Field(None, alias="disableChangeLog")
    data_push_delete_strategy: Optional["DataPushDeleteStrategy"] = Field(None, alias="dataPushDeleteStrategy")
    customize_column_selection: Optional["bool"] = Field(None, alias="customizeColumnSelection")
    serialized_connector_specific_configuration: Optional["str"] = Field(
        None, alias="serializedConnectorSpecificConfiguration"
    )
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class TableExtractionCalculatedColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    table_extraction_id: Optional["str"] = Field(None, alias="tableExtractionId")
    name: Optional["str"] = Field(None, alias="name")
    expression: Optional["str"] = Field(None, alias="expression")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class TableExtractionColumn(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    table_extraction_id: Optional["str"] = Field(None, alias="tableExtractionId")
    column_name: Optional["str"] = Field(None, alias="columnName")
    from_join: Optional["bool"] = Field(None, alias="fromJoin")
    anonymized: Optional["bool"] = Field(None, alias="anonymized")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    preferred_type: Optional["str"] = Field(None, alias="preferredType")
    date_format: Optional["str"] = Field(None, alias="dateFormat")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class TableExtractionJoin(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    table_extraction_id: Optional["str"] = Field(None, alias="tableExtractionId")
    parent_table: Optional["str"] = Field(None, alias="parentTable")
    child_table: Optional["str"] = Field(None, alias="childTable")
    use_primary_keys: Optional["bool"] = Field(None, alias="usePrimaryKeys")
    custom_join_path: Optional["str"] = Field(None, alias="customJoinPath")
    join_filter: Optional["str"] = Field(None, alias="joinFilter")
    order: Optional["int"] = Field(None, alias="order")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class Task(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    transformation_statement: Optional["str"] = Field(None, alias="transformationStatement")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class TaskInstance(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    published: Optional["bool"] = Field(None, alias="published")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    serialized_configuration: Optional["str"] = Field(None, alias="serializedConfiguration")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class Variable(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    name: Optional["str"] = Field(None, alias="name")
    placeholder: Optional["str"] = Field(None, alias="placeholder")
    description: Optional["str"] = Field(None, alias="description")
    type_: Optional["VariableType"] = Field(None, alias="type")
    data_type: Optional["FilterParserDataType"] = Field(None, alias="dataType")
    dynamic_variable_op_type: Optional["DynamicVariableOpType"] = Field(None, alias="dynamicVariableOpType")
    dynamic_table: Optional["str"] = Field(None, alias="dynamicTable")
    dynamic_column: Optional["str"] = Field(None, alias="dynamicColumn")
    dynamic_data_source_id: Optional["str"] = Field(None, alias="dynamicDataSourceId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class VariableDefaultSettings(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    variable_id: Optional["str"] = Field(None, alias="variableId")
    pool_variable_id: Optional["str"] = Field(None, alias="poolVariableId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class VariableDefaultValue(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    variable_id: Optional["str"] = Field(None, alias="variableId")
    value: Optional["str"] = Field(None, alias="value")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class VariableSettings(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    variable_id: Optional["str"] = Field(None, alias="variableId")
    task_instance_id: Optional["str"] = Field(None, alias="taskInstanceId")
    pool_variable_id: Optional["str"] = Field(None, alias="poolVariableId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class VariableValue(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    variable_id: Optional["str"] = Field(None, alias="variableId")
    task_instance_id: Optional["str"] = Field(None, alias="taskInstanceId")
    value: Optional["str"] = Field(None, alias="value")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class VersionedObject(PythonCoreBaseModel):
    object_key: Optional["str"] = Field(None, alias="objectKey")
    translation_key: Optional["str"] = Field(None, alias="translationKey")
    inner_versioned_objects: Optional["List[Optional[VersionedObject]]"] = Field(None, alias="innerVersionedObjects")
    json_content: Optional["str"] = Field(None, alias="jsonContent")
    schema_version: Optional["int"] = Field(None, alias="schemaVersion")


class CommitVersionTransport(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    commit_message: Optional["str"] = Field(None, alias="commitMessage")
    version: Optional["str"] = Field(None, alias="version")


class MoveDataPoolRequest(PythonCoreBaseModel):
    move_to_domain: Optional["str"] = Field(None, alias="moveToDomain")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    subset_of_data_models: Optional["bool"] = Field(None, alias="subsetOfDataModels")
    selected_data_models: Optional["List[Optional[str]]"] = Field(None, alias="selectedDataModels")


class AccessControlEntryTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    parent_object_id: Optional["str"] = Field(None, alias="parentObjectId")
    object_description: Optional["str"] = Field(None, alias="objectDescription")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    service_description: Optional["str"] = Field(None, alias="serviceDescription")
    subject_id: Optional["str"] = Field(None, alias="subjectId")
    subject_type: Optional["AccessControlEntrySubjectType"] = Field(None, alias="subjectType")
    subject_description: Optional["str"] = Field(None, alias="subjectDescription")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    auth_entity_id: Optional["str"] = Field(None, alias="authEntityId")


class ConnectorStatus(PythonCoreBaseModel):
    configuration_valid: Optional["bool"] = Field(None, alias="configurationValid")
    message: Optional["str"] = Field(None, alias="message")
    translated_connector_message: Optional["TranslatedConnectorMessage"] = Field(
        None, alias="translatedConnectorMessage"
    )
    reachable: Optional["bool"] = Field(None, alias="reachable")
    schema_reachable: Optional["bool"] = Field(None, alias="schemaReachable")
    warning_message: Optional["TranslatedConnectorMessage"] = Field(None, alias="warningMessage")
    steps: Optional["List[Optional[ConnectorStatusStep]]"] = Field(None, alias="steps")


class ConnectorStatusStep(PythonCoreBaseModel):
    name: Optional["TranslatedConnectorMessage"] = Field(None, alias="name")
    result: Optional["ConnectorStatusStepResult"] = Field(None, alias="result")


class DataPoolInstallReport(PythonCoreBaseModel):
    data_pool: Optional["DataPoolTransport"] = Field(None, alias="dataPool")
    data_source_id_mapping: Optional["Dict[str, Optional[str]]"] = Field(None, alias="dataSourceIdMapping")
    data_model_list: Optional["List[Optional[DataModel]]"] = Field(None, alias="dataModelList")


class InstallProcessRequest(PythonCoreBaseModel):
    content_store_id: Optional["str"] = Field(None, alias="contentStoreId")
    target_process_id: Optional["str"] = Field(None, alias="targetProcessId")
    skip_configure_data_source: Optional["bool"] = Field(None, alias="skipConfigureDataSource")
    selected_data_source_id: Optional["str"] = Field(None, alias="selectedDataSourceId")
    type_: Optional["HybridPoolProviderType"] = Field(None, alias="type")
    custom_data_pool_configuration: Optional["CustomDataPoolConfigurationTransport"] = Field(
        None, alias="customDataPoolConfiguration"
    )
    subset_of_data_models: Optional["bool"] = Field(None, alias="subsetOfDataModels")
    selected_data_models: Optional["List[Optional[str]]"] = Field(None, alias="selectedDataModels")
    config: Optional["DatabaseConnectionConfigurationTransport"] = Field(None, alias="config")


class FrontendLogTransport(PythonCoreBaseModel):
    stacktrace: Optional["str"] = Field(None, alias="stacktrace")
    url: Optional["str"] = Field(None, alias="url")


class CloneRequestTransport(PythonCoreBaseModel):
    source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="sourceTeams")


class TeamSlimTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    domain: Optional["str"] = Field(None, alias="domain")
    clone_data: Optional["bool"] = Field(None, alias="cloneData")


class CloneResultTransport(PythonCoreBaseModel):
    cloned_source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="clonedSourceTeams")
    failed_source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="failedSourceTeams")


class EraserLogMessageTransport(PythonCoreBaseModel):
    team_id: Optional["str"] = Field(None, alias="teamId")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    message: Optional["str"] = Field(None, alias="message")


class StreamingExecutionLogTransport(PythonCoreBaseModel):
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    execution_message: Optional["ExecutionLogTransport"] = Field(None, alias="executionMessage")
    log_level: Optional["LogLevel"] = Field(None, alias="logLevel")


class CpmNameMappingTransport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    identifier: Optional["str"] = Field(None, alias="identifier")
    translation: Optional["str"] = Field(None, alias="translation")
    language: Optional["str"] = Field(None, alias="language")
    description: Optional["str"] = Field(None, alias="description")
    type_: Optional["str"] = Field(None, alias="type")


class CpmNameMappings(PythonCoreBaseModel):
    column_mappings: Optional["List[Optional[CpmNameMappingTransport]]"] = Field(None, alias="columnMappings")
    table_mappings: Optional["List[Optional[CpmNameMappingTransport]]"] = Field(None, alias="tableMappings")
    general_mappings: Optional["List[Optional[CpmNameMappingTransport]]"] = Field(None, alias="generalMappings")


class SanitizeComputeNodesRequestTransport(PythonCoreBaseModel):
    compute_node_url: Optional["str"] = Field(None, alias="computeNodeUrl")
    team_ids: Optional["List[Optional[str]]"] = Field(None, alias="teamIds")


class DataModelExport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_name: Optional["str"] = Field(None, alias="dataModelName")
    data_model_calendar_type: Optional["DataModelCalendarType"] = Field(None, alias="dataModelCalendarType")
    configuration: Optional["DataModelConfiguration"] = Field(None, alias="configuration")
    configurations: Optional["List[Optional[DataModelConfiguration]]"] = Field(None, alias="configurations")
    tables: Optional["List[Optional[DataModelTable]]"] = Field(None, alias="tables")
    columns: Optional["List[Optional[DataModelTableColumn]]"] = Field(None, alias="columns")
    foreign_key_exports: Optional["List[Optional[DataModelForeignKeyExport]]"] = Field(None, alias="foreignKeyExports")
    custom_calendar_entries: Optional["List[Optional[DataModelCustomCalendarEntry]]"] = Field(
        None, alias="customCalendarEntries"
    )
    factory_calendars: Optional["List[Optional[DataModelFactoryCalendar]]"] = Field(None, alias="factoryCalendars")
    signal_links: Optional["List[Optional[DataModelSignalLinkTransport]]"] = Field(None, alias="signalLinks")
    eventlog_automerge_enabled: Optional["bool"] = Field(None, alias="eventlogAutomergeEnabled")
    auto_merge_execution_mode: Optional["AutoMergeExecutionMode"] = Field(None, alias="autoMergeExecutionMode")
    linearization_enabled: Optional["bool"] = Field(None, alias="linearizationEnabled")
    version_number: Optional["int"] = Field(None, alias="versionNumber")


class DataModelForeignKeyExport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    source_table_id: Optional["str"] = Field(None, alias="sourceTableId")
    target_table_id: Optional["str"] = Field(None, alias="targetTableId")
    foreign_key_columns: Optional["List[Optional[DataModelForeignKeyColumn]]"] = Field(None, alias="foreignKeyColumns")


class DataPoolExport(PythonCoreBaseModel):
    data_pool: Optional["DataPoolTransport"] = Field(None, alias="dataPool")
    data_sources: Optional["List[Optional[DataSourceTransport]]"] = Field(None, alias="dataSources")
    jobs: Optional["List[Optional[JobTransport]]"] = Field(None, alias="jobs")
    schedules: Optional["List[Optional[SchedulingTransport]]"] = Field(None, alias="schedules")
    scheduling_triggers: Optional["List[Optional[SchedulingTriggerTransport]]"] = Field(
        None, alias="schedulingTriggers"
    )
    job_schedules: Optional["List[Optional[JobSchedulingTransport]]"] = Field(None, alias="jobSchedules")
    extractions: Optional["List[Optional[ExtractionWithTablesTransport]]"] = Field(None, alias="extractions")
    transformations: Optional["List[Optional[TransformationTransport]]"] = Field(None, alias="transformations")
    pool_variables: Optional["List[Optional[PoolVariableTransport]]"] = Field(None, alias="poolVariables")
    task_variables: Optional["List[Optional[TaskVariableTransport]]"] = Field(None, alias="taskVariables")
    data_models: Optional["List[Optional[DataModelExport]]"] = Field(None, alias="dataModels")
    replication_data_source_configurations: Optional["ReplicationDataSourceConfigurationsExport"] = Field(
        None, alias="replicationDataSourceConfigurations"
    )
    replication_configurations: Optional["List[Optional[ReplicationConfigurationTransport]]"] = Field(
        None, alias="replicationConfigurations"
    )
    data_model_executions: Optional["List[Optional[DataModelExecutionTransport]]"] = Field(
        None, alias="dataModelExecutions"
    )
    execution_items: Optional["List[Optional[ExecutionItemTransport]]"] = Field(None, alias="executionItems")
    log_messages: Optional["List[Optional[LogMessageTransport]]"] = Field(None, alias="logMessages")
    custom_extractor_transports: Optional["List[Optional[CustomExtractorTransport]]"] = Field(
        None, alias="customExtractorTransports"
    )
    version_number: Optional["int"] = Field(None, alias="versionNumber")


class DataPoolImportRequest(PythonCoreBaseModel):
    data_pool_export: Optional["DataPoolExport"] = Field(None, alias="dataPoolExport")
    to_data_pool: Optional["DataPoolTransport"] = Field(None, alias="toDataPool")
    selected_data_source_id: Optional["str"] = Field(None, alias="selectedDataSourceId")
    subset_of_data_models: Optional["bool"] = Field(None, alias="subsetOfDataModels")
    selected_data_models: Optional["List[Optional[str]]"] = Field(None, alias="selectedDataModels")
    remove_not_supported_data_source: Optional["bool"] = Field(None, alias="removeNotSupportedDataSource")
    include_executions: Optional["bool"] = Field(None, alias="includeExecutions")
    set_original_id: Optional["bool"] = Field(None, alias="setOriginalId")
    skip_permissions: Optional["bool"] = Field(None, alias="skipPermissions")
    skip_license_check: Optional["bool"] = Field(None, alias="skipLicenseCheck")
    include_data_source_configurations: Optional["bool"] = Field(None, alias="includeDataSourceConfigurations")


class ExecutionItemTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    pool_name: Optional["str"] = Field(None, alias="poolName")
    execution_id: Optional["str"] = Field(None, alias="executionId")
    scheduling_id: Optional["str"] = Field(None, alias="schedulingId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    step_id: Optional["str"] = Field(None, alias="stepId")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    data_pool_version: Optional["str"] = Field(None, alias="dataPoolVersion")
    start_date: Optional["PythonCoreDatetime"] = Field(None, alias="startDate")
    end_date: Optional["PythonCoreDatetime"] = Field(None, alias="endDate")
    type_: Optional["ExecutionType"] = Field(None, alias="type")
    mode: Optional["ExtractionMode"] = Field(None, alias="mode")
    scheduling_name: Optional["str"] = Field(None, alias="schedulingName")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    monitored: Optional["bool"] = Field(None, alias="monitored")


class LogMessageTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    level: Optional["LogLevel"] = Field(None, alias="level")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    log_message: Optional["str"] = Field(None, alias="logMessage")
    log_translation_code: Optional["str"] = Field(None, alias="logTranslationCode")
    log_translation_parameters: Optional["List[Optional[LogTranslationParameter]]"] = Field(
        None, alias="logTranslationParameters"
    )


class ReplicationCalculatedColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    replication_id: Optional["str"] = Field(None, alias="replicationId")
    expression: Optional["str"] = Field(None, alias="expression")
    column_name: Optional["str"] = Field(None, alias="columnName")


class ReplicationColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    replication_id: Optional["str"] = Field(None, alias="replicationId")
    column_name: Optional["str"] = Field(None, alias="columnName")
    anonymized: Optional["bool"] = Field(None, alias="anonymized")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")
    mandatory_primary_key: Optional["bool"] = Field(None, alias="mandatoryPrimaryKey")


class ReplicationConfigurationTransport(PythonCoreBaseModel):
    replication: Optional["ReplicationTransport"] = Field(None, alias="replication")
    replication_columns: Optional["List[Optional[ReplicationColumnTransport]]"] = Field(
        None, alias="replicationColumns"
    )
    replication_calculated_columns: Optional["List[Optional[ReplicationCalculatedColumnTransport]]"] = Field(
        None, alias="replicationCalculatedColumns"
    )
    replication_dependencies: Optional["List[Optional[ReplicationDependencyTransport]]"] = Field(
        None, alias="replicationDependencies"
    )
    replication_transformations: Optional["List[Optional[ReplicationTransformationTransport]]"] = Field(
        None, alias="replicationTransformations"
    )
    replication_joins: Optional["List[Optional[ReplicationJoinTransport]]"] = Field(None, alias="replicationJoins")


class ReplicationDataSourceConfigurationsExport(PythonCoreBaseModel):
    initialization_scripts: Optional["List[Optional[ReplicationInitializationScriptTransport]]"] = Field(
        None, alias="initializationScripts"
    )


class ReplicationDependencyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    replication_id: Optional["str"] = Field(None, alias="replicationId")
    dependent_replication_id: Optional["str"] = Field(None, alias="dependentReplicationId")
    table_name: Optional["str"] = Field(None, alias="tableName")


class ReplicationInitializationScriptTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    statement: Optional["str"] = Field(None, alias="statement")


class ReplicationJoinTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    replication_id: Optional["str"] = Field(None, alias="replicationId")
    parent_table: Optional["str"] = Field(None, alias="parentTable")
    parent_schema: Optional["str"] = Field(None, alias="parentSchema")
    child_table: Optional["str"] = Field(None, alias="childTable")
    use_primary_keys: Optional["bool"] = Field(None, alias="usePrimaryKeys")
    custom_join_path: Optional["str"] = Field(None, alias="customJoinPath")
    join_filter: Optional["str"] = Field(None, alias="joinFilter")
    order: Optional["int"] = Field(None, alias="order")


class ReplicationTransformationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    replication_id: Optional["str"] = Field(None, alias="replicationId")
    statement: Optional["str"] = Field(None, alias="statement")
    order: Optional["int"] = Field(None, alias="order")
    disabled: Optional["bool"] = Field(None, alias="disabled")


class ReplicationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    table_name: Optional["str"] = Field(None, alias="tableName")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    status: Optional["ReplicationStatus"] = Field(None, alias="status")
    rename_target_table: Optional["bool"] = Field(None, alias="renameTargetTable")
    custom_target_table_name: Optional["str"] = Field(None, alias="customTargetTableName")
    filter_statement: Optional["str"] = Field(None, alias="filterStatement")
    type_: Optional["ReplicationType"] = Field(None, alias="type")
    debug_mode_until: Optional["PythonCoreDatetime"] = Field(None, alias="debugModeUntil")
    connector_specific_configuration: Optional["List[Optional[TableConfigurationParameterValue]]"] = Field(
        None, alias="connectorSpecificConfiguration"
    )
    data_push_delete_strategy: Optional["DataPushDeleteStrategy"] = Field(None, alias="dataPushDeleteStrategy")
    latest_status_change: Optional["PythonCoreDatetime"] = Field(None, alias="latestStatusChange")
    cl_override_enabled: Optional["bool"] = Field(None, alias="clOverrideEnabled")
    cl_override_table_name: Optional["str"] = Field(None, alias="clOverrideTableName")


class SchedulingTriggerTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    scheduling_id: Optional["str"] = Field(None, alias="schedulingId")
    triggering_scheduling_id: Optional["str"] = Field(None, alias="triggeringSchedulingId")


class DataPoolProviderColumn(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    column_type: Optional["DataPoolProviderColumnType"] = Field(None, alias="columnType")
    field_length: Optional["int"] = Field(None, alias="fieldLength")
    decimals: Optional["int"] = Field(None, alias="decimals")
    pk_field: Optional["bool"] = Field(None, alias="pkField")


class PoolProviderQueryTransport(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    query_type: Optional["PoolProviderQueryType"] = Field(None, alias="queryType")


class SelectExpression(PythonCoreBaseModel):
    expression_type: Optional["SelectExpressionType"] = Field(None, alias="expressionType")


class PoolProviderQueryResultTransport(PythonCoreBaseModel):
    affected_rows: Optional["int"] = Field(None, alias="affectedRows")
    table_content: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="tableContent")
    columns: Optional["List[Optional[DataPoolProviderColumn]]"] = Field(None, alias="columns")


class PoolProviderCredentialsTransport(PythonCoreBaseModel):
    team_id: Optional["str"] = Field(None, alias="teamId")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    last_access: Optional["PythonCoreDatetime"] = Field(None, alias="lastAccess")


class PoolProviderAssignmentTransport(PythonCoreBaseModel):
    pool_provider_id: Optional["str"] = Field(None, alias="poolProviderId")


class DataPoolImportReportTransport(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    data_model_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataModelIds")


class ObjectStorageBucketAssignmentTransport(PythonCoreBaseModel):
    object_storage_bucket_id: Optional["str"] = Field(None, alias="objectStorageBucketId")


class ComputeVersionRequest(PythonCoreBaseModel):
    compute_node_url: Optional["str"] = Field(None, alias="computeNodeUrl")


class AcceleratorVersion(PythonCoreBaseModel):
    major: Optional["int"] = Field(None, alias="major")
    minor: Optional["int"] = Field(None, alias="minor")
    patch: Optional["int"] = Field(None, alias="patch")
    revision: Optional["str"] = Field(None, alias="revision")


class DataModelLoadStatusUpdateMessage(PythonCoreBaseModel):
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    execution_type: Optional["ExecutionType"] = Field(None, alias="executionType")
    execution_status: Optional["ExecutionStatus"] = Field(None, alias="executionStatus")
    step_name: Optional["str"] = Field(None, alias="stepName")
    message: Optional["str"] = Field(None, alias="message")
    row_counts: Optional["List[Optional[DataModelTableRowCountTransport]]"] = Field(None, alias="rowCounts")
    user_error: Optional["bool"] = Field(None, alias="userError")


class DataModelTableRowCountTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    row_count: Optional["int"] = Field(None, alias="rowCount")


class ResolveParameterRequestBody(PythonCoreBaseModel):
    placeholders: Optional["List[Optional[str]]"] = Field(None, alias="placeholders")
    default_for_dynamic: Optional["bool"] = Field(None, alias="defaultForDynamic")


class FilterVariableValue(PythonCoreBaseModel):
    type_: Optional["FilterParserDataType"] = Field(None, alias="type")
    value: Optional["Any"] = Field(None, alias="value")


class FilterVariableValueMap(PythonCoreBaseModel):
    empty: Optional["bool"] = Field(None, alias="empty")


class DynamicDataPoolParameterTransport(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    data_type: Optional["str"] = Field(None, alias="dataType")
    default_value: Optional["str"] = Field(None, alias="defaultValue")


class DataQueryResultColumn(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["DataQueryColumnType"] = Field(None, alias="type")


class DataQueryResultTable(PythonCoreBaseModel):
    affected_rows: Optional["int"] = Field(None, alias="affectedRows")
    table_content: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="tableContent")
    columns: Optional["List[Optional[DataQueryResultColumn]]"] = Field(None, alias="columns")


class DataQueryTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    start_date: Optional["PythonCoreDatetime"] = Field(None, alias="startDate")
    end_date: Optional["PythonCoreDatetime"] = Field(None, alias="endDate")
    error: Optional["str"] = Field(None, alias="error")
    result: Optional["DataQueryResultTable"] = Field(None, alias="result")


class DeltaFilterTransformationOptions(PythonCoreBaseModel):
    delta_transformation_filter_column: Optional["str"] = Field(None, alias="deltaTransformationFilterColumn")
    delta_transformation_filter_value: Optional["str"] = Field(None, alias="deltaTransformationFilterValue")
    delta_transformation_custom_condition: Optional["str"] = Field(None, alias="deltaTransformationCustomCondition")


class TransformationOptions(PythonCoreBaseModel):
    source_table_name: Optional["str"] = Field(None, alias="sourceTableName")
    new_data_table_name: Optional["str"] = Field(None, alias="newDataTableName")
    transformation_view_name: Optional["str"] = Field(None, alias="transformationViewName")
    transformation_partitioning_options: Optional["TransformationPartitioningOptions"] = Field(
        None, alias="transformationPartitioningOptions"
    )
    delta_filter_transformation_options: Optional["DeltaFilterTransformationOptions"] = Field(
        None, alias="deltaFilterTransformationOptions"
    )


class TransformationPartitioningOptions(PythonCoreBaseModel):
    partition_column_name: Optional["str"] = Field(None, alias="partitionColumnName")
    partition_size_override: Optional["int"] = Field(None, alias="partitionSizeOverride")


class TransformationRequestTransport(PythonCoreBaseModel):
    query: Optional["str"] = Field(None, alias="query")
    transformation_options: Optional["TransformationOptions"] = Field(None, alias="transformationOptions")
    transformation_resource_pool: Optional["TransformationResourcePool"] = Field(
        None, alias="transformationResourcePool"
    )


class LiveDataModelsRequestTransport(PythonCoreBaseModel):
    data_model_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataModelIds")


class CcmmTableInfo(PythonCoreBaseModel):
    table_type: Optional["CcmmTableType"] = Field(None, alias="tableType")


class CustomCalendar(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    selected: Optional["bool"] = Field(None, alias="selected")
    start_time: Optional["int"] = Field(None, alias="startTime")
    end_time: Optional["int"] = Field(None, alias="endTime")


class DataColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    short_name: Optional["str"] = Field(None, alias="shortName")
    description: Optional["str"] = Field(None, alias="description")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    selected: Optional["bool"] = Field(None, alias="selected")
    active: Optional["bool"] = Field(None, alias="active")


class DataModelEngineTransport(PythonCoreBaseModel):
    loaded: Optional["bool"] = Field(None, alias="loaded")
    allow_raw_data_export: Optional["bool"] = Field(None, alias="allowRawDataExport")
    team_id: Optional["str"] = Field(None, alias="teamId")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    case_id_column_id: Optional["str"] = Field(None, alias="caseIdColumnId")
    case_table_id: Optional["str"] = Field(None, alias="caseTableId")
    activity_table_id: Optional["str"] = Field(None, alias="activityTableId")
    tables: Optional["List[Optional[DataTableTransport]]"] = Field(None, alias="tables")
    foreign_keys: Optional["List[Optional[ForeignKeyTransport]]"] = Field(None, alias="foreignKeys")
    data_model_load: Optional["DataModelLoadTransport"] = Field(None, alias="dataModelLoad")
    custom_calendar: Optional["List[Optional[CustomCalendar]]"] = Field(None, alias="customCalendar")
    general_translations: Optional["List[Optional[NameMappingTransport]]"] = Field(None, alias="generalTranslations")
    name_mapping_enabled: Optional["bool"] = Field(None, alias="nameMappingEnabled")


class DataModelLoadTableTransport(PythonCoreBaseModel):
    table_id: Optional["str"] = Field(None, alias="tableId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    table_row_count: Optional["int"] = Field(None, alias="tableRowCount")
    done: Optional["bool"] = Field(None, alias="done")
    invisible: Optional["bool"] = Field(None, alias="invisible")
    cancel: Optional["bool"] = Field(None, alias="cancel")


class DataModelLoadTransport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_model_name: Optional["str"] = Field(None, alias="dataModelName")
    done: Optional["bool"] = Field(None, alias="done")
    error: Optional["bool"] = Field(None, alias="error")
    tables_loaded: Optional["bool"] = Field(None, alias="tablesLoaded")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    last_load: Optional["PythonCoreDatetime"] = Field(None, alias="lastLoad")
    project_name: Optional["str"] = Field(None, alias="projectName")
    next_load: Optional["PythonCoreDatetime"] = Field(None, alias="nextLoad")
    data_model_uuid: Optional["str"] = Field(None, alias="dataModelUUID")
    num_tables: Optional["int"] = Field(None, alias="numTables")
    scheduled_loading: Optional["bool"] = Field(None, alias="scheduledLoading")
    cancel: Optional["bool"] = Field(None, alias="cancel")
    table_loads: Optional["List[Optional[DataModelLoadTableTransport]]"] = Field(None, alias="tableLoads")
    start_time: Optional["PythonCoreDatetime"] = Field(None, alias="startTime")
    end_time: Optional["PythonCoreDatetime"] = Field(None, alias="endTime")
    response: Optional["str"] = Field(None, alias="response")
    data_load_id: Optional["str"] = Field(None, alias="dataLoadId")


class DataTableConfigurationTransport(PythonCoreBaseModel):
    type_: Optional["TableType"] = Field(None, alias="type")
    ccmm_table_info: Optional["CcmmTableInfo"] = Field(None, alias="ccmmTableInfo")
    activity_column_id: Optional["str"] = Field(None, alias="activityColumnId")
    case_id_column_id: Optional["str"] = Field(None, alias="caseIdColumnId")
    timestamp_column_id: Optional["str"] = Field(None, alias="timestampColumnId")
    end_timestamp_column_id: Optional["str"] = Field(None, alias="endTimestampColumnId")
    cost_column_id: Optional["str"] = Field(None, alias="costColumnId")
    user_column_id: Optional["str"] = Field(None, alias="userColumnId")
    location_column_id: Optional["str"] = Field(None, alias="locationColumnId")
    sorting_columns: Optional["List[Optional[str]]"] = Field(None, alias="sortingColumns")
    case_table_name: Optional["str"] = Field(None, alias="caseTableName")
    default_event_table: Optional["bool"] = Field(None, alias="defaultEventTable")


class DataTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    short_name: Optional["str"] = Field(None, alias="shortName")
    description: Optional["str"] = Field(None, alias="description")
    table_configuration: Optional["DataTableConfigurationTransport"] = Field(None, alias="tableConfiguration")
    columns: Optional["List[Optional[DataColumnTransport]]"] = Field(None, alias="columns")
    generated: Optional["bool"] = Field(None, alias="generated")
    augmentation: Optional["bool"] = Field(None, alias="augmentation")


class ForeignKeyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    dimension_table_name: Optional["str"] = Field(None, alias="dimensionTableName")
    dimensional_table_columns: Optional["List[Optional[str]]"] = Field(None, alias="dimensionalTableColumns")
    fact_table_name: Optional["str"] = Field(None, alias="factTableName")
    fact_table_columns: Optional["List[Optional[str]]"] = Field(None, alias="factTableColumns")
    unknown_direction: Optional["bool"] = Field(None, alias="unknownDirection")
    table1_id: Optional["str"] = Field(None, alias="table1Id")
    column1_id_list: Optional["List[Optional[str]]"] = Field(None, alias="column1IdList")
    table2_id: Optional["str"] = Field(None, alias="table2Id")
    column2_id_list: Optional["List[Optional[str]]"] = Field(None, alias="column2IdList")


class LiveDataModelsResponseTransport(PythonCoreBaseModel):
    live_data_models: Optional["List[Optional[DataModelEngineTransport]]"] = Field(None, alias="liveDataModels")


class NameMappingTransport(PythonCoreBaseModel):
    identifier: Optional["str"] = Field(None, alias="identifier")
    translation: Optional["str"] = Field(None, alias="translation")
    language: Optional["str"] = Field(None, alias="language")
    description: Optional["str"] = Field(None, alias="description")
    mapping_type: Optional["str"] = Field(None, alias="mappingType")


class PostMultiQueryTransport(PythonCoreBaseModel):
    request: Optional["DataCommand"] = Field(None, alias="request")
    query_environment: Optional["QueryEnvironment"] = Field(None, alias="queryEnvironment")


class AcceleratorSelectionFilter(PythonCoreBaseModel):
    default_inactive: Optional["bool"] = Field(None, alias="defaultInactive")
    kind: Optional["AcceleratorSelectionKind"] = Field(None, alias="kind")
    expression: Optional["str"] = Field(None, alias="expression")
    type_: Optional["AcceleratorSelectionType"] = Field(None, alias="type")
    enabled: Optional["bool"] = Field(None, alias="enabled")
    null_selected: Optional["bool"] = Field(None, alias="nullSelected")
    entries_selected: Optional["int"] = Field(None, alias="entriesSelected")
    entries_total: Optional["int"] = Field(None, alias="entriesTotal")
    values_total: Optional["int"] = Field(None, alias="valuesTotal")
    values_selected: Optional["int"] = Field(None, alias="valuesSelected")
    cases_total: Optional["int"] = Field(None, alias="casesTotal")
    cases_selected: Optional["int"] = Field(None, alias="casesSelected")
    table_name: Optional["str"] = Field(None, alias="tableName")
    data_type: Optional["AcceleratorSelectionType"] = Field(None, alias="dataType")
    configuration: Optional["Any"] = Field(None, alias="configuration")
    pinned: Optional["bool"] = Field(None, alias="pinned")
    temporary: Optional["bool"] = Field(None, alias="temporary")
    id: Optional["str"] = Field(None, alias="id")
    position: Optional["int"] = Field(None, alias="position")
    volatile_filter: Optional["bool"] = Field(None, alias="volatileFilter")
    name: Optional["str"] = Field(None, alias="name")
    format: Optional["str"] = Field(None, alias="format")
    first_selected_values: Optional["List[Optional[str]]"] = Field(None, alias="firstSelectedValues")
    first_non_selected_values: Optional["List[Optional[str]]"] = Field(None, alias="firstNonSelectedValues")


class AcceleratorTableStatistics(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    table_count: Optional["int"] = Field(None, alias="tableCount")
    filtered_count: Optional["int"] = Field(None, alias="filteredCount")
    case_table: Optional["bool"] = Field(None, alias="caseTable")
    activity_table: Optional["bool"] = Field(None, alias="activityTable")


class ExplainNode(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    input_nodes: Optional["List[Optional[ExplainNode]]"] = Field(None, alias="inputNodes")


class MessageTransport(PythonCoreBaseModel):
    translation_code: Optional["str"] = Field(None, alias="translationCode")
    parameters: Optional["List[Optional[TranslationParameter]]"] = Field(None, alias="parameters")


class MissingColumnInfo(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    table_name: Optional["str"] = Field(None, alias="tableName")
    potential_meant_columns: Optional["List[Optional[str]]"] = Field(None, alias="potentialMeantColumns")


class PqlCompilationExceptionTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")


class PqlMultiResultTransport(PythonCoreBaseModel):
    components: Optional["Dict[str, Optional[PqlResultTransport]]"] = Field(None, alias="components")
    selections: Optional["List[Optional[AcceleratorSelectionFilter]]"] = Field(None, alias="selections")
    table_statistics: Optional["List[Optional[AcceleratorTableStatistics]]"] = Field(None, alias="tableStatistics")
    message: Optional["str"] = Field(None, alias="message")
    error_messages: Optional["List[Optional[MessageTransport]]"] = Field(None, alias="errorMessages")
    pql_compilation_exception: Optional["PqlCompilationExceptionTransport"] = Field(
        None, alias="pqlCompilationException"
    )
    pql_syntax_exception: Optional["PqlSyntaxExceptionTransport"] = Field(None, alias="pqlSyntaxException")
    pql_token_manager_exception: Optional["PqlTokenManagerExceptionTransport"] = Field(
        None, alias="pqlTokenManagerException"
    )
    missing_columns: Optional["Dict[str, Optional[List[Optional[MissingColumnInfo]]]]"] = Field(
        None, alias="missingColumns"
    )


class PqlResultQueryStatistics(PythonCoreBaseModel):
    query_execution_time_ms: Optional["int"] = Field(None, alias="queryExecutionTimeMs")
    query_compile_time_ms: Optional["int"] = Field(None, alias="queryCompileTimeMs")
    query_result_size_in_bytes: Optional["int"] = Field(None, alias="queryResultSizeInBytes")


class PqlResultTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")
    error_messages: Optional["List[Optional[MessageTransport]]"] = Field(None, alias="errorMessages")
    warnings: Optional["List[Optional[str]]"] = Field(None, alias="warnings")
    warning_messages: Optional["List[Optional[MessageTransport]]"] = Field(None, alias="warningMessages")
    result_index: Optional["Dict[str, Optional[int]]"] = Field(None, alias="resultIndex")
    results: Optional["List[Optional[TableResult]]"] = Field(None, alias="results")
    query_statistics: Optional["PqlResultQueryStatistics"] = Field(None, alias="queryStatistics")
    load_version: Optional["str"] = Field(None, alias="loadVersion")
    augmentation_table_used: Optional["bool"] = Field(None, alias="augmentationTableUsed")


class PqlSyntaxExceptionTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")
    token: Optional["str"] = Field(None, alias="token")
    begin_column: Optional["int"] = Field(None, alias="beginColumn")
    begin_line: Optional["int"] = Field(None, alias="beginLine")
    end_column: Optional["int"] = Field(None, alias="endColumn")
    end_line: Optional["int"] = Field(None, alias="endLine")


class PqlTokenManagerExceptionTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")


class TableMetaData(PythonCoreBaseModel):
    column_name: Optional["str"] = Field(None, alias="columnName")
    column_type: Optional["str"] = Field(None, alias="columnType")
    expression_lhs: Optional["str"] = Field(None, alias="expressionLhs")
    format: Optional["str"] = Field(None, alias="format")


class TableResult(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    utc_timestamps: Optional["bool"] = Field(None, alias="utcTimestamps")
    explain_nodes: Optional["List[Optional[ExplainNode]]"] = Field(None, alias="explainNodes")
    meta_data: Optional["List[Optional[TableMetaData]]"] = Field(None, alias="metaData")
    data: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="data")
    string_hashes: Optional["List[Optional[List[Optional[str]]]]"] = Field(None, alias="stringHashes")
    rids: Optional["List[Optional[int]]"] = Field(None, alias="rids")
    ids: Optional["List[Optional[List[Optional[int]]]]"] = Field(None, alias="ids")
    overall_count: Optional["int"] = Field(None, alias="overallCount")
    offset: Optional["int"] = Field(None, alias="offset")
    count: Optional["int"] = Field(None, alias="count")
    export_chunks: Optional["int"] = Field(None, alias="exportChunks")
    error: Optional["bool"] = Field(None, alias="error")
    message: Optional["str"] = Field(None, alias="message")
    selected: Optional["List[Optional[List[Optional[bool]]]]"] = Field(None, alias="selected")
    available: Optional["List[Optional[List[Optional[bool]]]]"] = Field(None, alias="available")
    has_others: Optional["List[Optional[bool]]"] = Field(None, alias="hasOthers")
    others: Optional["List[Optional[Any]]"] = Field(None, alias="others")
    warnings: Optional["List[Optional[str]]"] = Field(None, alias="warnings")
    common_table_name: Optional["str"] = Field(None, alias="commonTableName")


class TranslationParameter(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    value: Optional["str"] = Field(None, alias="value")


class PostMultiQueryChunkedTransport(PythonCoreBaseModel):
    request: Optional["DataCommand"] = Field(None, alias="request")
    query_environment: Optional["QueryEnvironment"] = Field(None, alias="queryEnvironment")
    limit: Optional["int"] = Field(None, alias="limit")
    offset: Optional["int"] = Field(None, alias="offset")


class DataCommandBatchTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    request: Optional["DataCommand"] = Field(None, alias="request")


class PostBatchQueryTransport(PythonCoreBaseModel):
    analysis_commands: Optional["List[Optional[DataCommandBatchTransport]]"] = Field(None, alias="analysisCommands")
    query_environment: Optional["QueryEnvironment"] = Field(None, alias="queryEnvironment")


class PqlBatchExpansionResultTransport(PythonCoreBaseModel):
    results: Optional["List[Optional[PqlMultiExpansionResultTransport]]"] = Field(None, alias="results")


class PqlMultiExpansionResultTransport(PythonCoreBaseModel):
    results: Optional["Dict[str, Optional[str]]"] = Field(None, alias="results")


class DataCommandBatchResultTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    result: Optional["PqlMultiResultTransport"] = Field(None, alias="result")


class QueryBatchResult(PythonCoreBaseModel):
    batch_results: Optional["List[Optional[DataCommandBatchResultTransport]]"] = Field(None, alias="batchResults")
    first_batch_error_optional: Optional["str"] = Field(None, alias="firstBatchErrorOptional")


class IntegrationCloneInternalTransport(PythonCoreBaseModel):
    target_team_domain: Optional["str"] = Field(None, alias="targetTeamDomain")


class IntegrationCloneResultInternalTransport(PythonCoreBaseModel):
    pass


class SnowflakeRestRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class DatabaseRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class ContactUsTransport(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")


class IntegrationCloneExternalTransport(PythonCoreBaseModel):
    target_team_domain: Optional["str"] = Field(None, alias="targetTeamDomain")


class IntegrationCloneResultExternalTransport(PythonCoreBaseModel):
    pass


class TeamTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    domain: Optional["str"] = Field(None, alias="domain")
    privacy_type: Optional["CloudTeamPrivacyType"] = Field(None, alias="privacyType")
    allowed_domain: Optional["str"] = Field(None, alias="allowedDomain")
    url: Optional["str"] = Field(None, alias="url")
    accessible_from_ip: Optional["bool"] = Field(None, alias="accessibleFromIp")
    active: Optional["bool"] = Field(None, alias="active")
    active_until: Optional["PythonCoreDatetime"] = Field(None, alias="activeUntil")
    visible: Optional["bool"] = Field(None, alias="visible")
    member_limit: Optional["int"] = Field(None, alias="memberLimit")
    analyst_limit: Optional["int"] = Field(None, alias="analystLimit")
    action_engine_user_limit: Optional["int"] = Field(None, alias="actionEngineUserLimit")
    ml_workbenches_limit: Optional["int"] = Field(None, alias="mlWorkbenchesLimit")
    table_rows_limit: Optional["int"] = Field(None, alias="tableRowsLimit")
    tracking_enabled: Optional["bool"] = Field(None, alias="trackingEnabled")
    terms_and_conditions_enabled: Optional["bool"] = Field(None, alias="termsAndConditionsEnabled")
    login_history_enabled: Optional["bool"] = Field(None, alias="loginHistoryEnabled")
    enforce_two_factor_authentication_enabled: Optional["bool"] = Field(
        None, alias="enforceTwoFactorAuthenticationEnabled"
    )
    terms_of_use_url: Optional["str"] = Field(None, alias="termsOfUseUrl")
    lms_url: Optional["str"] = Field(None, alias="lmsUrl")
    data_consumption_limit_in_gigabytes: Optional["int"] = Field(None, alias="dataConsumptionLimitInGigabytes")
    data_pool_versions_limit: Optional["int"] = Field(None, alias="dataPoolVersionsLimit")
    current_data_consumption_in_bytes: Optional["int"] = Field(None, alias="currentDataConsumptionInBytes")
    data_consumptions_last_updated_at: Optional["PythonCoreDatetime"] = Field(
        None, alias="dataConsumptionsLastUpdatedAt"
    )
    data_consumption_stage: Optional["DataConsumptionStage"] = Field(None, alias="dataConsumptionStage")
    data_transfer_hybrid_to_cloud_enabled: Optional["bool"] = Field(None, alias="dataTransferHybridToCloudEnabled")
    data_push_job_submission_limit_per_sec: Optional["int"] = Field(None, alias="dataPushJobSubmissionLimitPerSec")
    data_push_job_submission_limit_per_hour: Optional["int"] = Field(None, alias="dataPushJobSubmissionLimitPerHour")
    continuous_batch_processing_flush_interval_in_seconds: Optional["int"] = Field(
        None, alias="continuousBatchProcessingFlushIntervalInSeconds"
    )
    template: Optional["bool"] = Field(None, alias="template")
    clone_event_collection: Optional["bool"] = Field(None, alias="cloneEventCollection")
    feature_keys: Optional["List[Optional[str]]"] = Field(None, alias="featureKeys")
    permissions_management_mode: Optional["PermissionsManagementMode"] = Field(None, alias="permissionsManagementMode")
    request_date: Optional["PythonCoreDatetime"] = Field(None, alias="requestDate")
    allowed_domains: Optional["List[Optional[str]]"] = Field(None, alias="allowedDomains")
    current: Optional["bool"] = Field(None, alias="current")
    unlimited_action_engine_users: Optional["bool"] = Field(None, alias="unlimitedActionEngineUsers")
    unlimited_data_push_job_submissions: Optional["bool"] = Field(None, alias="unlimitedDataPushJobSubmissions")
    unlimited_data_pool_versions_limit: Optional["bool"] = Field(None, alias="unlimitedDataPoolVersionsLimit")
    unlimited_members: Optional["bool"] = Field(None, alias="unlimitedMembers")
    unlimited_analysts: Optional["bool"] = Field(None, alias="unlimitedAnalysts")
    unlimited_ml_workbenches: Optional["bool"] = Field(None, alias="unlimitedMlWorkbenches")
    unlimited_data_consumption: Optional["bool"] = Field(None, alias="unlimitedDataConsumption")
    unlimited_table_rows: Optional["bool"] = Field(None, alias="unlimitedTableRows")


class PageableBase(PythonCoreBaseModel):
    sort_by: Optional["str"] = Field(None, alias="sortBy")
    ascending: Optional["bool"] = Field(None, alias="ascending")
    page: Optional["int"] = Field(None, alias="page")
    limit: Optional["int"] = Field(None, alias="limit")


class PageTransportJobTransport(PythonCoreBaseModel):
    content: Optional["List[Optional[JobTransport]]"] = Field(None, alias="content")
    page_size: Optional["int"] = Field(None, alias="pageSize")
    page_number: Optional["int"] = Field(None, alias="pageNumber")
    total_count: Optional["int"] = Field(None, alias="totalCount")


class DataPushChunk(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    type_: Optional["ChunkType"] = Field(None, alias="type")
    push_job_id: Optional["str"] = Field(None, alias="pushJobId")
    checksum: Optional["str"] = Field(None, alias="checksum")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")


class DirectStorageTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class DataModelDataLoadHistoryTransport(PythonCoreBaseModel):
    data_load_id: Optional["str"] = Field(None, alias="dataLoadId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    start_date: Optional["PythonCoreDatetime"] = Field(None, alias="startDate")
    end_date: Optional["PythonCoreDatetime"] = Field(None, alias="endDate")
    load_status: Optional["DataModelLoadStatus"] = Field(None, alias="loadStatus")
    message: Optional["str"] = Field(None, alias="message")
    load_type: Optional["DataLoadType"] = Field(None, alias="loadType")
    data_pool_version: Optional["str"] = Field(None, alias="dataPoolVersion")


class TablePartitionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    table_name: Optional["str"] = Field(None, alias="tableName")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    num_partitions: Optional["int"] = Field(None, alias="numPartitions")
    max_partition: Optional["int"] = Field(None, alias="maxPartition")
    latest_partition_change: Optional["PythonCoreDatetime"] = Field(None, alias="latestPartitionChange")
    latest_load_date: Optional["PythonCoreDatetime"] = Field(None, alias="latestLoadDate")


class ReplicationCockpitServeDataTransport(PythonCoreBaseModel):
    serve_url: Optional["str"] = Field(None, alias="serveUrl")


class ReplicationCockpitOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    tables: Optional["List[Optional[ReplicationCockpitTableIdAndNameTransport]]"] = Field(None, alias="tables")
    data_source_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataSourceIds")
    count_transformations: Optional["int"] = Field(None, alias="countTransformations")


class ReplicationCockpitTableIdAndNameTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class PoolProviderFileNameMapping(PythonCoreBaseModel):
    type_: Optional["HybridPoolProviderType"] = Field(None, alias="type")
    filename: Optional["str"] = Field(None, alias="filename")


class ProcessDetailsTransport(PythonCoreBaseModel):
    version: Optional["str"] = Field(None, alias="version")
    id: Optional["str"] = Field(None, alias="id")
    content_id: Optional["str"] = Field(None, alias="contentId")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    source_system: Optional["str"] = Field(None, alias="sourceSystem")
    price: Optional["int"] = Field(None, alias="price")
    usage: Optional["str"] = Field(None, alias="usage")
    usage_path: Optional["str"] = Field(None, alias="usagePath")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    age: Optional["int"] = Field(None, alias="age")
    can_install: Optional["bool"] = Field(None, alias="canInstall")
    logo: Optional["str"] = Field(None, alias="logo")
    color: Optional["str"] = Field(None, alias="color")
    existing_process_id: Optional["str"] = Field(None, alias="existingProcessId")
    teaser_title: Optional["str"] = Field(None, alias="teaserTitle")
    teaser_bullet_points: Optional["List[Optional[str]]"] = Field(None, alias="teaserBulletPoints")
    supported_pool_providers: Optional["List[Optional[PoolProviderFileNameMapping]]"] = Field(
        None, alias="supportedPoolProviders"
    )
    tags: Optional["List[Optional[Tag]]"] = Field(None, alias="tags")
    changelog: Optional["str"] = Field(None, alias="changelog")
    real_time: Optional["bool"] = Field(None, alias="realTime")
    process_categories: Optional["List[Optional[str]]"] = Field(None, alias="processCategories")
    mock: Optional["bool"] = Field(None, alias="mock")


class Feature(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    enabled: Optional["bool"] = Field(None, alias="enabled")


class ColumnValueFilterTransport(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    connection_id: Optional["str"] = Field(None, alias="connectionId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    column_name: Optional["str"] = Field(None, alias="columnName")
    target_column_name: Optional["str"] = Field(None, alias="targetColumnName")
    column_values_at_a_time: Optional["int"] = Field(None, alias="columnValuesAtATime")


class TaskByPoolVariable(PythonCoreBaseModel):
    parameter_name: Optional["str"] = Field(None, alias="parameterName")
    task_name: Optional["str"] = Field(None, alias="taskName")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    job_name: Optional["str"] = Field(None, alias="jobName")


class StreamingLogMessageExecutionItemTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    execution_type: Optional["StreamingExecutionType"] = Field(None, alias="executionType")
    level: Optional["LogLevel"] = Field(None, alias="level")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    log_message: Optional["str"] = Field(None, alias="logMessage")
    log_translation_code: Optional["str"] = Field(None, alias="logTranslationCode")
    serialized_log_translation_parameters: Optional["str"] = Field(None, alias="serializedLogTranslationParameters")


class StreamingMonitoringTransport(PythonCoreBaseModel):
    log_message_execution_item_transports: Optional[
        "List[Optional[StreamingLogMessageExecutionItemTransport]]"
    ] = Field(None, alias="logMessageExecutionItemTransports")
    num_of_pages: Optional["int"] = Field(None, alias="numOfPages")


class DataSourceMetaData(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    columns: Optional["List[Optional[ColumnTransport]]"] = Field(None, alias="columns")
    date_columns: Optional["List[Optional[ColumnTransport]]"] = Field(None, alias="dateColumns")
    successful: Optional["bool"] = Field(None, alias="successful")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    translated_error_message: Optional["TranslatedConnectorMessage"] = Field(None, alias="translatedErrorMessage")


class ConnectorStreamingCapabilities(PythonCoreBaseModel):
    supports_additional_tables: Optional["bool"] = Field(None, alias="supportsAdditionalTables")
    column_type_override_support: Optional["ColumnTypeOverrideSupport"] = Field(None, alias="columnTypeOverrideSupport")
    available_table_configuration_parameters: Optional["List[Optional[TableConfigurationParameter]]"] = Field(
        None, alias="availableTableConfigurationParameters"
    )
    supports_api_selection: Optional["bool"] = Field(None, alias="supportsApiSelection")


class TableConfigurationParameter(PythonCoreBaseModel):
    key: Optional["TableConfigurationParameterKey"] = Field(None, alias="key")
    label: Optional["str"] = Field(None, alias="label")
    type_: Optional["TableConfigurationParameterType"] = Field(None, alias="type")
    options: Optional["List[Optional[str]]"] = Field(None, alias="options")
    default_value: Optional["Any"] = Field(None, alias="defaultValue")
    required_feature: Optional["str"] = Field(None, alias="requiredFeature")
    optional: Optional["bool"] = Field(None, alias="optional")
    table_level_only: Optional["bool"] = Field(None, alias="tableLevelOnly")
    extraction_level_only: Optional["bool"] = Field(None, alias="extractionLevelOnly")
    display_in_realtime_cockpit: Optional["bool"] = Field(None, alias="displayInRealtimeCockpit")
    display_in_extraction_ui: Optional["bool"] = Field(None, alias="displayInExtractionUI")
    display_tooltip: Optional["bool"] = Field(None, alias="displayTooltip")
    display_paragraph: Optional["bool"] = Field(None, alias="displayParagraph")
    depends_on: Optional["TableConfigurationParameterDependency"] = Field(None, alias="dependsOn")


class TableConfigurationParameterDependency(PythonCoreBaseModel):
    table_configuration_parameter_key: Optional["TableConfigurationParameterKey"] = Field(
        None, alias="tableConfigurationParameterKey"
    )
    value: Optional["Any"] = Field(None, alias="value")


class ExecutionItemWithPageTransport(PythonCoreBaseModel):
    execution_items: Optional["List[Optional[ExecutionItemTransport]]"] = Field(None, alias="executionItems")
    num_of_pages: Optional["int"] = Field(None, alias="numOfPages")


class EntityStatus(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    last_execution_start_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionStartDate")


class LogMessageWithPageTransport(PythonCoreBaseModel):
    log_messages: Optional["List[Optional[LogMessageTransport]]"] = Field(None, alias="logMessages")
    num_of_pages: Optional["int"] = Field(None, alias="numOfPages")


class PoolQueryResultColumn(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["DataPoolProviderColumnType"] = Field(None, alias="type")


class PoolQueryResultTable(PythonCoreBaseModel):
    affected_rows: Optional["int"] = Field(None, alias="affectedRows")
    table_content: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="tableContent")
    columns: Optional["List[Optional[PoolQueryResultColumn]]"] = Field(None, alias="columns")


class WorkbenchQueryResultTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    query: Optional["str"] = Field(None, alias="query")
    result: Optional["PoolQueryResultTable"] = Field(None, alias="result")
    message: Optional["str"] = Field(None, alias="message")
    error: Optional["str"] = Field(None, alias="error")


class StatementTransport(PythonCoreBaseModel):
    statement: Optional["str"] = Field(None, alias="statement")
    legal_note: Optional["str"] = Field(None, alias="legalNote")


class DataModelExecutionOption(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_model_name: Optional["str"] = Field(None, alias="dataModelName")


class ExtractionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    task_id: Optional["str"] = Field(None, alias="taskId")
    task_type: Optional["TaskType"] = Field(None, alias="taskType")
    template: Optional["bool"] = Field(None, alias="template")
    protection_status: Optional["TemplateProtectionStatus"] = Field(None, alias="protectionStatus")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    job_id: Optional["str"] = Field(None, alias="jobId")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    task_created_at: Optional["PythonCoreDatetime"] = Field(None, alias="taskCreatedAt")
    execution_order: Optional["int"] = Field(None, alias="executionOrder")
    published: Optional["bool"] = Field(None, alias="published")
    disabled: Optional["bool"] = Field(None, alias="disabled")
    legal_agreement_accepted: Optional["bool"] = Field(None, alias="legalAgreementAccepted")
    extraction_configuration_value_transport: Optional["ExtractionConfigurationValueTransport"] = Field(
        None, alias="extractionConfigurationValueTransport"
    )
    extraction_configuration: Optional["ExtractionConfigurationValueTransport"] = Field(
        None, alias="extractionConfiguration"
    )


class ConfiguredConnector(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")
    host: Optional["str"] = Field(None, alias="host")
    default_to_uplink: Optional["bool"] = Field(None, alias="defaultToUplink")
    hide_uplink_option: Optional["bool"] = Field(None, alias="hideUplinkOption")
    show_uplink_option_by_feature: Optional["bool"] = Field(None, alias="showUplinkOptionByFeature")
    attributes: Optional["Dict[str, Optional[str]]"] = Field(None, alias="attributes")
    override_to_on_prem: Optional["bool"] = Field(None, alias="overrideToOnPrem")
    on_premise_connector: Optional["bool"] = Field(None, alias="onPremiseConnector")
    cloud_connector: Optional["bool"] = Field(None, alias="cloudConnector")
    custom_extractor: Optional["bool"] = Field(None, alias="customExtractor")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    configuration_handler: Optional["str"] = Field(None, alias="configurationHandler")


class DataSourceIdNameMapping(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["str"] = Field(None, alias="type")


class DataTransferImportOption(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_pool_name: Optional["str"] = Field(None, alias="dataPoolName")
    data_sources: Optional["List[Optional[DataSourceIdNameMapping]]"] = Field(None, alias="dataSources")


class DataTransferDataPoolsMapping(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    pool_name: Optional["str"] = Field(None, alias="poolName")
    already_imported: Optional["bool"] = Field(None, alias="alreadyImported")
    selected: Optional["bool"] = Field(None, alias="selected")


class DataTransferExportTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")
    data_transfer_export_type: Optional["DataTransferExportType"] = Field(None, alias="dataTransferExportType")
    nb_of_allowed_data_pools: Optional["int"] = Field(None, alias="nbOfAllowedDataPools")
    nb_of_importing_data_pools: Optional["int"] = Field(None, alias="nbOfImportingDataPools")
    nb_of_exported_tables: Optional["int"] = Field(None, alias="nbOfExportedTables")
    export_subset: Optional["bool"] = Field(None, alias="exportSubset")
    other_data_pools: Optional["List[Optional[DataTransferDataPoolsMapping]]"] = Field(None, alias="otherDataPools")
    data_transfer_export_tables: Optional["List[Optional[DataTransferExportTableTransport]]"] = Field(
        None, alias="dataTransferExportTables"
    )


class DataPoolIdNameMapping(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    pool_name: Optional["str"] = Field(None, alias="poolName")


class DataTransferExportOptions(PythonCoreBaseModel):
    data_transfer_exportable_data_sources: Optional["List[Optional[DataTransferExportableDataSource]]"] = Field(
        None, alias="dataTransferExportableDataSources"
    )
    other_data_pools: Optional["List[Optional[DataPoolIdNameMapping]]"] = Field(None, alias="otherDataPools")


class DataTransferExportableDataSource(PythonCoreBaseModel):
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")


class DataSourceAvailableTables(PythonCoreBaseModel):
    available_tables: Optional["List[Optional[DataSourceTable]]"] = Field(None, alias="availableTables")
    lookup_successful: Optional["bool"] = Field(None, alias="lookupSuccessful")
    message: Optional["str"] = Field(None, alias="message")
    translated_connector_message: Optional["TranslatedConnectorMessage"] = Field(
        None, alias="translatedConnectorMessage"
    )


class DataSourceTable(PythonCoreBaseModel):
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    alias: Optional["str"] = Field(None, alias="alias")
    schema_: Optional["str"] = Field(None, alias="schema")


class AdditionalConnectorInformation(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    value: Optional["str"] = Field(None, alias="value")


class ConnectorInformation(PythonCoreBaseModel):
    not_reachable: Optional["bool"] = Field(None, alias="notReachable")
    connector_version: Optional["str"] = Field(None, alias="connectorVersion")
    instance_version: Optional["str"] = Field(None, alias="instanceVersion")
    job_transports: Optional["List[Optional[JobTransport]]"] = Field(None, alias="jobTransports")
    latest_execution: Optional["ExecutionItemTransport"] = Field(None, alias="latestExecution")
    additional_information: Optional["List[Optional[AdditionalConnectorInformation]]"] = Field(
        None, alias="additionalInformation"
    )
    queue_information: Optional["ExtractionQueueStatus"] = Field(None, alias="queueInformation")


class ExtractionQueueStatus(PythonCoreBaseModel):
    extractions_being_processed_in_queue: Optional["List[Optional[ExtractionQueuedTable]]"] = Field(
        None, alias="extractionsBeingProcessedInQueue"
    )
    extractions_in_queue: Optional["List[Optional[ExtractionQueuedTable]]"] = Field(None, alias="extractionsInQueue")


class ExtractionQueuedTable(PythonCoreBaseModel):
    execution_item_id: Optional["str"] = Field(None, alias="executionItemId")
    table_name: Optional["str"] = Field(None, alias="tableName")


class DataSourceStatus(PythonCoreBaseModel):
    connector_status: Optional["ConnectorStatus"] = Field(None, alias="connectorStatus")
    type_: Optional["str"] = Field(None, alias="type")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    supports_realtime: Optional["bool"] = Field(None, alias="supportsRealtime")


class ImportedDataSourceChangesTransport(PythonCoreBaseModel):
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    tables_to_be_created: Optional["List[Optional[str]]"] = Field(None, alias="tablesToBeCreated")
    tables_to_be_synchronized: Optional["List[Optional[str]]"] = Field(None, alias="tablesToBeSynchronized")
    tables_to_be_deleted: Optional["List[Optional[str]]"] = Field(None, alias="tablesToBeDeleted")
    added_in_source_and_target: Optional["List[Optional[str]]"] = Field(None, alias="addedInSourceAndTarget")
    source_data_pool_id: Optional["str"] = Field(None, alias="sourceDataPoolId")
    source_data_source_id: Optional["str"] = Field(None, alias="sourceDataSourceId")


class ChangeLogStatus(PythonCoreBaseModel):
    error_querying_status: Optional["bool"] = Field(None, alias="errorQueryingStatus")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    connection_supports_realtime: Optional["bool"] = Field(None, alias="connectionSupportsRealtime")
    change_log_table_metadata: Optional["ChangeLogTableMetadata"] = Field(None, alias="changeLogTableMetadata")


class ChangeLogTableMetadata(PythonCoreBaseModel):
    change_log_name: Optional["str"] = Field(None, alias="changeLogName")
    trigger_name: Optional["str"] = Field(None, alias="triggerName")
    change_log_table_status: Optional["ChangeLogTableStatus"] = Field(None, alias="changeLogTableStatus")
    external_cdc: Optional["bool"] = Field(None, alias="externalCdc")


class ConnectorCapabilities(PythonCoreBaseModel):
    supports_columns: Optional["bool"] = Field(None, alias="supportsColumns")
    supports_anonymized_columns: Optional["bool"] = Field(None, alias="supportsAnonymizedColumns")
    supports_filters: Optional["bool"] = Field(None, alias="supportsFilters")
    supports_remote_search: Optional["bool"] = Field(None, alias="supportsRemoteSearch")
    supports_joins: Optional["bool"] = Field(None, alias="supportsJoins")
    supports_double_joins: Optional["bool"] = Field(None, alias="supportsDoubleJoins")
    supports_join_columns: Optional["bool"] = Field(None, alias="supportsJoinColumns")
    supports_pk_joins: Optional["bool"] = Field(None, alias="supportsPkJoins")
    supports_override_pk_columns: Optional["bool"] = Field(None, alias="supportsOverridePkColumns")
    supports_target_table_renaming: Optional["bool"] = Field(None, alias="supportsTargetTableRenaming")
    table_capabilities: Optional["List[Optional[TableCapabilities]]"] = Field(None, alias="tableCapabilities")
    supports_bulk_import: Optional["bool"] = Field(None, alias="supportsBulkImport")
    supports_filter_validation: Optional["bool"] = Field(None, alias="supportsFilterValidation")
    supports_dependent_table_selection: Optional["bool"] = Field(None, alias="supportsDependentTableSelection")
    supports_column_value_filters: Optional["bool"] = Field(None, alias="supportsColumnValueFilters")
    supports_connector_information: Optional["bool"] = Field(None, alias="supportsConnectorInformation")
    supports_advanced_settings: Optional["bool"] = Field(None, alias="supportsAdvancedSettings")
    column_type_override_support: Optional["ColumnTypeOverrideSupport"] = Field(None, alias="columnTypeOverrideSupport")
    supports_extractor_logs: Optional["bool"] = Field(None, alias="supportsExtractorLogs")
    nested_table_capabilities: Optional["ConnectorCapabilities"] = Field(None, alias="nestedTableCapabilities")
    data_push_upsert_strategy_options: Optional["DataPushUpsertStrategyOptions"] = Field(
        None, alias="dataPushUpsertStrategyOptions"
    )
    extra_capabilities: Optional["List[Optional[str]]"] = Field(None, alias="extraCapabilities")
    available_table_configuration_parameters: Optional["List[Optional[TableConfigurationParameter]]"] = Field(
        None, alias="availableTableConfigurationParameters"
    )
    anonymization_algorithms: Optional["List[Optional[AnonymizationAlgorithm]]"] = Field(
        None, alias="anonymizationAlgorithms"
    )
    filter_options: Optional["FilterOptions"] = Field(None, alias="filterOptions")
    supports_calculated_columns: Optional["bool"] = Field(None, alias="supportsCalculatedColumns")
    supports_join_path_validation: Optional["bool"] = Field(None, alias="supportsJoinPathValidation")
    supports_change_log_table_option: Optional["bool"] = Field(None, alias="supportsChangeLogTableOption")
    supports_convert_to_delete_job: Optional["bool"] = Field(None, alias="supportsConvertToDeleteJob")
    supports_extraction_preview: Optional["bool"] = Field(None, alias="supportsExtractionPreview")
    supports_batch_cl_statuses: Optional["bool"] = Field(None, alias="supportsBatchCLStatuses")
    extraction_validation_triggers: Optional["List[Optional[ExtractionValidationTrigger]]"] = Field(
        None, alias="extractionValidationTriggers"
    )
    supports_extract_deletions: Optional["bool"] = Field(None, alias="supportsExtractDeletions")
    data_push_delete_strategy_options: Optional["DataPushDeleteStrategyOptions"] = Field(
        None, alias="dataPushDeleteStrategyOptions"
    )
    support_customize_column_selection: Optional["bool"] = Field(None, alias="supportCustomizeColumnSelection")
    columns_displayed_but_not_deselectable: Optional["bool"] = Field(None, alias="columnsDisplayedButNotDeselectable")
    support_internal_system_config: Optional["bool"] = Field(None, alias="supportInternalSystemConfig")
    supports_invalidate_cache: Optional["bool"] = Field(None, alias="supportsInvalidateCache")
    supports_cl_override_table: Optional["bool"] = Field(None, alias="supportsClOverrideTable")
    supports_parallelization_queue_information: Optional["bool"] = Field(
        None, alias="supportsParallelizationQueueInformation"
    )
    general_table_options_available: Optional["bool"] = Field(None, alias="generalTableOptionsAvailable")
    any_table_options_available: Optional["bool"] = Field(None, alias="anyTableOptionsAvailable")


class FilterOption(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    column_type: Optional["ColumnType"] = Field(None, alias="columnType")
    available_in_creation_filter: Optional["bool"] = Field(None, alias="availableInCreationFilter")
    allow_end_date_creation_filter: Optional["bool"] = Field(None, alias="allowEndDateCreationFilter")
    available_in_update_filter: Optional["bool"] = Field(None, alias="availableInUpdateFilter")
    explicit_date_filter_option: Optional["bool"] = Field(None, alias="explicitDateFilterOption")


class FilterOptions(PythonCoreBaseModel):
    include_metadata_columns_as_options: Optional["bool"] = Field(None, alias="includeMetadataColumnsAsOptions")
    time_filters_disabled: Optional["bool"] = Field(None, alias="timeFiltersDisabled")
    options: Optional["List[Optional[FilterOption]]"] = Field(None, alias="options")


class TableCapabilities(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    pattern: Optional["str"] = Field(None, alias="pattern")
    capabilities: Optional["ConnectorCapabilities"] = Field(None, alias="capabilities")


class DataSourceTypeTransport(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")


class TableSyncJobTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    started_at: Optional["PythonCoreDatetime"] = Field(None, alias="startedAt")
    partitions: Optional["int"] = Field(None, alias="partitions")
    partitions_done: Optional["int"] = Field(None, alias="partitionsDone")
    rows: Optional["int"] = Field(None, alias="rows")
    rows_done: Optional["int"] = Field(None, alias="rowsDone")
    partitions_error: Optional["int"] = Field(None, alias="partitionsError")
    error_messages: Optional["List[Optional[str]]"] = Field(None, alias="errorMessages")


class DataModelTableLoadingHistoryTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    status: Optional["DataModelTableLoadingStatus"] = Field(None, alias="status")


class DataModelLoadTableExtendedTransport(PythonCoreBaseModel):
    table_id: Optional["str"] = Field(None, alias="tableId")
    table_name: Optional["str"] = Field(None, alias="tableName")
    table_row_count: Optional["int"] = Field(None, alias="tableRowCount")
    done: Optional["bool"] = Field(None, alias="done")
    invisible: Optional["bool"] = Field(None, alias="invisible")
    cancel: Optional["bool"] = Field(None, alias="cancel")
    augmented: Optional["bool"] = Field(None, alias="augmented")


class DataLoadHistoryTransport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_load_id: Optional["str"] = Field(None, alias="dataLoadId")
    message: Optional["str"] = Field(None, alias="message")
    load_status: Optional["LoadStatus"] = Field(None, alias="loadStatus")
    start_date: Optional["PythonCoreDatetime"] = Field(None, alias="startDate")
    end_date: Optional["PythonCoreDatetime"] = Field(None, alias="endDate")
    warmup_duration: Optional["int"] = Field(None, alias="warmupDuration")
    done: Optional["bool"] = Field(None, alias="done")


class DataModelAverageTimeMapTransport(PythonCoreBaseModel):
    type_: Optional["DataLoadType"] = Field(None, alias="type")
    average_loading_time: Optional["int"] = Field(None, alias="averageLoadingTime")


class DataModelLoadHistoryTransport(PythonCoreBaseModel):
    last_successful_data_model: Optional["DataLoadHistoryTransport"] = Field(None, alias="lastSuccessfulDataModel")
    data_load_history: Optional["List[Optional[DataModelDataLoadHistoryTransport]]"] = Field(
        None, alias="dataLoadHistory"
    )
    average_load_time: Optional["List[Optional[DataModelAverageTimeMapTransport]]"] = Field(
        None, alias="averageLoadTime"
    )


class DataModelLoadInfoTransport(PythonCoreBaseModel):
    live_data_model: Optional["DataModelLoadTransport"] = Field(None, alias="liveDataModel")
    current_compute_load: Optional["DataModelDataLoadHistoryTransport"] = Field(None, alias="currentComputeLoad")


class DataModelLoadSyncTransport(PythonCoreBaseModel):
    load_info: Optional["DataModelLoadInfoTransport"] = Field(None, alias="loadInfo")
    load_history: Optional["DataModelLoadHistoryTransport"] = Field(None, alias="loadHistory")


class ActivityTableCreationRestriction(PythonCoreBaseModel):
    number_of_existing_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingProcessConfigurations"
    )
    number_of_existing_data_models_without_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingDataModelsWithoutProcessConfigurations"
    )
    number_of_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfProcessConfigurationsToCreate"
    )
    number_of_data_models_without_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfDataModelsWithoutProcessConfigurationsToCreate"
    )
    number_of_licensed_processes: Optional["int"] = Field(None, alias="numberOfLicensedProcesses")
    number_of_process_configurations_for_data_model: Optional["int"] = Field(
        None, alias="numberOfProcessConfigurationsForDataModel"
    )
    can_create_activity_table: Optional["bool"] = Field(None, alias="canCreateActivityTable")
    unlimited_number_of_licensed_data_models: Optional["bool"] = Field(
        None, alias="unlimitedNumberOfLicensedDataModels"
    )
    number_of_installable_processes: Optional["int"] = Field(None, alias="numberOfInstallableProcesses")
    number_of_processes_to_create: Optional["int"] = Field(None, alias="numberOfProcessesToCreate")
    number_of_existing_processes: Optional["int"] = Field(None, alias="numberOfExistingProcesses")
    can_create_data_model: Optional["bool"] = Field(None, alias="canCreateDataModel")
    monitoring_target_pool: Optional["bool"] = Field(None, alias="monitoringTargetPool")


class DataModelWithStatusTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    active_data_model: Optional["bool"] = Field(None, alias="activeDataModel")
    loaded_before: Optional["bool"] = Field(None, alias="loadedBefore")
    last_successful_load_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastSuccessfulLoadDate")
    load_status: Optional["DataModelLoadStatus"] = Field(None, alias="loadStatus")
    last_load_start_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastLoadStartDate")
    has_enabled_data_permissions: Optional["bool"] = Field(None, alias="hasEnabledDataPermissions")
    count_table_rows_loaded_on_last_successful_load: Optional["int"] = Field(
        None, alias="countTableRowsLoadedOnLastSuccessfulLoad"
    )


class DataModelIdAndNameTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class DataPoolDataModelOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_models: Optional["List[Optional[DataModelIdAndNameTransport]]"] = Field(None, alias="dataModels")
    data_model_table_data_source_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataModelTableDataSourceIds")


class PoolTablePreview(PythonCoreBaseModel):
    columns: Optional["List[Optional[PoolColumn]]"] = Field(None, alias="columns")
    data_columns: Optional["List[Optional[List[Optional[Any]]]]"] = Field(None, alias="dataColumns")


class DataPoolVersionSlim(PythonCoreBaseModel):
    schema_version: Optional["str"] = Field(None, alias="schemaVersion")
    jobs: Optional["List[Optional[Job]]"] = Field(None, alias="jobs")
    job_schedulings: Optional["List[Optional[JobScheduling]]"] = Field(None, alias="jobSchedulings")
    schedulings: Optional["List[Optional[Scheduling]]"] = Field(None, alias="schedulings")
    scheduling_triggers: Optional["List[Optional[SchedulingTrigger]]"] = Field(None, alias="schedulingTriggers")
    table_extractions: Optional["List[Optional[TableExtraction]]"] = Field(None, alias="tableExtractions")
    table_extraction_calculated_columns: Optional["List[Optional[TableExtractionCalculatedColumn]]"] = Field(
        None, alias="tableExtractionCalculatedColumns"
    )
    table_extraction_columns: Optional["List[Optional[TableExtractionColumn]]"] = Field(
        None, alias="tableExtractionColumns"
    )
    table_extraction_joins: Optional["List[Optional[TableExtractionJoin]]"] = Field(None, alias="tableExtractionJoins")
    data_model_executions: Optional["List[Optional[DataModelExecution]]"] = Field(None, alias="dataModelExecutions")
    data_model_execution_tables: Optional["List[Optional[DataModelExecutionTable]]"] = Field(
        None, alias="dataModelExecutionTables"
    )
    tasks: Optional["List[Optional[Task]]"] = Field(None, alias="tasks")
    task_instances: Optional["List[Optional[TaskInstance]]"] = Field(None, alias="taskInstances")
    variables: Optional["List[Optional[Variable]]"] = Field(None, alias="variables")
    variable_default_settings: Optional["List[Optional[VariableDefaultSettings]]"] = Field(
        None, alias="variableDefaultSettings"
    )
    variable_default_values: Optional["List[Optional[VariableDefaultValue]]"] = Field(
        None, alias="variableDefaultValues"
    )
    variable_settings: Optional["List[Optional[VariableSettings]]"] = Field(None, alias="variableSettings")
    variable_values: Optional["List[Optional[VariableValue]]"] = Field(None, alias="variableValues")
    data_models: Optional["List[Optional[DataModel]]"] = Field(None, alias="dataModels")
    data_model_configurations: Optional["List[Optional[DataModelConfiguration]]"] = Field(
        None, alias="dataModelConfigurations"
    )
    data_model_custom_calendar_entries: Optional["List[Optional[DataModelCustomCalendarEntry]]"] = Field(
        None, alias="dataModelCustomCalendarEntries"
    )
    data_model_factory_calendars: Optional["List[Optional[DataModelFactoryCalendar]]"] = Field(
        None, alias="dataModelFactoryCalendars"
    )
    data_model_foreign_keys: Optional["List[Optional[DataModelForeignKey]]"] = Field(None, alias="dataModelForeignKeys")
    data_model_foreign_key_columns: Optional["List[Optional[DataModelForeignKeyColumn]]"] = Field(
        None, alias="dataModelForeignKeyColumns"
    )
    data_model_signal_links: Optional["List[Optional[DataModelSignalLink]]"] = Field(None, alias="dataModelSignalLinks")
    data_model_signal_link_columns: Optional["List[Optional[DataModelSignalLinkColumn]]"] = Field(
        None, alias="dataModelSignalLinkColumns"
    )
    data_model_tables: Optional["List[Optional[DataModelTable]]"] = Field(None, alias="dataModelTables")
    data_model_table_columns: Optional["List[Optional[DataModelTableColumn]]"] = Field(
        None, alias="dataModelTableColumns"
    )
    replication_cockpit_data: Optional["VersionedObject"] = Field(None, alias="replicationCockpitData")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_pool_name: Optional["str"] = Field(None, alias="dataPoolName")
    data_sources_versioning: Optional["List[Optional[DataSourceVersioning]]"] = Field(
        None, alias="dataSourcesVersioning"
    )


class DataSourceVersioning(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["str"] = Field(None, alias="type")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    target_schema_name: Optional["str"] = Field(None, alias="targetSchemaName")
    imported: Optional["bool"] = Field(None, alias="imported")


class DataModelCreationRestrictionWithSelection(PythonCoreBaseModel):
    number_of_existing_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingProcessConfigurations"
    )
    number_of_existing_data_models_without_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingDataModelsWithoutProcessConfigurations"
    )
    number_of_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfProcessConfigurationsToCreate"
    )
    number_of_data_models_without_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfDataModelsWithoutProcessConfigurationsToCreate"
    )
    number_of_licensed_processes: Optional["int"] = Field(None, alias="numberOfLicensedProcesses")
    data_model_import_options: Optional["List[Optional[DataModelImportOption]]"] = Field(
        None, alias="dataModelImportOptions"
    )
    unlimited_number_of_licensed_data_models: Optional["bool"] = Field(
        None, alias="unlimitedNumberOfLicensedDataModels"
    )
    number_of_installable_processes: Optional["int"] = Field(None, alias="numberOfInstallableProcesses")
    number_of_processes_to_create: Optional["int"] = Field(None, alias="numberOfProcessesToCreate")
    number_of_existing_processes: Optional["int"] = Field(None, alias="numberOfExistingProcesses")
    can_create_data_model: Optional["bool"] = Field(None, alias="canCreateDataModel")
    monitoring_target_pool: Optional["bool"] = Field(None, alias="monitoringTargetPool")


class DataModelImportOption(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    process_configurations: Optional["int"] = Field(None, alias="processConfigurations")
    process_count: Optional["int"] = Field(None, alias="processCount")
    has_no_process_configurations: Optional["bool"] = Field(None, alias="hasNoProcessConfigurations")


class ApplicationWizardExecutionSummary(PythonCoreBaseModel):
    job_id: Optional["str"] = Field(None, alias="jobId")
    job_name: Optional["str"] = Field(None, alias="jobName")
    execution_status: Optional["ExecutionStatus"] = Field(None, alias="executionStatus")
    current_task_name: Optional["str"] = Field(None, alias="currentTaskName")
    current_task_type: Optional["TaskType"] = Field(None, alias="currentTaskType")


class StudioPackageOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    last_publish_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastPublishDate")
    created_by_user_info: Optional["StudioPackageUserInfoTransport"] = Field(None, alias="createdByUserInfo")
    related_data_models: Optional["List[Optional[StudioPackageRelatedDataModelInfoTransport]]"] = Field(
        None, alias="relatedDataModels"
    )


class StudioPackageRelatedDataModelInfoTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class StudioPackageUserInfoTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class SchedulingOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["ExecutionStatus"] = Field(None, alias="status")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    data_job_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataJobIds")


class ReplicationCockpitTableOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["ReplicationCockpitTableStatus"] = Field(None, alias="status")
    start_date: Optional["PythonCoreDatetime"] = Field(None, alias="startDate")
    number_of_transformations: Optional["int"] = Field(None, alias="numberOfTransformations")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_source_name: Optional["str"] = Field(None, alias="dataSourceName")


class DataModelOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    execution_status: Optional["ExecutionStatus"] = Field(None, alias="executionStatus")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    data_source_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataSourceIds")


class DataJobOverviewTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    execution_status: Optional["ExecutionStatus"] = Field(None, alias="executionStatus")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_model_ids: Optional["List[Optional[str]]"] = Field(None, alias="dataModelIds")
    number_of_extractions: Optional["int"] = Field(None, alias="numberOfExtractions")
    number_of_transformations: Optional["int"] = Field(None, alias="numberOfTransformations")


class DataPoolOverviewTransport(PythonCoreBaseModel):
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_source_overview_transports: Optional["List[Optional[DataSourceOverviewTransport]]"] = Field(
        None, alias="dataSourceOverviewTransports"
    )
    replication_cockpit_table_overview_transports: Optional[
        "List[Optional[ReplicationCockpitTableOverviewTransport]]"
    ] = Field(None, alias="replicationCockpitTableOverviewTransports")
    scheduling_overview_transports: Optional["List[Optional[SchedulingOverviewTransport]]"] = Field(
        None, alias="schedulingOverviewTransports"
    )
    data_model_overview_transports: Optional["List[Optional[DataModelOverviewTransport]]"] = Field(
        None, alias="dataModelOverviewTransports"
    )
    data_job_overview_transports: Optional["List[Optional[DataJobOverviewTransport]]"] = Field(
        None, alias="dataJobOverviewTransports"
    )
    studio_package_overview_transports: Optional["List[Optional[StudioPackageOverviewTransport]]"] = Field(
        None, alias="studioPackageOverviewTransports"
    )


class DataPoolWithExtendedContentTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    time_stamp: Optional["PythonCoreDatetime"] = Field(None, alias="timeStamp")
    configuration_status: Optional["PoolConfigurationStatus"] = Field(None, alias="configurationStatus")
    locked: Optional["bool"] = Field(None, alias="locked")
    content_id: Optional["str"] = Field(None, alias="contentId")
    content_version: Optional["int"] = Field(None, alias="contentVersion")
    tags: Optional["List[Optional[Tag]]"] = Field(None, alias="tags")
    original_id: Optional["str"] = Field(None, alias="originalId")
    monitoring_target: Optional["bool"] = Field(None, alias="monitoringTarget")
    custom_monitoring_target: Optional["bool"] = Field(None, alias="customMonitoringTarget")
    custom_monitoring_target_active: Optional["bool"] = Field(None, alias="customMonitoringTargetActive")
    exported: Optional["bool"] = Field(None, alias="exported")
    monitoring_message_columns_migrated: Optional["bool"] = Field(None, alias="monitoringMessageColumnsMigrated")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    data_sources: Optional["List[Optional[DataSourceTransport]]"] = Field(None, alias="dataSources")
    job_logs: Optional["ExecutionItemWithPageTransport"] = Field(None, alias="jobLogs")
    data_models_with_status: Optional["List[Optional[DataModelWithStatusTransport]]"] = Field(
        None, alias="dataModelsWithStatus"
    )
    object_id: Optional["str"] = Field(None, alias="objectId")


class DataPoolPageTransport(PythonCoreBaseModel):
    content: Optional["List[Optional[DataPoolSlimTransport]]"] = Field(None, alias="content")
    page_size: Optional["int"] = Field(None, alias="pageSize")
    page_number: Optional["int"] = Field(None, alias="pageNumber")
    total_count: Optional["int"] = Field(None, alias="totalCount")


class DataPoolSlimTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    status: Optional["DataPoolStatus"] = Field(None, alias="status")
    last_execution_start_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionStartDate")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    tags: Optional["List[Optional[Tag]]"] = Field(None, alias="tags")
    raw_data_size: Optional["int"] = Field(None, alias="rawDataSize")
    data_sources: Optional["List[Optional[DataSourceSlimTransport]]"] = Field(None, alias="dataSources")


class DataSourceSlimTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    imported: Optional["bool"] = Field(None, alias="imported")
    imported_pool_id: Optional["str"] = Field(None, alias="importedPoolId")


class DataPoolMoveHybridVersionCheck(PythonCoreBaseModel):
    matched: Optional["bool"] = Field(None, alias="matched")
    message: Optional["str"] = Field(None, alias="message")


class PermissionOptionTransport(PythonCoreBaseModel):
    permission_key: Optional["str"] = Field(None, alias="permissionKey")
    permission_type: Optional["str"] = Field(None, alias="permissionType")
    requires_analyst: Optional["bool"] = Field(None, alias="requiresAnalyst")
    use: Optional["bool"] = Field(None, alias="use")
    requires_use: Optional["bool"] = Field(None, alias="requiresUse")
    display_name: Optional["str"] = Field(None, alias="displayName")


class PermissionRoleTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    permission_keys: Optional["List[Optional[str]]"] = Field(None, alias="permissionKeys")
    requires_analyst: Optional["bool"] = Field(None, alias="requiresAnalyst")


class PermissionsModelTransport(PythonCoreBaseModel):
    access_restricted: Optional["bool"] = Field(None, alias="accessRestricted")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    roles: Optional["List[Optional[PermissionRoleTransport]]"] = Field(None, alias="roles")
    options: Optional["List[Optional[PermissionOptionTransport]]"] = Field(None, alias="options")


class TeamConsumptionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    consumption_in_bytes: Optional["int"] = Field(None, alias="consumptionInBytes")
    consumption_stage: Optional["DataConsumptionStage"] = Field(None, alias="consumptionStage")
    consumption_status: Optional["ConsumptionStatus"] = Field(None, alias="consumptionStatus")
    last_update: Optional["PythonCoreDatetime"] = Field(None, alias="lastUpdate")
    last_notified_consumption_stage: Optional["DataConsumptionStage"] = Field(
        None, alias="lastNotifiedConsumptionStage"
    )


class ExtendedTableConsumptionPageTransport(PythonCoreBaseModel):
    extended_table_consumption_transports: Optional["List[Optional[ExtendedTableConsumptionTransport]]"] = Field(
        None, alias="extendedTableConsumptionTransports"
    )
    num_of_page: Optional["int"] = Field(None, alias="numOfPage")
    page_consumption_in_bytes: Optional["int"] = Field(None, alias="pageConsumptionInBytes")


class ExtendedTableConsumptionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    table_name: Optional["str"] = Field(None, alias="tableName")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    data_connection_id: Optional["str"] = Field(None, alias="dataConnectionId")
    last_update: Optional["PythonCoreDatetime"] = Field(None, alias="lastUpdate")
    raw_data_size: Optional["int"] = Field(None, alias="rawDataSize")
    last_epoch: Optional["PythonCoreDatetime"] = Field(None, alias="lastEpoch")
    data_pool_name: Optional["str"] = Field(None, alias="dataPoolName")
    data_connection_name: Optional["str"] = Field(None, alias="dataConnectionName")


class PackageInformation(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    existing_process_id: Optional["str"] = Field(None, alias="existingProcessId")
    source_system: Optional["str"] = Field(None, alias="sourceSystem")
    logo: Optional["str"] = Field(None, alias="logo")


class PackageDataConnectionInformation(PythonCoreBaseModel):
    can_install: Optional["bool"] = Field(None, alias="canInstall")
    connection_id: Optional["str"] = Field(None, alias="connectionId")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["str"] = Field(None, alias="type")


class JobFutureTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    lock_id: Optional["str"] = Field(None, alias="lockId")
    entity_id: Optional["str"] = Field(None, alias="entityId")
    lock_start: Optional["PythonCoreDatetime"] = Field(None, alias="lockStart")
    locked_until: Optional["PythonCoreDatetime"] = Field(None, alias="lockedUntil")


class TransformationExecutionTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    item_id: Optional["str"] = Field(None, alias="itemId")
    transformation_execution_type: Optional["TransformationExecutionType"] = Field(
        None, alias="transformationExecutionType"
    )
    status: Optional["TransformationExecutionStatus"] = Field(None, alias="status")
    pool_provider_session_id: Optional["str"] = Field(None, alias="poolProviderSessionId")


class PermissionsOverviewTransport(PythonCoreBaseModel):
    service_name: Optional["str"] = Field(None, alias="serviceName")
    members_count: Optional["int"] = Field(None, alias="membersCount")
    analysts_count: Optional["int"] = Field(None, alias="analystsCount")
    permissions_size: Optional["int"] = Field(None, alias="permissionsSize")


class AccessControlListTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    parent_object_id: Optional["str"] = Field(None, alias="parentObjectId")
    object_description: Optional["str"] = Field(None, alias="objectDescription")
    service_name: Optional["str"] = Field(None, alias="serviceName")


class SearchItem(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    link: Optional["str"] = Field(None, alias="link")
    type_: Optional["str"] = Field(None, alias="type")
    description: Optional["str"] = Field(None, alias="description")
    icon: Optional["str"] = Field(None, alias="icon")
    app_key: Optional["str"] = Field(None, alias="appKey")


class ProcessConfigurationTransport(PythonCoreBaseModel):
    process_count: Optional["int"] = Field(None, alias="processCount")


class DataModelCreationRestrictionWithSelectionV1(PythonCoreBaseModel):
    number_of_existing_data_models: Optional["int"] = Field(None, alias="numberOfExistingDataModels")
    number_of_licensed_data_models: Optional["int"] = Field(None, alias="numberOfLicensedDataModels")
    number_of_data_models_to_create: Optional["int"] = Field(None, alias="numberOfDataModelsToCreate")
    data_model_import_options: Optional["List[Optional[DataModelImportOptionV1]]"] = Field(
        None, alias="dataModelImportOptions"
    )
    unlimited_number_of_licensed_data_models: Optional["bool"] = Field(
        None, alias="unlimitedNumberOfLicensedDataModels"
    )
    number_of_installable_data_models: Optional["int"] = Field(None, alias="numberOfInstallableDataModels")
    can_create_data_model: Optional["bool"] = Field(None, alias="canCreateDataModel")


class DataModelImportOptionV1(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class PoolProviderConnectionDetails(PythonCoreBaseModel):
    url: Optional["str"] = Field(None, alias="url")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    message_type: Optional["str"] = Field(None, alias="messageType")


class PoolProviderDetailTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_provider_type: Optional["PoolProviderType"] = Field(None, alias="poolProviderType")
    pool_provider_connection_details: Optional[
        "Union[DatabaseProviderConnectionDetails,SnowflakeProviderConnectionDetails,VerticaProviderConnectionDetails,None]"
    ] = Field(None, alias="poolProviderConnectionDetails")


class KerberosConfiguration(PythonCoreBaseModel):
    host: Optional["str"] = Field(None, alias="host")
    realm: Optional["str"] = Field(None, alias="realm")
    kdc: Optional["List[Optional[str]]"] = Field(None, alias="kdc")
    admin_server: Optional["str"] = Field(None, alias="adminServer")
    ha_namenodes: Optional["List[Optional[str]]"] = Field(None, alias="haNamenodes")
    zookeeper_quorum: Optional["List[Optional[str]]"] = Field(None, alias="zookeeperQuorum")
    principal: Optional["str"] = Field(None, alias="principal")
    key_provider: Optional["str"] = Field(None, alias="keyProvider")
    port: Optional["int"] = Field(None, alias="port")
    root_path: Optional["str"] = Field(None, alias="rootPath")
    password: Optional["str"] = Field(None, alias="password")
    username: Optional["str"] = Field(None, alias="username")
    nn_http_port: Optional["int"] = Field(None, alias="nnHttpPort")
    nn_https_port: Optional["int"] = Field(None, alias="nnHttpsPort")
    rpc_protection: Optional["str"] = Field(None, alias="rpcProtection")
    url: Optional["str"] = Field(None, alias="url")


class ConnectionConfiguration(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")
    use_uplink: Optional["bool"] = Field(None, alias="useUplink")
    streaming_connector: Optional["bool"] = Field(None, alias="streamingConnector")
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    connection_configuration_logging_data: Optional["Dict[str, Optional[Any]]"] = Field(
        None, alias="connectionConfigurationLoggingData"
    )


class DataPushChunkTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    type_: Optional["ChunkType"] = Field(None, alias="type")


class DataPoolTableStatus(PythonCoreBaseModel):
    table_exists: Optional["bool"] = Field(None, alias="tableExists")
    row_count: Optional["int"] = Field(None, alias="rowCount")
    table_empty: Optional["bool"] = Field(None, alias="tableEmpty")


class DataPoolPermissionSummary(PythonCoreBaseModel):
    pool_id: Optional["str"] = Field(None, alias="poolId")
    has_admin_permission: Optional["bool"] = Field(None, alias="hasAdminPermission")
    has_data_push_api_permission: Optional["bool"] = Field(None, alias="hasDataPushApiPermission")
    has_continuous_data_push_api_permission: Optional["bool"] = Field(None, alias="hasContinuousDataPushApiPermission")
    has_view_only_permission: Optional["bool"] = Field(None, alias="hasViewOnlyPermission")


class DataModelSummary(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    pool_id: Optional["str"] = Field(None, alias="poolId")


class DataPoolSummary(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    data_models: Optional["List[Optional[DataModelSummary]]"] = Field(None, alias="dataModels")


class DataModelNameMappingTransport(PythonCoreBaseModel):
    name_mappings: Optional["List[Optional[NameMappingTransport]]"] = Field(None, alias="nameMappings")
    name_mapping_enabled: Optional["bool"] = Field(None, alias="nameMappingEnabled")


class DataLoadFactoryCalendarTransport(PythonCoreBaseModel):
    calendar_id: Optional["str"] = Field(None, alias="calendarId")
    year: Optional["str"] = Field(None, alias="year")
    month_day_masks: Optional["List[Optional[str]]"] = Field(None, alias="monthDayMasks")


class DataPoolVersionInfo(PythonCoreBaseModel):
    draft_id: Optional["str"] = Field(None, alias="draftId")
    active: Optional["bool"] = Field(None, alias="active")
    version: Optional["str"] = Field(None, alias="version")


class ProcessDataModelTransport(PythonCoreBaseModel):
    loaded: Optional["bool"] = Field(None, alias="loaded")
    allow_raw_data_export: Optional["bool"] = Field(None, alias="allowRawDataExport")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    case_id_column_id: Optional["str"] = Field(None, alias="caseIdColumnId")
    case_table_id: Optional["str"] = Field(None, alias="caseTableId")
    activity_table_id: Optional["str"] = Field(None, alias="activityTableId")
    tables: Optional["List[Optional[DataTableTransport]]"] = Field(None, alias="tables")
    foreign_keys: Optional["List[Optional[ForeignKeyTransport]]"] = Field(None, alias="foreignKeys")
    data_model_load: Optional["DataModelLoadTransport"] = Field(None, alias="dataModelLoad")
    custom_calendar: Optional["List[Optional[CustomCalendar]]"] = Field(None, alias="customCalendar")
    general_translations: Optional["List[Optional[NameMappingTransport]]"] = Field(None, alias="generalTranslations")
    name_mapping_enabled: Optional["bool"] = Field(None, alias="nameMappingEnabled")


class PqlCategoryTransport(PythonCoreBaseModel):
    title: Optional["str"] = Field(None, alias="title")
    description: Optional["str"] = Field(None, alias="description")
    audience: Optional["str"] = Field(None, alias="audience")
    pql_help_url: Optional["str"] = Field(None, alias="pqlHelpUrl")


class PqlOperatorTransport(PythonCoreBaseModel):
    title: Optional["str"] = Field(None, alias="title")
    category: Optional["str"] = Field(None, alias="category")
    description: Optional["str"] = Field(None, alias="description")
    syntax: Optional["List[Optional[PqlSyntaxTransport]]"] = Field(None, alias="syntax")


class PqlReferenceTransport(PythonCoreBaseModel):
    pql_categories: Optional["List[Optional[PqlCategoryTransport]]"] = Field(None, alias="pqlCategories")
    pql_operators: Optional["List[Optional[PqlOperatorTransport]]"] = Field(None, alias="pqlOperators")


class PqlSyntaxTransport(PythonCoreBaseModel):
    text: Optional["str"] = Field(None, alias="text")
    snippet: Optional["str"] = Field(None, alias="snippet")


class ComputeAcceleratorVersionTransport(PythonCoreBaseModel):
    major: Optional["int"] = Field(None, alias="major")
    minor: Optional["int"] = Field(None, alias="minor")
    patch: Optional["int"] = Field(None, alias="patch")


class DataStateTransport(PythonCoreBaseModel):
    group_states: Optional["List[Optional[GroupStateTransport]]"] = Field(None, alias="groupStates")
    description: Optional["str"] = Field(None, alias="description")
    memory_consumption: Optional["int"] = Field(None, alias="memoryConsumption")
    disk_consumption: Optional["int"] = Field(None, alias="diskConsumption")


class EntityStateTransport(PythonCoreBaseModel):
    description: Optional["str"] = Field(None, alias="description")
    status: Optional["str"] = Field(None, alias="status")
    size_in_memory: Optional["int"] = Field(None, alias="sizeInMemory")
    size_on_disk: Optional["int"] = Field(None, alias="sizeOnDisk")
    access_count: Optional["int"] = Field(None, alias="accessCount")
    last_access: Optional["str"] = Field(None, alias="lastAccess")


class GroupStateTransport(PythonCoreBaseModel):
    entities: Optional["List[Optional[EntityStateTransport]]"] = Field(None, alias="entities")
    description: Optional["str"] = Field(None, alias="description")
    status: Optional["str"] = Field(None, alias="status")


class HybridCapabilities(PythonCoreBaseModel):
    log_export_enabled: Optional["bool"] = Field(None, alias="logExportEnabled")


class ClusterMemberState(PythonCoreBaseModel):
    cluster_version: Optional["str"] = Field(None, alias="clusterVersion")
    distributed_caching_enabled: Optional["bool"] = Field(None, alias="distributedCachingEnabled")
    distributed_caching_suspended: Optional["bool"] = Field(None, alias="distributedCachingSuspended")


class HybridBuildInfoTransport(PythonCoreBaseModel):
    version: Optional["str"] = Field(None, alias="version")
    name: Optional["str"] = Field(None, alias="name")
    group: Optional["str"] = Field(None, alias="group")
    build_time: Optional["PythonCoreDatetime"] = Field(None, alias="buildTime")
    pool_provider_info: Optional["HybridStatusPoolProviderInfo"] = Field(None, alias="poolProviderInfo")


class HybridStatusInfoResponse(PythonCoreBaseModel):
    build_info: Optional["HybridBuildInfoTransport"] = Field(None, alias="buildInfo")
    process_mining_engine_connected: Optional["bool"] = Field(None, alias="processMiningEngineConnected")


class HybridStatusPoolProviderInfo(PythonCoreBaseModel):
    type_: Optional["PoolProviderType"] = Field(None, alias="type")
    database_type: Optional["DatabaseType"] = Field(None, alias="databaseType")


class FeaturesTransport(PythonCoreBaseModel):
    standalone: Optional["bool"] = Field(None, alias="standalone")
    hybrid: Optional["bool"] = Field(None, alias="hybrid")


class ZendeskRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class ServiceNowRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class InternalSystemTransport(PythonCoreBaseModel):
    internal_system_id: Optional["str"] = Field(None, alias="internalSystemId")
    internal_system_name: Optional["str"] = Field(None, alias="internalSystemName")


class SalesforceRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class GoogleSheetsRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class CustomExtractorRedirectTransport(PythonCoreBaseModel):
    redirect_url: Optional["str"] = Field(None, alias="redirectUrl")


class DatabaseConnectionInputTemplate(PythonCoreBaseModel):
    server_name_displayed: Optional["bool"] = Field(None, alias="serverNameDisplayed")
    database_name_displayed: Optional["bool"] = Field(None, alias="databaseNameDisplayed")
    service_name_displayed: Optional["bool"] = Field(None, alias="serviceNameDisplayed")
    warehouse_name_displayed: Optional["bool"] = Field(None, alias="warehouseNameDisplayed")
    schema_name_displayed: Optional["bool"] = Field(None, alias="schemaNameDisplayed")
    username_displayed: Optional["bool"] = Field(None, alias="usernameDisplayed")
    password_displayed: Optional["bool"] = Field(None, alias="passwordDisplayed")
    certificate_validation_displayed: Optional["bool"] = Field(None, alias="certificateValidationDisplayed")
    region_displayed: Optional["bool"] = Field(None, alias="regionDisplayed")
    output_location_displayed: Optional["bool"] = Field(None, alias="outputLocationDisplayed")
    display_live_data_connection: Optional["bool"] = Field(None, alias="displayLiveDataConnection")
    extract_row_id_displayed: Optional["bool"] = Field(None, alias="extractRowIdDisplayed")
    client_id_displayed: Optional["bool"] = Field(None, alias="clientIdDisplayed")
    client_secret_displayed: Optional["bool"] = Field(None, alias="clientSecretDisplayed")
    principal_id_displayed: Optional["bool"] = Field(None, alias="principalIdDisplayed")
    principal_secret_displayed: Optional["bool"] = Field(None, alias="principalSecretDisplayed")
    service_acct_email_displayed: Optional["bool"] = Field(None, alias="serviceAcctEmailDisplayed")
    service_acct_creds_displayed: Optional["bool"] = Field(None, alias="serviceAcctCredsDisplayed")
    private_key_displayed: Optional["bool"] = Field(None, alias="privateKeyDisplayed")
    http_path_displayed: Optional["bool"] = Field(None, alias="httpPathDisplayed")
    personal_access_token_displayed: Optional["bool"] = Field(None, alias="personalAccessTokenDisplayed")


class DatabaseConnectionTemplate(PythonCoreBaseModel):
    default_binary_handling_option: Optional["BinaryHandlingOption"] = Field(None, alias="defaultBinaryHandlingOption")
    available_authentication_methods: Optional["List[Optional[DatabaseAuthenticationMethod]]"] = Field(
        None, alias="availableAuthenticationMethods"
    )
    default_authentication_method: Optional["DatabaseAuthenticationMethod"] = Field(
        None, alias="defaultAuthenticationMethod"
    )
    default_schema_name: Optional["str"] = Field(None, alias="defaultSchemaName")
    version_query: Optional["str"] = Field(None, alias="versionQuery")
    version_number_query: Optional["str"] = Field(None, alias="versionNumberQuery")
    limit_and_offset_syntax: Optional["LimitAndOffsetStatementSyntax"] = Field(None, alias="limitAndOffsetSyntax")
    required_schema_set: Optional["List[Optional[str]]"] = Field(None, alias="requiredSchemaSet")
    metadata_options: Optional["DatabaseMetadataOptions"] = Field(None, alias="metadataOptions")
    ware_house_query: Optional["str"] = Field(None, alias="wareHouseQuery")
    default_batch_size: Optional["int"] = Field(None, alias="defaultBatchSize")
    table_types: Optional["List[Optional[str]]"] = Field(None, alias="tableTypes")
    validation_query: Optional["str"] = Field(None, alias="validationQuery")
    auto_commit: Optional["AutoCommit"] = Field(None, alias="autoCommit")
    input_fields_template: Optional["DatabaseConnectionInputTemplate"] = Field(None, alias="inputFieldsTemplate")
    driver_name: Optional["str"] = Field(None, alias="driverName")
    redirect_url_key: Optional["str"] = Field(None, alias="redirectUrlKey")
    display_name: Optional["str"] = Field(None, alias="displayName")
    id: Optional["str"] = Field(None, alias="id")
    default_port: Optional["int"] = Field(None, alias="defaultPort")


class DatabaseMetadataOptions(PythonCoreBaseModel):
    supported_metadata_sources: Optional["List[Optional[DatabaseMetadataSource]]"] = Field(
        None, alias="supportedMetadataSources"
    )


class DataUploaderServeDataTransport(PythonCoreBaseModel):
    serve_url: Optional["str"] = Field(None, alias="serveUrl")


class DataPipelineOrchestratorServeDataTransport(PythonCoreBaseModel):
    serve_url: Optional["str"] = Field(None, alias="serveUrl")


class DataPipelineHistoryServeDataTransport(PythonCoreBaseModel):
    serve_url: Optional["str"] = Field(None, alias="serveUrl")


class DataModelCreationRestriction(PythonCoreBaseModel):
    number_of_existing_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingProcessConfigurations"
    )
    number_of_existing_data_models_without_process_configurations: Optional["int"] = Field(
        None, alias="numberOfExistingDataModelsWithoutProcessConfigurations"
    )
    number_of_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfProcessConfigurationsToCreate"
    )
    number_of_data_models_without_process_configurations_to_create: Optional["int"] = Field(
        None, alias="numberOfDataModelsWithoutProcessConfigurationsToCreate"
    )
    number_of_licensed_processes: Optional["int"] = Field(None, alias="numberOfLicensedProcesses")
    unlimited_number_of_licensed_data_models: Optional["bool"] = Field(
        None, alias="unlimitedNumberOfLicensedDataModels"
    )
    number_of_installable_processes: Optional["int"] = Field(None, alias="numberOfInstallableProcesses")
    number_of_processes_to_create: Optional["int"] = Field(None, alias="numberOfProcessesToCreate")
    number_of_existing_processes: Optional["int"] = Field(None, alias="numberOfExistingProcesses")
    can_create_data_model: Optional["bool"] = Field(None, alias="canCreateDataModel")
    monitoring_target_pool: Optional["bool"] = Field(None, alias="monitoringTargetPool")


class ConnectorList(PythonCoreBaseModel):
    cloud_connectors: Optional["List[Optional[ConnectorTransport]]"] = Field(None, alias="cloudConnectors")
    on_premise_connectors: Optional["List[Optional[ConnectorTransport]]"] = Field(None, alias="onPremiseConnectors")
    custom_extractors: Optional["List[Optional[CustomExtractorTransport]]"] = Field(None, alias="customExtractors")
    streaming_connectors: Optional["List[Optional[ConnectorTransport]]"] = Field(None, alias="streamingConnectors")


class ConnectorTransport(PythonCoreBaseModel):
    type_: Optional["str"] = Field(None, alias="type")
    default_to_uplink: Optional["bool"] = Field(None, alias="defaultToUplink")
    hide_uplink_option: Optional["bool"] = Field(None, alias="hideUplinkOption")
    show_uplink_option_by_feature: Optional["bool"] = Field(None, alias="showUplinkOptionByFeature")
    override_to_on_prem: Optional["bool"] = Field(None, alias="overrideToOnPrem")
    on_premise_connector: Optional["bool"] = Field(None, alias="onPremiseConnector")
    cloud_connector: Optional["bool"] = Field(None, alias="cloudConnector")
    custom_extractor: Optional["bool"] = Field(None, alias="customExtractor")
    custom_extractor_name: Optional["str"] = Field(None, alias="customExtractorName")
    configuration_handler: Optional["str"] = Field(None, alias="configurationHandler")


class SwaggerResource(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    url: Optional["str"] = Field(None, alias="url")
    swagger_version: Optional["str"] = Field(None, alias="swaggerVersion")
    location: Optional["str"] = Field(None, alias="location")


class UiConfiguration(PythonCoreBaseModel):
    apis_sorter: Optional["str"] = Field(None, alias="apisSorter")
    supported_submit_methods: Optional["List[Optional[str]]"] = Field(None, alias="supportedSubmitMethods")
    json_editor: Optional["bool"] = Field(None, alias="jsonEditor")
    show_request_headers: Optional["bool"] = Field(None, alias="showRequestHeaders")
    deep_linking: Optional["bool"] = Field(None, alias="deepLinking")
    display_operation_id: Optional["bool"] = Field(None, alias="displayOperationId")
    default_models_expand_depth: Optional["int"] = Field(None, alias="defaultModelsExpandDepth")
    default_model_expand_depth: Optional["int"] = Field(None, alias="defaultModelExpandDepth")
    default_model_rendering: Optional["ModelRendering"] = Field(None, alias="defaultModelRendering")
    display_request_duration: Optional["bool"] = Field(None, alias="displayRequestDuration")
    doc_expansion: Optional["DocExpansion"] = Field(None, alias="docExpansion")
    filter: Optional["Any"] = Field(None, alias="filter")
    max_displayed_tags: Optional["int"] = Field(None, alias="maxDisplayedTags")
    operations_sorter: Optional["OperationsSorter"] = Field(None, alias="operationsSorter")
    show_extensions: Optional["bool"] = Field(None, alias="showExtensions")
    tags_sorter: Optional["TagsSorter"] = Field(None, alias="tagsSorter")
    validator_url: Optional["str"] = Field(None, alias="validatorUrl")


class SecurityConfiguration(PythonCoreBaseModel):
    api_key: Optional["str"] = Field(None, alias="apiKey")
    api_key_vehicle: Optional["str"] = Field(None, alias="apiKeyVehicle")
    api_key_name: Optional["str"] = Field(None, alias="apiKeyName")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    realm: Optional["str"] = Field(None, alias="realm")
    app_name: Optional["str"] = Field(None, alias="appName")
    scope_separator: Optional["str"] = Field(None, alias="scopeSeparator")
    additional_query_string_params: Optional["Dict[str, Optional[Any]]"] = Field(
        None, alias="additionalQueryStringParams"
    )
    use_basic_authentication_with_access_code_grant: Optional["bool"] = Field(
        None, alias="useBasicAuthenticationWithAccessCodeGrant"
    )


class CustomConfigurationTransport(PoolProviderTransport, PythonCoreBaseModel):
    pass


class DatabaseConfigurationTransport(PoolProviderTransport, PythonCoreBaseModel):
    url: Optional["str"] = Field(None, alias="url")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    type_: Optional["DatabaseType"] = Field(None, alias="type")
    tenancy: Optional["DatabaseTenancyType"] = Field(None, alias="tenancy")


class VerticaConfigurationTransport(PoolProviderTransport, PythonCoreBaseModel):
    vertica_hosts: Optional["str"] = Field(None, alias="verticaHosts")


class ZendeskConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    username: Optional["str"] = Field(None, alias="username")
    auth_method: Optional["ZendeskAuthMethods"] = Field(None, alias="authMethod")
    access_token: Optional["str"] = Field(None, alias="accessToken")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    password: Optional["str"] = Field(None, alias="password")
    realm: Optional["str"] = Field(None, alias="realm")


class WorkdayConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    tenant: Optional["str"] = Field(None, alias="tenant")
    host: Optional["str"] = Field(None, alias="host")
    api_version: Optional["WorkdayApiVersion"] = Field(None, alias="apiVersion")
    report_configurations: Optional["List[Optional[WorkdayReportConfiguration]]"] = Field(
        None, alias="reportConfigurations"
    )
    auth_method: Optional["WorkdayAuthMethods"] = Field(None, alias="authMethod")
    client_id: Optional["str"] = Field(None, alias="clientId")
    user_id: Optional["str"] = Field(None, alias="userId")
    private_key: Optional["str"] = Field(None, alias="privateKey")
    access_token: Optional["str"] = Field(None, alias="accessToken")


class UiPathConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    tenant: Optional["str"] = Field(None, alias="tenant")
    host: Optional["str"] = Field(None, alias="host")
    extract_complete_robot_log: Optional["bool"] = Field(None, alias="extractCompleteRobotLog")
    extract_celonis_log: Optional["bool"] = Field(None, alias="extractCelonisLog")
    organization_unit_id: Optional["str"] = Field(None, alias="organizationUnitId")


class SuccessFactorsConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    hostname: Optional["str"] = Field(None, alias="hostname")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    sandbox_api_key: Optional["str"] = Field(None, alias="sandboxApiKey")
    environment: Optional["DataSourceEnvironment"] = Field(None, alias="environment")


class SnowflakeRestConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    host: Optional["str"] = Field(None, alias="host")
    database: Optional["str"] = Field(None, alias="database")
    warehouse: Optional["str"] = Field(None, alias="warehouse")
    schema_: Optional["str"] = Field(None, alias="schema")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    access_token: Optional["str"] = Field(None, alias="accessToken")


class ServiceNowConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    tenant: Optional["str"] = Field(None, alias="tenant")
    user: Optional["str"] = Field(None, alias="user")
    auth_method: Optional["ServiceNowAuthMethods"] = Field(None, alias="authMethod")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    access_token: Optional["str"] = Field(None, alias="accessToken")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    password: Optional["str"] = Field(None, alias="password")
    execution_configuration: Optional["ServiceNowExecutionConfiguration"] = Field(None, alias="executionConfiguration")
    live_data_connection: Optional["bool"] = Field(None, alias="liveDataConnection")


class SapSnsConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    tenant: Optional["str"] = Field(None, alias="tenant")
    api_version: Optional["SapSnsVersions"] = Field(None, alias="apiVersion")


class SapMarketingCloudConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    tenant: Optional["str"] = Field(None, alias="tenant")


class SalesforceConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    client_id: Optional["str"] = Field(None, alias="clientId")
    consumer_key: Optional["str"] = Field(None, alias="consumerKey")
    instance_url: Optional["str"] = Field(None, alias="instanceUrl")
    username: Optional["str"] = Field(None, alias="username")
    environment: Optional["DataSourceEnvironment"] = Field(None, alias="environment")
    auth_method: Optional["SalesForceAuthMethods"] = Field(None, alias="authMethod")
    use_api_key: Optional["bool"] = Field(None, alias="useApiKey")
    password: Optional["str"] = Field(None, alias="password")
    consumer_secret: Optional["str"] = Field(None, alias="consumerSecret")
    platform_event_channel_name: Optional["str"] = Field(None, alias="platformEventChannelName")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    application_key: Optional["str"] = Field(None, alias="applicationKey")
    proxy_service: Optional["SalesforceProxyService"] = Field(None, alias="proxyService")
    authorize_url: Optional["str"] = Field(None, alias="authorizeUrl")
    token_url: Optional["str"] = Field(None, alias="tokenUrl")
    data_url: Optional["str"] = Field(None, alias="dataUrl")


class RossumConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    queue: Optional["str"] = Field(None, alias="queue")
    status: Optional["str"] = Field(None, alias="status")
    access_token: Optional["str"] = Field(None, alias="accessToken")


class PythonConnectorConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    parameters: Optional["List[Optional[PythonConnectorConnectionConfigurationParameter]]"] = Field(
        None, alias="parameters"
    )
    sub_type: Optional["str"] = Field(None, alias="subType")


class OracleCloudConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    host: Optional["str"] = Field(None, alias="host")
    instance_version: Optional["OracleCloudInstanceVersions"] = Field(None, alias="instanceVersion")


class MicrosoftDynamics365ConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    host: Optional["str"] = Field(None, alias="host")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    access_token: Optional["str"] = Field(None, alias="accessToken")
    tenant: Optional["str"] = Field(None, alias="tenant")


class KafkaConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    topics: Optional["List[Optional[KafkaTopicConfiguration]]"] = Field(None, alias="topics")
    api_key: Optional["str"] = Field(None, alias="apiKey")


class JiraConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    instance_url: Optional["str"] = Field(None, alias="instanceURL")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")


class HappyFoxConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    auth_code: Optional["str"] = Field(None, alias="authCode")
    host: Optional["str"] = Field(None, alias="host")


class GoogleSheetsConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    spreadsheet_url: Optional["str"] = Field(None, alias="spreadsheetUrl")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    environment: Optional["DataSourceEnvironment"] = Field(None, alias="environment")


class FieldglassConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    api_group: Optional["FieldglassApiGroup"] = Field(None, alias="apiGroup")
    host: Optional["str"] = Field(None, alias="host")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    application_key: Optional["str"] = Field(None, alias="applicationKey")


class EventHubConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    use_api_key: Optional["bool"] = Field(None, alias="useApiKey")
    event_hubs: Optional["List[Optional[EventHubConfiguration]]"] = Field(None, alias="eventHubs")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    application_key: Optional["str"] = Field(None, alias="applicationKey")


class CustomConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")


class CustomExtractorConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    custom_extractor_id: Optional["str"] = Field(None, alias="customExtractorId")
    custom_extractor_configuration: Optional["CustomExtractorConfiguration"] = Field(
        None, alias="customExtractorConfiguration"
    )
    authentication_method: Optional["CustomExtractorAuthenticationMethod"] = Field(None, alias="authenticationMethod")
    parameters: Optional["List[Optional[CustomExtractorConnectionConnfigurationParameter]]"] = Field(
        None, alias="parameters"
    )
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    token: Optional["str"] = Field(None, alias="token")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    use_celonis_client_and_secret: Optional["bool"] = Field(None, alias="useCelonisClientAndSecret")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    access_token: Optional["str"] = Field(None, alias="accessToken")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    issuer: Optional["str"] = Field(None, alias="issuer")
    audience: Optional["str"] = Field(None, alias="audience")
    subject: Optional["str"] = Field(None, alias="subject")
    private_key: Optional["str"] = Field(None, alias="privateKey")
    socket_timeout_seconds: Optional["int"] = Field(None, alias="socketTimeoutSeconds")


class CoupaConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    instance_name: Optional["str"] = Field(None, alias="instanceName")
    auth_method: Optional["CoupaAuthMethods"] = Field(None, alias="authMethod")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    access_token: Optional["str"] = Field(None, alias="accessToken")
    oidc_scopes: Optional["str"] = Field(None, alias="oidcScopes")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    api_version: Optional["CoupaApiVersion"] = Field(None, alias="apiVersion")


class CelonisActionEngineConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    host: Optional["str"] = Field(None, alias="host")
    api_token: Optional["str"] = Field(None, alias="apiToken")


class BiPublisherConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    host: Optional["str"] = Field(None, alias="host")
    report_configurations: Optional["List[Optional[BiPublisherReportConfiguration]]"] = Field(
        None, alias="reportConfigurations"
    )
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")


class AzureServiceBusConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    use_api_key: Optional["bool"] = Field(None, alias="useApiKey")
    subscriptions: Optional["List[Optional[AzureServiceBusSubscriptionConfiguration]]"] = Field(
        None, alias="subscriptions"
    )
    api_key: Optional["str"] = Field(None, alias="apiKey")
    application_key: Optional["str"] = Field(None, alias="applicationKey")


class AutomationAnywhereConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    host: Optional["str"] = Field(None, alias="host")
    get_available_bots_date: Optional["str"] = Field(None, alias="getAvailableBotsDate")


class AribaConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    realm: Optional["str"] = Field(None, alias="realm")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    pipo_host: Optional["str"] = Field(None, alias="pipoHost")
    adapter: Optional["str"] = Field(None, alias="adapter")
    use_custom_request: Optional["bool"] = Field(None, alias="useCustomRequest")
    getx_tenant: Optional["str"] = Field(None, alias="getxTenant")
    getx_system: Optional["str"] = Field(None, alias="getxSystem")
    getx_an_id: Optional["str"] = Field(None, alias="getxAnId")
    view_template_request: Optional["str"] = Field(None, alias="viewTemplateRequest")
    metadata_request: Optional["str"] = Field(None, alias="metadataRequest")
    job_submission_request: Optional["str"] = Field(None, alias="jobSubmissionRequest")
    job_result_request: Optional["str"] = Field(None, alias="jobResultRequest")
    job_status_request: Optional["str"] = Field(None, alias="jobStatusRequest")
    use_pipo: Optional["bool"] = Field(None, alias="usePIPO")
    display_state_string: Optional["bool"] = Field(None, alias="displayStateString")
    ariba_proxy_service: Optional["AribaProxyService"] = Field(None, alias="aribaProxyService")
    region: Optional["AribaRegion"] = Field(None, alias="region")
    api_group: Optional["AribaApiGroup"] = Field(None, alias="apiGroup")
    table_execution_configurations: Optional["List[Optional[AribaTableExecutionConfiguration]]"] = Field(
        None, alias="tableExecutionConfigurations"
    )


class AmazonS3ConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    region: Optional["AmazonS3Region"] = Field(None, alias="region")
    bucket: Optional["str"] = Field(None, alias="bucket")
    access_key_id: Optional["str"] = Field(None, alias="accessKeyId")
    access_key_secret: Optional["str"] = Field(None, alias="accessKeySecret")
    session_token: Optional["str"] = Field(None, alias="sessionToken")
    use_temporary_credentials: Optional["bool"] = Field(None, alias="useTemporaryCredentials")
    customize_prefixes: Optional["bool"] = Field(None, alias="customizePrefixes")
    prefixes: Optional["List[Optional[str]]"] = Field(None, alias="prefixes")


class PoolProviderCopyTableQuery(PoolProviderQueryTransport, PythonCoreBaseModel):
    source_table_name: Optional["str"] = Field(None, alias="sourceTableName")
    target_table_name: Optional["str"] = Field(None, alias="targetTableName")


class PoolProviderCreateTableQuery(PoolProviderQueryTransport, PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    columns: Optional["List[Optional[DataPoolProviderColumn]]"] = Field(None, alias="columns")


class PoolProviderSelectTableQuery(PoolProviderQueryTransport, PythonCoreBaseModel):
    select_expressions: Optional["List[Optional[SelectExpression]]"] = Field(None, alias="selectExpressions")
    table_name: Optional["str"] = Field(None, alias="tableName")


class DatabaseProviderConnectionDetails(PoolProviderConnectionDetails, PythonCoreBaseModel):
    database_type: Optional["DatabaseType"] = Field(None, alias="databaseType")


class SnowflakeProviderConnectionDetails(PoolProviderConnectionDetails, PythonCoreBaseModel):
    database: Optional["str"] = Field(None, alias="database")
    ware_house: Optional["str"] = Field(None, alias="wareHouse")
    host: Optional["str"] = Field(None, alias="host")


class VerticaProviderConnectionDetails(PoolProviderConnectionDetails, PythonCoreBaseModel):
    database: Optional["str"] = Field(None, alias="database")
    hosts: Optional["List[Optional[str]]"] = Field(None, alias="hosts")


class AribaConnectionConfigurationV2(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    realm: Optional["str"] = Field(None, alias="realm")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    api_key: Optional["str"] = Field(None, alias="apiKey")
    username: Optional["str"] = Field(None, alias="username")
    password: Optional["str"] = Field(None, alias="password")
    pipo_host: Optional["str"] = Field(None, alias="pipoHost")
    adapter: Optional["str"] = Field(None, alias="adapter")
    use_custom_request: Optional["bool"] = Field(None, alias="useCustomRequest")
    getx_tenant: Optional["str"] = Field(None, alias="getxTenant")
    getx_system: Optional["str"] = Field(None, alias="getxSystem")
    getx_an_id: Optional["str"] = Field(None, alias="getxAnId")
    view_template_request: Optional["str"] = Field(None, alias="viewTemplateRequest")
    metadata_request: Optional["str"] = Field(None, alias="metadataRequest")
    job_submission_request: Optional["str"] = Field(None, alias="jobSubmissionRequest")
    job_result_request: Optional["str"] = Field(None, alias="jobResultRequest")
    job_status_request: Optional["str"] = Field(None, alias="jobStatusRequest")
    use_pipo: Optional["bool"] = Field(None, alias="usePIPO")
    display_state_string: Optional["bool"] = Field(None, alias="displayStateString")
    ariba_proxy_service: Optional["AribaProxyService"] = Field(None, alias="aribaProxyService")
    region: Optional["AribaRegion"] = Field(None, alias="region")
    api_group: Optional["AribaApiGroup"] = Field(None, alias="apiGroup")
    table_execution_configurations: Optional["List[Optional[AribaTableExecutionConfiguration]]"] = Field(
        None, alias="tableExecutionConfigurations"
    )


class DatabaseConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    template_id: Optional["str"] = Field(None, alias="templateId")
    authentication_method: Optional["DatabaseAuthenticationMethod"] = Field(None, alias="authenticationMethod")
    server_name: Optional["str"] = Field(None, alias="serverName")
    port: Optional["int"] = Field(None, alias="port")
    database_name: Optional["str"] = Field(None, alias="databaseName")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    warehouse_name: Optional["str"] = Field(None, alias="warehouseName")
    use_custom_string: Optional["bool"] = Field(None, alias="useCustomString")
    custom_string: Optional["str"] = Field(None, alias="customString")
    connection_string_additional: Optional["str"] = Field(None, alias="connectionStringAdditional")
    custom_driver_class: Optional["str"] = Field(None, alias="customDriverClass")
    username: Optional["str"] = Field(None, alias="username")
    region: Optional["str"] = Field(None, alias="region")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    connection_timeout: Optional["int"] = Field(None, alias="connectionTimeout")
    password: Optional["str"] = Field(None, alias="password")
    output_location: Optional["str"] = Field(None, alias="outputLocation")
    live_data_connection: Optional["bool"] = Field(None, alias="liveDataConnection")
    extract_row_id: Optional["bool"] = Field(None, alias="extractRowId")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    principal_id: Optional["str"] = Field(None, alias="principalId")
    principal_secret: Optional["str"] = Field(None, alias="principalSecret")
    service_account_email_id: Optional["str"] = Field(None, alias="serviceAccountEmailId")
    service_account_credentials: Optional["str"] = Field(None, alias="serviceAccountCredentials")
    encrypted_key: Optional["bool"] = Field(None, alias="encryptedKey")
    private_key_file_path: Optional["bool"] = Field(None, alias="privateKeyFilePath")
    private_key_passphrase: Optional["str"] = Field(None, alias="privateKeyPassphrase")
    private_key: Optional["str"] = Field(None, alias="privateKey")
    http_path: Optional["str"] = Field(None, alias="httpPath")
    personal_access_token: Optional["str"] = Field(None, alias="personalAccessToken")


class DemoSapConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    host: Optional["str"] = Field(None, alias="host")
    system_number: Optional["str"] = Field(None, alias="systemNumber")
    client: Optional["str"] = Field(None, alias="client")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    compression_type: Optional["CompressionType"] = Field(None, alias="compressionType")


class DemoServiceNowConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    template_id: Optional["str"] = Field(None, alias="templateId")
    authentication_method: Optional["DatabaseAuthenticationMethod"] = Field(None, alias="authenticationMethod")
    server_name: Optional["str"] = Field(None, alias="serverName")
    port: Optional["int"] = Field(None, alias="port")
    database_name: Optional["str"] = Field(None, alias="databaseName")
    schema_name: Optional["str"] = Field(None, alias="schemaName")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    warehouse_name: Optional["str"] = Field(None, alias="warehouseName")
    use_custom_string: Optional["bool"] = Field(None, alias="useCustomString")
    custom_string: Optional["str"] = Field(None, alias="customString")
    connection_string_additional: Optional["str"] = Field(None, alias="connectionStringAdditional")
    custom_driver_class: Optional["str"] = Field(None, alias="customDriverClass")
    username: Optional["str"] = Field(None, alias="username")
    region: Optional["str"] = Field(None, alias="region")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    connection_timeout: Optional["int"] = Field(None, alias="connectionTimeout")
    password: Optional["str"] = Field(None, alias="password")
    output_location: Optional["str"] = Field(None, alias="outputLocation")
    live_data_connection: Optional["bool"] = Field(None, alias="liveDataConnection")
    extract_row_id: Optional["bool"] = Field(None, alias="extractRowId")
    client_id: Optional["str"] = Field(None, alias="clientId")
    client_secret: Optional["str"] = Field(None, alias="clientSecret")
    refresh_token: Optional["str"] = Field(None, alias="refreshToken")
    principal_id: Optional["str"] = Field(None, alias="principalId")
    principal_secret: Optional["str"] = Field(None, alias="principalSecret")
    service_account_email_id: Optional["str"] = Field(None, alias="serviceAccountEmailId")
    service_account_credentials: Optional["str"] = Field(None, alias="serviceAccountCredentials")
    encrypted_key: Optional["bool"] = Field(None, alias="encryptedKey")
    private_key_file_path: Optional["bool"] = Field(None, alias="privateKeyFilePath")
    private_key_passphrase: Optional["str"] = Field(None, alias="privateKeyPassphrase")
    private_key: Optional["str"] = Field(None, alias="privateKey")
    http_path: Optional["str"] = Field(None, alias="httpPath")
    personal_access_token: Optional["str"] = Field(None, alias="personalAccessToken")
    default_tenant_value: Optional["str"] = Field(None, alias="defaultTenantValue")
    default_service_now_username: Optional["str"] = Field(None, alias="defaultServiceNowUsername")
    default_service_now_password: Optional["str"] = Field(None, alias="defaultServiceNowPassword")


class ImportedConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")


class PardotConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    number_of_threads: Optional["int"] = Field(None, alias="numberOfThreads")
    custom_json_configuration: Optional["str"] = Field(None, alias="customJsonConfiguration")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    api_key: Optional["str"] = Field(None, alias="apiKey")


class SapConnectionConfiguration(ConnectionConfiguration, PythonCoreBaseModel):
    host: Optional["str"] = Field(None, alias="host")
    system_number: Optional["str"] = Field(None, alias="systemNumber")
    client: Optional["str"] = Field(None, alias="client")
    user: Optional["str"] = Field(None, alias="user")
    password: Optional["str"] = Field(None, alias="password")
    parallel_tables: Optional["int"] = Field(None, alias="parallelTables")
    compression_type: Optional["CompressionType"] = Field(None, alias="compressionType")


ExceptionReference.model_rebuild()
FrontendHandledBackendError.model_rebuild()
PoolVariableTransport.model_rebuild()
VariableSettingsTransport.model_rebuild()
VariableValueTransport.model_rebuild()
TaskTemplateTransport.model_rebuild()
TaskVariableTransport.model_rebuild()
StreamingColumnTransport.model_rebuild()
StreamingTableTransport.model_rebuild()
SchedulingTransport.model_rebuild()
DataPoolSchedulingOverviewFilterTransport.model_rebuild()
DataPoolSchedulingOverviewTransport.model_rebuild()
SchedulingIdAndNameTransport.model_rebuild()
TransformationTransport.model_rebuild()
TaskUpdate.model_rebuild()
TaskInstanceTransport.model_rebuild()
DataModelExecutionTableItem.model_rebuild()
DataModelExecutionTransport.model_rebuild()
CalculatedColumnTransport.model_rebuild()
TableConfigurationParameterValue.model_rebuild()
TableExtractionColumnTransport.model_rebuild()
TableExtractionJoinTransport.model_rebuild()
TableExtractionTransport.model_rebuild()
ColumnTransport.model_rebuild()
ExtractionConfigurationValueTransport.model_rebuild()
ExtractionWithTablesTransport.model_rebuild()
TableTransport.model_rebuild()
JobTransport.model_rebuild()
DataPoolDataJobOverviewFilterTransport.model_rebuild()
DataJobIdAndNameTransport.model_rebuild()
DataPoolDataJobOverviewTransport.model_rebuild()
JobSchedulingTransport.model_rebuild()
FileDataTable.model_rebuild()
FileDataColumn.model_rebuild()
CustomExtractorAuthenticationConfiguration.model_rebuild()
CustomExtractorColumn.model_rebuild()
CustomExtractorConfiguration.model_rebuild()
CustomExtractorConnectionParameter.model_rebuild()
CustomExtractorEndpoint.model_rebuild()
CustomExtractorEndpointResponse.model_rebuild()
CustomExtractorErrorHandlingRule.model_rebuild()
CustomExtractorFilteringSyntax.model_rebuild()
CustomExtractorNestedTable.model_rebuild()
CustomExtractorPagination.model_rebuild()
CustomExtractorPaginationData.model_rebuild()
CustomExtractorRequestParameter.model_rebuild()
CustomExtractorTransport.model_rebuild()
CustomFieldParameter.model_rebuild()
CustomExtractorAuthenticationTransport.model_rebuild()
DataTransferExportCreateEditTransport.model_rebuild()
DataTransferExportTableTransport.model_rebuild()
DataTransferExportSlimTransport.model_rebuild()
DataPoolDataSourceOverviewFilterTransport.model_rebuild()
DataPoolDataSourceOverviewTransport.model_rebuild()
DataSourceOverviewTransport.model_rebuild()
DataModelColumnTransport.model_rebuild()
DataModelConfigurationTransport.model_rebuild()
DataModelCustomCalendarEntryTransport.model_rebuild()
DataModelCustomCalendarTransport.model_rebuild()
DataModelFactoryCalendarTransport.model_rebuild()
DataModelForeignKeyColumnTransport.model_rebuild()
DataModelForeignKeyTransport.model_rebuild()
DataModelTableTransport.model_rebuild()
DataModelTransport.model_rebuild()
DataModelSignalLinkColumnNameTransport.model_rebuild()
DataModelSignalLinkColumnTransport.model_rebuild()
DataModelSignalLinkMappingColumnTransport.model_rebuild()
DataModelSignalLinkMappingTransport.model_rebuild()
DataModelSignalLinkTransport.model_rebuild()
DataModelConfiguration.model_rebuild()
ParallelProcessConfiguration.model_rebuild()
DataModelGraphPositioningTransport.model_rebuild()
DataModelTablePosition.model_rebuild()
DataPermission.model_rebuild()
DataPermissionSyncTableTransport.model_rebuild()
DataPermissionTableTransport.model_rebuild()
DataPermissionAssignmentTransport.model_rebuild()
GroupTransport.model_rebuild()
UserTransport.model_rebuild()
DataPermissionAssignmentRuleTransport.model_rebuild()
DataPermissionAssignmentRuleValue.model_rebuild()
DataModelListItemTransport.model_rebuild()
DataPoolTransport.model_rebuild()
Tag.model_rebuild()
DataPoolUpdateStatusTransport.model_rebuild()
CustomDataPoolConfigurationTransport.model_rebuild()
DatabaseConnectionConfigurationTransport.model_rebuild()
PoolProviderTransport.model_rebuild()
ObjectStorageBucketTransport.model_rebuild()
ZendeskDataSource.model_rebuild()
WorkdayDataSource.model_rebuild()
WorkdayReportConfiguration.model_rebuild()
UiPathDataSource.model_rebuild()
SuccessFactorsDataSource.model_rebuild()
SnowflakeRestDataSource.model_rebuild()
ServiceNowCustomBatchSize.model_rebuild()
ServiceNowDataSource.model_rebuild()
ServiceNowExecutionConfiguration.model_rebuild()
SapSnsDataSource.model_rebuild()
SapConnectionConfigurationTransport.model_rebuild()
SapDataSource.model_rebuild()
SapMarketingCloudDataSource.model_rebuild()
SalesforceDataSource.model_rebuild()
RossumV2DataSource.model_rebuild()
PythonConnectorConnectionConfigurationParameter.model_rebuild()
PythonConnectorDataSource.model_rebuild()
OracleCloudDataSource.model_rebuild()
MicrosoftDynamics365DataSource.model_rebuild()
KafkaDataSource.model_rebuild()
KafkaTopicConfiguration.model_rebuild()
JiraDataSource.model_rebuild()
HappyFoxDataSource.model_rebuild()
GoogleSheetsDataSource.model_rebuild()
FieldglassDataSource.model_rebuild()
EventHubConfiguration.model_rebuild()
EventHubDataSource.model_rebuild()
DatabaseDataSource.model_rebuild()
DataPushDataSourceTransport.model_rebuild()
CustomDataSource.model_rebuild()
CustomExtractorConnectionConnfigurationParameter.model_rebuild()
CustomExtractorDataSource.model_rebuild()
CoupaDataSource.model_rebuild()
CelonisActionEngineDataSource.model_rebuild()
BiPublisherDataSource.model_rebuild()
BiPublisherReportConfiguration.model_rebuild()
AzureServiceBusDataSource.model_rebuild()
AzureServiceBusSubscriptionConfiguration.model_rebuild()
AutomationAnywhereDataSource.model_rebuild()
AribaDataSource.model_rebuild()
AribaTableExecutionConfiguration.model_rebuild()
AmazonS3DataSource.model_rebuild()
CopyVersionRequest.model_rebuild()
DraftTransport.model_rebuild()
CsvColumnParsingOptions.model_rebuild()
CsvParsingOptions.model_rebuild()
DataPushJob.model_rebuild()
UploadDirectStorageTableChunkRequest.model_rebuild()
DirectStorageTableChunkTransport.model_rebuild()
DataCommand.model_rebuild()
DataExportRequest.model_rebuild()
DataPermissionRule.model_rebuild()
DataQuery.model_rebuild()
Kpi.model_rebuild()
KpiInformation.model_rebuild()
QueryEnvironment.model_rebuild()
DataExportStatusResponse.model_rebuild()
UplinkRegistrationTransport.model_rebuild()
CreateApplicationKeyTransport.model_rebuild()
ApplicationKeyTransport.model_rebuild()
CreateSubscriptionTransport.model_rebuild()
SubscriptionTransport.model_rebuild()
ExecutionLogTransport.model_rebuild()
LogTranslationParameter.model_rebuild()
DataPushJobTransport.model_rebuild()
DuplicateRemovalOptions.model_rebuild()
ExtractionExecutionTransport.model_rebuild()
UpdateTaskTemplateStatusTransport.model_rebuild()
BulkUpdateTaskTemplateStatusRequest.model_rebuild()
BulkTaskTemplateRequestBase.model_rebuild()
NewTaskTemplateTransport.model_rebuild()
StreamingSubscriptionTransport.model_rebuild()
StreamingConfigurationTransport.model_rebuild()
SchedulingTriggersTransport.model_rebuild()
WorkbenchReplRequest.model_rebuild()
WorkbenchQueryStatusTransport.model_rebuild()
NewTaskInstanceTransport.model_rebuild()
TableExtractionValidationTransport.model_rebuild()
TranslatedConnectorMessage.model_rebuild()
ExtractionPreviewLogs.model_rebuild()
ExtractionPreviewResponse.model_rebuild()
DataModelExecutionConfiguration.model_rebuild()
ExtractionConfiguration.model_rebuild()
JobExecutionConfiguration.model_rebuild()
JobCopyRequestTransport.model_rebuild()
JobAutoCancellationConfigurationTransport.model_rebuild()
JobAlertConfigurationTransport.model_rebuild()
PoolColumn.model_rebuild()
PoolSchema.model_rebuild()
PoolTable.model_rebuild()
DataColumn.model_rebuild()
DataStorePreviewData.model_rebuild()
InferFromSampleResponse.model_rebuild()
RepresentationResponse.model_rebuild()
InferFromSampleRequest.model_rebuild()
DataTransferImportTransport.model_rebuild()
ImportedDataSourceTableSyncTransport.model_rebuild()
TableSyncResultTransport.model_rebuild()
DataSourceTransport.model_rebuild()
ColumnNameMappingFromPoolConfig.model_rebuild()
NameMappingFromPoolConfig.model_rebuild()
TableNameMappingFromPoolConfig.model_rebuild()
NameMappingAggregated.model_rebuild()
NameMappingLoadReport.model_rebuild()
DataModelFactoryCalendar.model_rebuild()
AnonymizationSaltTransport.model_rebuild()
DataModel.model_rebuild()
DataModelCustomCalendarEntry.model_rebuild()
DataModelExecution.model_rebuild()
DataModelExecutionTable.model_rebuild()
DataModelForeignKey.model_rebuild()
DataModelForeignKeyColumn.model_rebuild()
DataModelSignalLink.model_rebuild()
DataModelSignalLinkColumn.model_rebuild()
DataModelTable.model_rebuild()
DataModelTableColumn.model_rebuild()
DataPool.model_rebuild()
DataPoolVersion.model_rebuild()
DataSource.model_rebuild()
Job.model_rebuild()
JobScheduling.model_rebuild()
Scheduling.model_rebuild()
SchedulingTrigger.model_rebuild()
TableExtraction.model_rebuild()
TableExtractionCalculatedColumn.model_rebuild()
TableExtractionColumn.model_rebuild()
TableExtractionJoin.model_rebuild()
Task.model_rebuild()
TaskInstance.model_rebuild()
Variable.model_rebuild()
VariableDefaultSettings.model_rebuild()
VariableDefaultValue.model_rebuild()
VariableSettings.model_rebuild()
VariableValue.model_rebuild()
VersionedObject.model_rebuild()
CommitVersionTransport.model_rebuild()
MoveDataPoolRequest.model_rebuild()
AccessControlEntryTransport.model_rebuild()
ConnectorStatus.model_rebuild()
ConnectorStatusStep.model_rebuild()
DataPoolInstallReport.model_rebuild()
InstallProcessRequest.model_rebuild()
FrontendLogTransport.model_rebuild()
CloneRequestTransport.model_rebuild()
TeamSlimTransport.model_rebuild()
CloneResultTransport.model_rebuild()
EraserLogMessageTransport.model_rebuild()
StreamingExecutionLogTransport.model_rebuild()
CpmNameMappingTransport.model_rebuild()
CpmNameMappings.model_rebuild()
SanitizeComputeNodesRequestTransport.model_rebuild()
DataModelExport.model_rebuild()
DataModelForeignKeyExport.model_rebuild()
DataPoolExport.model_rebuild()
DataPoolImportRequest.model_rebuild()
ExecutionItemTransport.model_rebuild()
LogMessageTransport.model_rebuild()
ReplicationCalculatedColumnTransport.model_rebuild()
ReplicationColumnTransport.model_rebuild()
ReplicationConfigurationTransport.model_rebuild()
ReplicationDataSourceConfigurationsExport.model_rebuild()
ReplicationDependencyTransport.model_rebuild()
ReplicationInitializationScriptTransport.model_rebuild()
ReplicationJoinTransport.model_rebuild()
ReplicationTransformationTransport.model_rebuild()
ReplicationTransport.model_rebuild()
SchedulingTriggerTransport.model_rebuild()
DataPoolProviderColumn.model_rebuild()
PoolProviderQueryTransport.model_rebuild()
SelectExpression.model_rebuild()
PoolProviderQueryResultTransport.model_rebuild()
PoolProviderCredentialsTransport.model_rebuild()
PoolProviderAssignmentTransport.model_rebuild()
DataPoolImportReportTransport.model_rebuild()
ObjectStorageBucketAssignmentTransport.model_rebuild()
ComputeVersionRequest.model_rebuild()
AcceleratorVersion.model_rebuild()
DataModelLoadStatusUpdateMessage.model_rebuild()
DataModelTableRowCountTransport.model_rebuild()
ResolveParameterRequestBody.model_rebuild()
FilterVariableValue.model_rebuild()
FilterVariableValueMap.model_rebuild()
DynamicDataPoolParameterTransport.model_rebuild()
DataQueryResultColumn.model_rebuild()
DataQueryResultTable.model_rebuild()
DataQueryTransport.model_rebuild()
DeltaFilterTransformationOptions.model_rebuild()
TransformationOptions.model_rebuild()
TransformationPartitioningOptions.model_rebuild()
TransformationRequestTransport.model_rebuild()
LiveDataModelsRequestTransport.model_rebuild()
CcmmTableInfo.model_rebuild()
CustomCalendar.model_rebuild()
DataColumnTransport.model_rebuild()
DataModelEngineTransport.model_rebuild()
DataModelLoadTableTransport.model_rebuild()
DataModelLoadTransport.model_rebuild()
DataTableConfigurationTransport.model_rebuild()
DataTableTransport.model_rebuild()
ForeignKeyTransport.model_rebuild()
LiveDataModelsResponseTransport.model_rebuild()
NameMappingTransport.model_rebuild()
PostMultiQueryTransport.model_rebuild()
AcceleratorSelectionFilter.model_rebuild()
AcceleratorTableStatistics.model_rebuild()
ExplainNode.model_rebuild()
MessageTransport.model_rebuild()
MissingColumnInfo.model_rebuild()
PqlCompilationExceptionTransport.model_rebuild()
PqlMultiResultTransport.model_rebuild()
PqlResultQueryStatistics.model_rebuild()
PqlResultTransport.model_rebuild()
PqlSyntaxExceptionTransport.model_rebuild()
PqlTokenManagerExceptionTransport.model_rebuild()
TableMetaData.model_rebuild()
TableResult.model_rebuild()
TranslationParameter.model_rebuild()
PostMultiQueryChunkedTransport.model_rebuild()
DataCommandBatchTransport.model_rebuild()
PostBatchQueryTransport.model_rebuild()
PqlBatchExpansionResultTransport.model_rebuild()
PqlMultiExpansionResultTransport.model_rebuild()
DataCommandBatchResultTransport.model_rebuild()
QueryBatchResult.model_rebuild()
IntegrationCloneInternalTransport.model_rebuild()
IntegrationCloneResultInternalTransport.model_rebuild()
SnowflakeRestRedirectTransport.model_rebuild()
DatabaseRedirectTransport.model_rebuild()
ContactUsTransport.model_rebuild()
IntegrationCloneExternalTransport.model_rebuild()
IntegrationCloneResultExternalTransport.model_rebuild()
TeamTransport.model_rebuild()
PageableBase.model_rebuild()
PageTransportJobTransport.model_rebuild()
DataPushChunk.model_rebuild()
DirectStorageTableTransport.model_rebuild()
DataModelDataLoadHistoryTransport.model_rebuild()
TablePartitionTransport.model_rebuild()
ReplicationCockpitServeDataTransport.model_rebuild()
ReplicationCockpitOverviewTransport.model_rebuild()
ReplicationCockpitTableIdAndNameTransport.model_rebuild()
PoolProviderFileNameMapping.model_rebuild()
ProcessDetailsTransport.model_rebuild()
Feature.model_rebuild()
ColumnValueFilterTransport.model_rebuild()
TaskByPoolVariable.model_rebuild()
StreamingLogMessageExecutionItemTransport.model_rebuild()
StreamingMonitoringTransport.model_rebuild()
DataSourceMetaData.model_rebuild()
ConnectorStreamingCapabilities.model_rebuild()
TableConfigurationParameter.model_rebuild()
TableConfigurationParameterDependency.model_rebuild()
ExecutionItemWithPageTransport.model_rebuild()
EntityStatus.model_rebuild()
LogMessageWithPageTransport.model_rebuild()
PoolQueryResultColumn.model_rebuild()
PoolQueryResultTable.model_rebuild()
WorkbenchQueryResultTransport.model_rebuild()
StatementTransport.model_rebuild()
DataModelExecutionOption.model_rebuild()
ExtractionTransport.model_rebuild()
ConfiguredConnector.model_rebuild()
DataSourceIdNameMapping.model_rebuild()
DataTransferImportOption.model_rebuild()
DataTransferDataPoolsMapping.model_rebuild()
DataTransferExportTransport.model_rebuild()
DataPoolIdNameMapping.model_rebuild()
DataTransferExportOptions.model_rebuild()
DataTransferExportableDataSource.model_rebuild()
DataSourceAvailableTables.model_rebuild()
DataSourceTable.model_rebuild()
AdditionalConnectorInformation.model_rebuild()
ConnectorInformation.model_rebuild()
ExtractionQueueStatus.model_rebuild()
ExtractionQueuedTable.model_rebuild()
DataSourceStatus.model_rebuild()
ImportedDataSourceChangesTransport.model_rebuild()
ChangeLogStatus.model_rebuild()
ChangeLogTableMetadata.model_rebuild()
ConnectorCapabilities.model_rebuild()
FilterOption.model_rebuild()
FilterOptions.model_rebuild()
TableCapabilities.model_rebuild()
DataSourceTypeTransport.model_rebuild()
TableSyncJobTransport.model_rebuild()
DataModelTableLoadingHistoryTransport.model_rebuild()
DataModelLoadTableExtendedTransport.model_rebuild()
DataLoadHistoryTransport.model_rebuild()
DataModelAverageTimeMapTransport.model_rebuild()
DataModelLoadHistoryTransport.model_rebuild()
DataModelLoadInfoTransport.model_rebuild()
DataModelLoadSyncTransport.model_rebuild()
ActivityTableCreationRestriction.model_rebuild()
DataModelWithStatusTransport.model_rebuild()
DataModelIdAndNameTransport.model_rebuild()
DataPoolDataModelOverviewTransport.model_rebuild()
PoolTablePreview.model_rebuild()
DataPoolVersionSlim.model_rebuild()
DataSourceVersioning.model_rebuild()
DataModelCreationRestrictionWithSelection.model_rebuild()
DataModelImportOption.model_rebuild()
ApplicationWizardExecutionSummary.model_rebuild()
StudioPackageOverviewTransport.model_rebuild()
StudioPackageRelatedDataModelInfoTransport.model_rebuild()
StudioPackageUserInfoTransport.model_rebuild()
SchedulingOverviewTransport.model_rebuild()
ReplicationCockpitTableOverviewTransport.model_rebuild()
DataModelOverviewTransport.model_rebuild()
DataJobOverviewTransport.model_rebuild()
DataPoolOverviewTransport.model_rebuild()
DataPoolWithExtendedContentTransport.model_rebuild()
DataPoolPageTransport.model_rebuild()
DataPoolSlimTransport.model_rebuild()
DataSourceSlimTransport.model_rebuild()
DataPoolMoveHybridVersionCheck.model_rebuild()
PermissionOptionTransport.model_rebuild()
PermissionRoleTransport.model_rebuild()
PermissionsModelTransport.model_rebuild()
TeamConsumptionTransport.model_rebuild()
ExtendedTableConsumptionPageTransport.model_rebuild()
ExtendedTableConsumptionTransport.model_rebuild()
PackageInformation.model_rebuild()
PackageDataConnectionInformation.model_rebuild()
JobFutureTransport.model_rebuild()
TransformationExecutionTransport.model_rebuild()
PermissionsOverviewTransport.model_rebuild()
AccessControlListTransport.model_rebuild()
SearchItem.model_rebuild()
ProcessConfigurationTransport.model_rebuild()
DataModelCreationRestrictionWithSelectionV1.model_rebuild()
DataModelImportOptionV1.model_rebuild()
PoolProviderConnectionDetails.model_rebuild()
PoolProviderDetailTransport.model_rebuild()
KerberosConfiguration.model_rebuild()
ConnectionConfiguration.model_rebuild()
DataPushChunkTransport.model_rebuild()
DataPoolTableStatus.model_rebuild()
DataPoolPermissionSummary.model_rebuild()
DataModelSummary.model_rebuild()
DataPoolSummary.model_rebuild()
DataModelNameMappingTransport.model_rebuild()
DataLoadFactoryCalendarTransport.model_rebuild()
DataPoolVersionInfo.model_rebuild()
ProcessDataModelTransport.model_rebuild()
PqlCategoryTransport.model_rebuild()
PqlOperatorTransport.model_rebuild()
PqlReferenceTransport.model_rebuild()
PqlSyntaxTransport.model_rebuild()
ComputeAcceleratorVersionTransport.model_rebuild()
DataStateTransport.model_rebuild()
EntityStateTransport.model_rebuild()
GroupStateTransport.model_rebuild()
HybridCapabilities.model_rebuild()
ClusterMemberState.model_rebuild()
HybridBuildInfoTransport.model_rebuild()
HybridStatusInfoResponse.model_rebuild()
HybridStatusPoolProviderInfo.model_rebuild()
FeaturesTransport.model_rebuild()
ZendeskRedirectTransport.model_rebuild()
ServiceNowRedirectTransport.model_rebuild()
InternalSystemTransport.model_rebuild()
SalesforceRedirectTransport.model_rebuild()
GoogleSheetsRedirectTransport.model_rebuild()
CustomExtractorRedirectTransport.model_rebuild()
DatabaseConnectionInputTemplate.model_rebuild()
DatabaseConnectionTemplate.model_rebuild()
DatabaseMetadataOptions.model_rebuild()
DataUploaderServeDataTransport.model_rebuild()
DataPipelineOrchestratorServeDataTransport.model_rebuild()
DataPipelineHistoryServeDataTransport.model_rebuild()
DataModelCreationRestriction.model_rebuild()
ConnectorList.model_rebuild()
ConnectorTransport.model_rebuild()
SwaggerResource.model_rebuild()
UiConfiguration.model_rebuild()
SecurityConfiguration.model_rebuild()
CustomConfigurationTransport.model_rebuild()
DatabaseConfigurationTransport.model_rebuild()
VerticaConfigurationTransport.model_rebuild()
ZendeskConnectionConfiguration.model_rebuild()
WorkdayConnectionConfiguration.model_rebuild()
UiPathConnectionConfiguration.model_rebuild()
SuccessFactorsConnectionConfiguration.model_rebuild()
SnowflakeRestConnectionConfiguration.model_rebuild()
ServiceNowConnectionConfiguration.model_rebuild()
SapSnsConnectionConfiguration.model_rebuild()
SapMarketingCloudConnectionConfiguration.model_rebuild()
SalesforceConnectionConfiguration.model_rebuild()
RossumConnectionConfiguration.model_rebuild()
PythonConnectorConnectionConfiguration.model_rebuild()
OracleCloudConnectionConfiguration.model_rebuild()
MicrosoftDynamics365ConnectionConfiguration.model_rebuild()
KafkaConnectionConfiguration.model_rebuild()
JiraConnectionConfiguration.model_rebuild()
HappyFoxConnectionConfiguration.model_rebuild()
GoogleSheetsConnectionConfiguration.model_rebuild()
FieldglassConnectionConfiguration.model_rebuild()
EventHubConnectionConfiguration.model_rebuild()
CustomConnectionConfiguration.model_rebuild()
CustomExtractorConnectionConfiguration.model_rebuild()
CoupaConnectionConfiguration.model_rebuild()
CelonisActionEngineConnectionConfiguration.model_rebuild()
BiPublisherConnectionConfiguration.model_rebuild()
AzureServiceBusConnectionConfiguration.model_rebuild()
AutomationAnywhereConnectionConfiguration.model_rebuild()
AribaConnectionConfiguration.model_rebuild()
AmazonS3ConnectionConfiguration.model_rebuild()
PoolProviderCopyTableQuery.model_rebuild()
PoolProviderCreateTableQuery.model_rebuild()
PoolProviderSelectTableQuery.model_rebuild()
DatabaseProviderConnectionDetails.model_rebuild()
SnowflakeProviderConnectionDetails.model_rebuild()
VerticaProviderConnectionDetails.model_rebuild()
AribaConnectionConfigurationV2.model_rebuild()
DatabaseConnectionConfiguration.model_rebuild()
DemoSapConnectionConfiguration.model_rebuild()
DemoServiceNowConnectionConfiguration.model_rebuild()
ImportedConnectionConfiguration.model_rebuild()
PardotConnectionConfiguration.model_rebuild()
SapConnectionConfiguration.model_rebuild()


class IntegrationClientBase(ABC):
    client: AsyncClient

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.client = AsyncClient(base_url=base_url, **kwargs)

    async def put_api_subscriptions_unsubscribe_subscription_id(self, subscription_id: str, **kwargs: Any) -> None:
        return await self.client.request(
            method="PUT", url=f"/api/subscriptions/unsubscribe/{subscription_id}", **kwargs
        )

    async def get_api_pools_pool_id_variables_id(self, pool_id: str, id: str, **kwargs: Any) -> PoolVariableTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/variables/{id}",
            parse_json=True,
            type_=PoolVariableTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_variables_id(
        self, pool_id: str, id: str, request_body: PoolVariableTransport, **kwargs: Any
    ) -> PoolVariableTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/variables/{id}",
            request_body=request_body,
            parse_json=True,
            type_=PoolVariableTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_variables_id(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{pool_id}/variables/{id}", **kwargs)

    async def get_api_pools_pool_id_templates_task_id(
        self, pool_id: str, task_id: str, **kwargs: Any
    ) -> TaskTemplateTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/templates/{task_id}",
            parse_json=True,
            type_=TaskTemplateTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_templates_task_id(
        self, pool_id: str, task_id: str, request_body: TaskTemplateTransport, **kwargs: Any
    ) -> TaskTemplateTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/templates/{task_id}",
            request_body=request_body,
            parse_json=True,
            type_=TaskTemplateTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_templates_task_id(self, pool_id: str, task_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{pool_id}/templates/{task_id}", **kwargs)

    async def put_api_pools_pool_id_tasks_task_instance_id_variables_id(
        self, pool_id: str, task_instance_id: str, id: str, request_body: TaskVariableTransport, **kwargs: Any
    ) -> TaskVariableTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/{id}",
            request_body=request_body,
            parse_json=True,
            type_=TaskVariableTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_tasks_task_instance_id_variables_id(
        self, pool_id: str, task_instance_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/{id}", **kwargs
        )

    async def put_api_pools_pool_id_streaming_tables(
        self, pool_id: str, request_body: List[Optional[StreamingTableTransport]], **kwargs: Any
    ) -> List[Optional[StreamingTableTransport]]:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/streaming/tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[StreamingTableTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_scheduling_id(self, pool_id: str, id: str, **kwargs: Any) -> SchedulingTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/scheduling/{id}",
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_scheduling_id(
        self, pool_id: str, id: str, request_body: SchedulingTransport, **kwargs: Any
    ) -> SchedulingTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/scheduling/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_scheduling_id(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{pool_id}/scheduling/{id}", **kwargs)

    async def put_api_pools_pool_id_scheduling_run_all(self, pool_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="PUT", url=f"/api/pools/{pool_id}/scheduling/run-all", **kwargs)

    async def get_api_pools_pool_id_scheduling_overview(
        self, pool_id: str, **kwargs: Any
    ) -> DataPoolSchedulingOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/scheduling/overview",
            parse_json=True,
            type_=DataPoolSchedulingOverviewTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_scheduling_overview(
        self, pool_id: str, request_body: DataPoolSchedulingOverviewFilterTransport, **kwargs: Any
    ) -> DataPoolSchedulingOverviewTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/scheduling/overview",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolSchedulingOverviewTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_transformations_transformation_id_statement(
        self, pool_id: str, job_id: str, transformation_id: str, **kwargs: Any
    ) -> StatementTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/transformations/{transformation_id}/statement",
            parse_json=True,
            type_=StatementTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_transformations_transformation_id_statement(
        self, pool_id: str, job_id: str, transformation_id: str, request_body: str, **kwargs: Any
    ) -> TransformationTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/transformations/{transformation_id}/statement",
            request_body=request_body,
            parse_json=True,
            type_=TransformationTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_tasks_task_instance_id(
        self, pool_id: str, job_id: str, task_instance_id: str, request_body: TaskUpdate, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}",
            request_body=request_body,
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_tasks_task_instance_id(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}", **kwargs
        )

    async def get_api_pools_pool_id_jobs_job_id_tasks(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[TaskInstanceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/",
            parse_json=True,
            type_=List[Optional[TaskInstanceTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_tasks(
        self,
        pool_id: str,
        job_id: str,
        request_body: List[Optional[str]],
        type_: Optional["TaskType"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_tasks(
        self, pool_id: str, job_id: str, request_body: NewTaskInstanceTransport, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/",
            request_body=request_body,
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_loads_data_model_execution_id(
        self, pool_id: str, job_id: str, data_model_execution_id: str, **kwargs: Any
    ) -> DataModelExecutionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/{data_model_execution_id}",
            parse_json=True,
            type_=DataModelExecutionTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_loads_data_model_execution_id(
        self,
        pool_id: str,
        job_id: str,
        data_model_execution_id: str,
        request_body: DataModelExecutionTransport,
        **kwargs: Any,
    ) -> DataModelExecutionTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/{data_model_execution_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelExecutionTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables(
        self,
        pool_id: str,
        job_id: str,
        extraction_id: str,
        request_body: List[Optional[TableExtractionTransport]],
        **kwargs: Any,
    ) -> List[Optional[TableExtractionTransport]]:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[TableExtractionTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables(
        self,
        pool_id: str,
        job_id: str,
        extraction_id: str,
        request_body: List[Optional[TableExtractionTransport]],
        **kwargs: Any,
    ) -> List[Optional[TableExtractionTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[TableExtractionTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_job_id_extractions_extraction_id_configuration(
        self, pool_id: str, job_id: str, extraction_id: str, request_body: ExtractionWithTablesTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/configuration",
            request_body=request_body,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_id(self, pool_id: str, id: str, **kwargs: Any) -> JobTransport:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/jobs/{id}", parse_json=True, type_=JobTransport, **kwargs
        )

    async def put_api_pools_pool_id_jobs_id(
        self, pool_id: str, id: str, request_body: JobTransport, **kwargs: Any
    ) -> JobTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/{id}",
            request_body=request_body,
            parse_json=True,
            type_=JobTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_overview(
        self, pool_id: str, **kwargs: Any
    ) -> DataPoolDataJobOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/overview",
            parse_json=True,
            type_=DataPoolDataJobOverviewTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_jobs_overview(
        self, pool_id: str, request_body: DataPoolDataJobOverviewFilterTransport, **kwargs: Any
    ) -> DataPoolDataJobOverviewTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/jobs/overview",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolDataJobOverviewTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_job_scheduling_schedule_id(
        self, pool_id: str, schedule_id: str, **kwargs: Any
    ) -> List[Optional[JobSchedulingTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/job-scheduling/{schedule_id}",
            parse_json=True,
            type_=List[Optional[JobSchedulingTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_job_scheduling_schedule_id(
        self, pool_id: str, schedule_id: str, request_body: JobSchedulingTransport, **kwargs: Any
    ) -> JobSchedulingTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/job-scheduling/{schedule_id}",
            request_body=request_body,
            parse_json=True,
            type_=JobSchedulingTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_files_file_id(self, pool_id: str, file_id: str, **kwargs: Any) -> FileDataTable:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/files/{file_id}", parse_json=True, type_=FileDataTable, **kwargs
        )

    async def put_api_pools_pool_id_files_file_id(
        self, pool_id: str, file_id: str, request_body: FileDataTable, **kwargs: Any
    ) -> FileDataTable:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/files/{file_id}",
            request_body=request_body,
            parse_json=True,
            type_=FileDataTable,
            **kwargs,
        )

    async def delete_api_pools_pool_id_files_file_id(self, pool_id: str, file_id: str, **kwargs: Any) -> str:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/files/{file_id}", parse_json=True, type_=str, **kwargs
        )

    async def put_api_pools_pool_id_files_file_id_columns(
        self, pool_id: str, file_id: str, request_body: List[Optional[FileDataColumn]], **kwargs: Any
    ) -> str:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/files/{file_id}/columns",
            request_body=request_body,
            parse_json=True,
            type_=str,
            **kwargs,
        )

    async def put_api_pools_pool_id_files_file_id_cancel(self, pool_id: str, file_id: str, **kwargs: Any) -> str:
        return await self.client.request(
            method="PUT", url=f"/api/pools/{pool_id}/files/{file_id}/cancel", parse_json=True, type_=str, **kwargs
        )

    async def put_api_pools_pool_id_extractor_builder_id_information(
        self, pool_id: str, id: str, request_body: CustomExtractorTransport, **kwargs: Any
    ) -> CustomExtractorTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/extractor-builder/{id}/information",
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_extractor_builder_id_connection_parameters(
        self, pool_id: str, id: str, request_body: List[Optional[CustomExtractorConnectionParameter]], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/extractor-builder/{id}/connectionParameters",
            request_body=request_body,
            **kwargs,
        )

    async def put_api_pools_pool_id_extractor_builder_id_authentication_method(
        self, pool_id: str, id: str, request_body: CustomExtractorAuthenticationTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/extractor-builder/{id}/authenticationMethod",
            request_body=request_body,
            **kwargs,
        )

    async def put_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint_endpoint_id(
        self,
        pool_id: str,
        custom_extractor_id: str,
        endpoint_id: str,
        request_body: CustomExtractorEndpoint,
        **kwargs: Any,
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint/{endpoint_id}",
            request_body=request_body,
            **kwargs,
        )

    async def delete_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint_endpoint_id(
        self, pool_id: str, custom_extractor_id: str, endpoint_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint/{endpoint_id}",
            **kwargs,
        )

    async def put_api_pools_pool_id_data_transfer_exports_export_id(
        self, pool_id: str, export_id: str, request_body: DataTransferExportCreateEditTransport, **kwargs: Any
    ) -> DataTransferExportSlimTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-transfer/exports/{export_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataTransferExportSlimTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_transfer_exports_export_id(
        self, pool_id: str, export_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-transfer/exports/{export_id}", **kwargs
        )

    async def get_api_pools_pool_id_data_sources_v2_overview(
        self, pool_id: str, **kwargs: Any
    ) -> DataPoolDataSourceOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/v2/overview",
            parse_json=True,
            type_=DataPoolDataSourceOverviewTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_sources_v2_overview(
        self, pool_id: str, request_body: DataPoolDataSourceOverviewFilterTransport, **kwargs: Any
    ) -> DataPoolDataSourceOverviewTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-sources/v2/overview",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolDataSourceOverviewTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id(
        self, pool_id: str, data_model_id: str, request_body: DataModelTransport, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-models/{data_model_id}", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_signal_links_id(
        self, pool_id: str, data_model_id: str, id: str, **kwargs: Any
    ) -> DataModelSignalLinkTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/signal-links/{id}",
            parse_json=True,
            type_=DataModelSignalLinkTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_signal_links_id(
        self, pool_id: str, data_model_id: str, id: str, request_body: DataModelSignalLinkTransport, **kwargs: Any
    ) -> DataModelSignalLinkTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/signal-links/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelSignalLinkTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_signal_links_id(
        self, pool_id: str, data_model_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/signal-links/{id}", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_process_configurations(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelConfiguration]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/process-configurations",
            parse_json=True,
            type_=List[Optional[DataModelConfiguration]],
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_process_configurations(
        self, pool_id: str, data_model_id: str, request_body: DataModelConfiguration, **kwargs: Any
    ) -> DataModelConfiguration:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/process-configurations",
            request_body=request_body,
            parse_json=True,
            type_=DataModelConfiguration,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_process_configurations_default_activity_table(
        self, pool_id: str, data_model_id: str, request_body: DataModelTableTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/process-configurations/default-activity-table",
            request_body=request_body,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_parallel_configuration(
        self, pool_id: str, data_model_id: str, request_body: ParallelProcessConfiguration, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/parallel-configuration",
            request_body=request_body,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_graph_positioning(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelGraphPositioningTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/graph/positioning",
            parse_json=True,
            type_=DataModelGraphPositioningTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_graph_positioning(
        self, pool_id: str, data_model_id: str, request_body: DataModelGraphPositioningTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/graph/positioning",
            request_body=request_body,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_foreign_keys_id(
        self, pool_id: str, data_model_id: str, id: str, **kwargs: Any
    ) -> DataModelForeignKeyTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/foreign-keys/{id}",
            parse_json=True,
            type_=DataModelForeignKeyTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_foreign_keys_id(
        self, pool_id: str, data_model_id: str, id: str, request_body: DataModelForeignKeyTransport, **kwargs: Any
    ) -> DataModelForeignKeyTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/foreign-keys/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelForeignKeyTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_foreign_keys_id(
        self, pool_id: str, data_model_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/foreign-keys/{id}", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_type(
        self, pool_id: str, data_model_id: str, type_: DataPermissionType, **kwargs: Any
    ) -> DataPermission:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{type_}",
            parse_json=True,
            type_=DataPermission,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_data_permission_type(
        self, pool_id: str, data_model_id: str, type_: DataPermissionType, request_body: DataPermission, **kwargs: Any
    ) -> DataPermission:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{type_}",
            request_body=request_body,
            parse_json=True,
            type_=DataPermission,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_permission_tables(
        self, pool_id: str, data_model_id: str, data_permission_id: str, **kwargs: Any
    ) -> List[Optional[DataPermissionTableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/permission-tables",
            parse_json=True,
            type_=List[Optional[DataPermissionTableTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_permission_tables(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        request_body: List[Optional[DataPermissionTableTransport]],
        **kwargs: Any,
    ) -> List[Optional[DataPermissionTableTransport]]:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/permission-tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataPermissionTableTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        assignment_id: str,
        request_body: DataPermissionAssignmentTransport,
        **kwargs: Any,
    ) -> DataPermissionAssignmentTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataPermissionAssignmentTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id(
        self, pool_id: str, data_model_id: str, data_permission_id: str, assignment_id: str, **kwargs: Any
    ) -> str:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}",
            parse_json=True,
            type_=str,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id_rules_rule_id(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        assignment_id: str,
        rule_id: str,
        request_body: DataPermissionAssignmentRuleTransport,
        **kwargs: Any,
    ) -> DataPermissionAssignmentRuleTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}/rules/{rule_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataPermissionAssignmentRuleTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id_rules_rule_id(
        self, pool_id: str, data_model_id: str, data_permission_id: str, assignment_id: str, rule_id: str, **kwargs: Any
    ) -> str:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}/rules/{rule_id}",
            parse_json=True,
            type_=str,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_models_list_data_model_id(
        self, pool_id: str, data_model_id: str, request_body: DataModelListItemTransport, **kwargs: Any
    ) -> DataModelListItemTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-models/list/{data_model_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelListItemTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables",
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def put_api_pools_pool_id_data_model_data_model_id_tables(
        self, pool_id: str, data_model_id: str, request_body: List[Optional[DataModelTableTransport]], **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_model_data_model_id_tables(
        self, pool_id: str, data_model_id: str, request_body: List[Optional[DataModelTableTransport]], **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables_id(
        self, pool_id: str, data_model_id: str, id: str, **kwargs: Any
    ) -> DataModelTableTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{id}",
            parse_json=True,
            type_=DataModelTableTransport,
            **kwargs,
        )

    async def put_api_pools_pool_id_data_model_data_model_id_tables_id(
        self, pool_id: str, data_model_id: str, id: str, request_body: DataModelTableTransport, **kwargs: Any
    ) -> DataModelTableTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTableTransport,
            **kwargs,
        )

    async def get_api_pools_id(self, id: str, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="GET", url=f"/api/pools/{id}", parse_json=True, type_=DataPoolTransport, **kwargs
        )

    async def put_api_pools_id(self, id: str, request_body: DataPoolTransport, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def delete_api_pools_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{id}", **kwargs)

    async def put_api_pools_id_tags(
        self, id: str, request_body: List[Optional[Tag]], **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{id}/tags",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def put_api_pools_id_status(
        self, id: str, request_body: DataPoolUpdateStatusTransport, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/{id}/status",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def put_api_pools_custom_pool_id_custom_config_id(
        self, pool_id: str, custom_config_id: str, request_body: CustomDataPoolConfigurationTransport, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/pools/custom/{pool_id}/{custom_config_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def get_api_datasource_zendesk_id(self, id: str, **kwargs: Any) -> ZendeskDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/zendesk/{id}", parse_json=True, type_=ZendeskDataSource, **kwargs
        )

    async def put_api_datasource_zendesk_id(
        self, id: str, request_body: ZendeskDataSource, **kwargs: Any
    ) -> ZendeskDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/zendesk/{id}",
            request_body=request_body,
            parse_json=True,
            type_=ZendeskDataSource,
            **kwargs,
        )

    async def get_api_datasource_workday_id(self, id: str, **kwargs: Any) -> WorkdayDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/workday/{id}", parse_json=True, type_=WorkdayDataSource, **kwargs
        )

    async def put_api_datasource_workday_id(
        self, id: str, request_body: WorkdayDataSource, **kwargs: Any
    ) -> WorkdayDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/workday/{id}",
            request_body=request_body,
            parse_json=True,
            type_=WorkdayDataSource,
            **kwargs,
        )

    async def get_api_datasource_uipath_id(self, id: str, **kwargs: Any) -> UiPathDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/uipath/{id}", parse_json=True, type_=UiPathDataSource, **kwargs
        )

    async def put_api_datasource_uipath_id(
        self, id: str, request_body: UiPathDataSource, **kwargs: Any
    ) -> UiPathDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/uipath/{id}",
            request_body=request_body,
            parse_json=True,
            type_=UiPathDataSource,
            **kwargs,
        )

    async def get_api_datasource_success_factors_id(self, id: str, **kwargs: Any) -> SuccessFactorsDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/success-factors/{id}",
            parse_json=True,
            type_=SuccessFactorsDataSource,
            **kwargs,
        )

    async def put_api_datasource_success_factors_id(
        self, id: str, request_body: SuccessFactorsDataSource, **kwargs: Any
    ) -> SuccessFactorsDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/success-factors/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SuccessFactorsDataSource,
            **kwargs,
        )

    async def get_api_datasource_snowflake_rest_id(self, id: str, **kwargs: Any) -> SnowflakeRestDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/snowflake-rest/{id}",
            parse_json=True,
            type_=SnowflakeRestDataSource,
            **kwargs,
        )

    async def put_api_datasource_snowflake_rest_id(
        self, id: str, request_body: SnowflakeRestDataSource, **kwargs: Any
    ) -> SnowflakeRestDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/snowflake-rest/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SnowflakeRestDataSource,
            **kwargs,
        )

    async def get_api_datasource_service_now_id(self, id: str, **kwargs: Any) -> ServiceNowDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/service-now/{id}", parse_json=True, type_=ServiceNowDataSource, **kwargs
        )

    async def put_api_datasource_service_now_id(
        self, id: str, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ServiceNowDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/service-now/{id}",
            request_body=request_body,
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def get_api_datasource_service_now_demo_id(self, id: str, **kwargs: Any) -> ServiceNowDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/service-now-demo/{id}",
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def put_api_datasource_service_now_demo_id(
        self, id: str, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ServiceNowDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/service-now-demo/{id}",
            request_body=request_body,
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def get_api_datasource_sapsns_id(self, id: str, **kwargs: Any) -> SapSnsDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/sapsns/{id}", parse_json=True, type_=SapSnsDataSource, **kwargs
        )

    async def put_api_datasource_sapsns_id(
        self, id: str, request_body: SapSnsDataSource, **kwargs: Any
    ) -> SapSnsDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/sapsns/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SapSnsDataSource,
            **kwargs,
        )

    async def get_api_datasource_sap_id(self, id: str, **kwargs: Any) -> SapDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/sap/{id}", parse_json=True, type_=SapDataSource, **kwargs
        )

    async def put_api_datasource_sap_id(self, id: str, request_body: SapDataSource, **kwargs: Any) -> SapDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/sap/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SapDataSource,
            **kwargs,
        )

    async def get_api_datasource_sap_marketing_cloud_id(self, id: str, **kwargs: Any) -> SapMarketingCloudDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/sap-marketing-cloud/{id}",
            parse_json=True,
            type_=SapMarketingCloudDataSource,
            **kwargs,
        )

    async def put_api_datasource_sap_marketing_cloud_id(
        self, id: str, request_body: SapMarketingCloudDataSource, **kwargs: Any
    ) -> SapMarketingCloudDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/sap-marketing-cloud/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SapMarketingCloudDataSource,
            **kwargs,
        )

    async def get_api_datasource_salesforce_id(self, id: str, **kwargs: Any) -> SalesforceDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/salesforce/{id}", parse_json=True, type_=SalesforceDataSource, **kwargs
        )

    async def put_api_datasource_salesforce_id(
        self, id: str, request_body: SalesforceDataSource, **kwargs: Any
    ) -> SalesforceDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/salesforce/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SalesforceDataSource,
            **kwargs,
        )

    async def get_api_datasource_rossum_v2_id(self, id: str, **kwargs: Any) -> RossumV2DataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/rossum-v2/{id}", parse_json=True, type_=RossumV2DataSource, **kwargs
        )

    async def put_api_datasource_rossum_v2_id(
        self, id: str, request_body: RossumV2DataSource, **kwargs: Any
    ) -> RossumV2DataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/rossum-v2/{id}",
            request_body=request_body,
            parse_json=True,
            type_=RossumV2DataSource,
            **kwargs,
        )

    async def get_api_datasource_python_connector_id(self, id: str, **kwargs: Any) -> PythonConnectorDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/python-connector/{id}",
            parse_json=True,
            type_=PythonConnectorDataSource,
            **kwargs,
        )

    async def put_api_datasource_python_connector_id(
        self, id: str, request_body: PythonConnectorDataSource, **kwargs: Any
    ) -> PythonConnectorDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/python-connector/{id}",
            request_body=request_body,
            parse_json=True,
            type_=PythonConnectorDataSource,
            **kwargs,
        )

    async def get_api_datasource_oracle_cloud_id(self, id: str, **kwargs: Any) -> OracleCloudDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/oracle-cloud/{id}",
            parse_json=True,
            type_=OracleCloudDataSource,
            **kwargs,
        )

    async def put_api_datasource_oracle_cloud_id(
        self, id: str, request_body: OracleCloudDataSource, **kwargs: Any
    ) -> OracleCloudDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/oracle-cloud/{id}",
            request_body=request_body,
            parse_json=True,
            type_=OracleCloudDataSource,
            **kwargs,
        )

    async def get_api_datasource_microsoft_dynamics_365_id(
        self, id: str, **kwargs: Any
    ) -> MicrosoftDynamics365DataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/microsoft-dynamics-365/{id}",
            parse_json=True,
            type_=MicrosoftDynamics365DataSource,
            **kwargs,
        )

    async def put_api_datasource_microsoft_dynamics_365_id(
        self, id: str, request_body: MicrosoftDynamics365DataSource, **kwargs: Any
    ) -> MicrosoftDynamics365DataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/microsoft-dynamics-365/{id}",
            request_body=request_body,
            parse_json=True,
            type_=MicrosoftDynamics365DataSource,
            **kwargs,
        )

    async def get_api_datasource_kafka_id(self, id: str, **kwargs: Any) -> KafkaDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/kafka/{id}", parse_json=True, type_=KafkaDataSource, **kwargs
        )

    async def put_api_datasource_kafka_id(
        self, id: str, request_body: KafkaDataSource, **kwargs: Any
    ) -> KafkaDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/kafka/{id}",
            request_body=request_body,
            parse_json=True,
            type_=KafkaDataSource,
            **kwargs,
        )

    async def get_api_datasource_jira_id(self, id: str, **kwargs: Any) -> JiraDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/jira/{id}", parse_json=True, type_=JiraDataSource, **kwargs
        )

    async def put_api_datasource_jira_id(self, id: str, request_body: JiraDataSource, **kwargs: Any) -> JiraDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/jira/{id}",
            request_body=request_body,
            parse_json=True,
            type_=JiraDataSource,
            **kwargs,
        )

    async def get_api_datasource_happyfox_id(self, id: str, **kwargs: Any) -> HappyFoxDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/happyfox/{id}", parse_json=True, type_=HappyFoxDataSource, **kwargs
        )

    async def put_api_datasource_happyfox_id(
        self, id: str, request_body: HappyFoxDataSource, **kwargs: Any
    ) -> HappyFoxDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/happyfox/{id}",
            request_body=request_body,
            parse_json=True,
            type_=HappyFoxDataSource,
            **kwargs,
        )

    async def get_api_datasource_google_sheets_id(self, id: str, **kwargs: Any) -> GoogleSheetsDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/google-sheets/{id}",
            parse_json=True,
            type_=GoogleSheetsDataSource,
            **kwargs,
        )

    async def put_api_datasource_google_sheets_id(
        self, id: str, request_body: GoogleSheetsDataSource, **kwargs: Any
    ) -> GoogleSheetsDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/google-sheets/{id}",
            request_body=request_body,
            parse_json=True,
            type_=GoogleSheetsDataSource,
            **kwargs,
        )

    async def get_api_datasource_fieldglass_id(self, id: str, **kwargs: Any) -> FieldglassDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/fieldglass/{id}", parse_json=True, type_=FieldglassDataSource, **kwargs
        )

    async def put_api_datasource_fieldglass_id(
        self, id: str, request_body: FieldglassDataSource, **kwargs: Any
    ) -> FieldglassDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/fieldglass/{id}",
            request_body=request_body,
            parse_json=True,
            type_=FieldglassDataSource,
            **kwargs,
        )

    async def get_api_datasource_eventhub_id(self, id: str, **kwargs: Any) -> EventHubDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/eventhub/{id}", parse_json=True, type_=EventHubDataSource, **kwargs
        )

    async def put_api_datasource_eventhub_id(
        self, id: str, request_body: EventHubDataSource, **kwargs: Any
    ) -> EventHubDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/eventhub/{id}",
            request_body=request_body,
            parse_json=True,
            type_=EventHubDataSource,
            **kwargs,
        )

    async def get_api_datasource_database_id(self, id: str, **kwargs: Any) -> DatabaseDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/database/{id}", parse_json=True, type_=DatabaseDataSource, **kwargs
        )

    async def put_api_datasource_database_id(
        self, id: str, request_body: DatabaseDataSource, **kwargs: Any
    ) -> DatabaseDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/database/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DatabaseDataSource,
            **kwargs,
        )

    async def get_api_datasource_data_push_id(self, id: str, **kwargs: Any) -> DataPushDataSourceTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/data-push/{id}",
            parse_json=True,
            type_=DataPushDataSourceTransport,
            **kwargs,
        )

    async def put_api_datasource_data_push_id(
        self, id: str, request_body: DataPushDataSourceTransport, **kwargs: Any
    ) -> DataPushDataSourceTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/data-push/{id}",
            request_body=request_body,
            parse_json=True,
            type_=DataPushDataSourceTransport,
            **kwargs,
        )

    async def get_api_datasource_custom_id(self, id: str, **kwargs: Any) -> CustomDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/custom/{id}", parse_json=True, type_=CustomDataSource, **kwargs
        )

    async def put_api_datasource_custom_id(
        self, id: str, request_body: CustomDataSource, **kwargs: Any
    ) -> CustomDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/custom/{id}",
            request_body=request_body,
            parse_json=True,
            type_=CustomDataSource,
            **kwargs,
        )

    async def get_api_datasource_custom_extractor_id(self, id: str, **kwargs: Any) -> CustomExtractorDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/custom-extractor/{id}",
            parse_json=True,
            type_=CustomExtractorDataSource,
            **kwargs,
        )

    async def put_api_datasource_custom_extractor_id(
        self, id: str, request_body: CustomExtractorDataSource, **kwargs: Any
    ) -> CustomExtractorDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/custom-extractor/{id}",
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorDataSource,
            **kwargs,
        )

    async def get_api_datasource_coupa_id(self, id: str, **kwargs: Any) -> CoupaDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/coupa/{id}", parse_json=True, type_=CoupaDataSource, **kwargs
        )

    async def put_api_datasource_coupa_id(
        self, id: str, request_body: CoupaDataSource, **kwargs: Any
    ) -> CoupaDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/coupa/{id}",
            request_body=request_body,
            parse_json=True,
            type_=CoupaDataSource,
            **kwargs,
        )

    async def get_api_datasource_celonis_action_engine_id(
        self, id: str, **kwargs: Any
    ) -> CelonisActionEngineDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/celonis-action-engine/{id}",
            parse_json=True,
            type_=CelonisActionEngineDataSource,
            **kwargs,
        )

    async def put_api_datasource_celonis_action_engine_id(
        self, id: str, request_body: CelonisActionEngineDataSource, **kwargs: Any
    ) -> CelonisActionEngineDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/celonis-action-engine/{id}",
            request_body=request_body,
            parse_json=True,
            type_=CelonisActionEngineDataSource,
            **kwargs,
        )

    async def get_api_datasource_bi_publisher_id(self, id: str, **kwargs: Any) -> BiPublisherDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/bi-publisher/{id}",
            parse_json=True,
            type_=BiPublisherDataSource,
            **kwargs,
        )

    async def put_api_datasource_bi_publisher_id(
        self, id: str, request_body: BiPublisherDataSource, **kwargs: Any
    ) -> BiPublisherDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/bi-publisher/{id}",
            request_body=request_body,
            parse_json=True,
            type_=BiPublisherDataSource,
            **kwargs,
        )

    async def get_api_datasource_azure_service_bus_v2_id(self, id: str, **kwargs: Any) -> AzureServiceBusDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/azure-service-bus-v2/{id}",
            parse_json=True,
            type_=AzureServiceBusDataSource,
            **kwargs,
        )

    async def put_api_datasource_azure_service_bus_v2_id(
        self, id: str, request_body: AzureServiceBusDataSource, **kwargs: Any
    ) -> AzureServiceBusDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/azure-service-bus-v2/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AzureServiceBusDataSource,
            **kwargs,
        )

    async def get_api_datasource_automation_anywhere_id(self, id: str, **kwargs: Any) -> AutomationAnywhereDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/automation-anywhere/{id}",
            parse_json=True,
            type_=AutomationAnywhereDataSource,
            **kwargs,
        )

    async def put_api_datasource_automation_anywhere_id(
        self, id: str, request_body: AutomationAnywhereDataSource, **kwargs: Any
    ) -> AutomationAnywhereDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/automation-anywhere/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AutomationAnywhereDataSource,
            **kwargs,
        )

    async def get_api_datasource_ariba_id(self, id: str, **kwargs: Any) -> AribaDataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/ariba/{id}", parse_json=True, type_=AribaDataSource, **kwargs
        )

    async def put_api_datasource_ariba_id(
        self, id: str, request_body: AribaDataSource, **kwargs: Any
    ) -> AribaDataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/ariba/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AribaDataSource,
            **kwargs,
        )

    async def get_api_datasource_amazons3_id(self, id: str, **kwargs: Any) -> AmazonS3DataSource:
        return await self.client.request(
            method="GET", url=f"/api/datasource/amazons3/{id}", parse_json=True, type_=AmazonS3DataSource, **kwargs
        )

    async def put_api_datasource_amazons3_id(
        self, id: str, request_body: AmazonS3DataSource, **kwargs: Any
    ) -> AmazonS3DataSource:
        return await self.client.request(
            method="PUT",
            url=f"/api/datasource/amazons3/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AmazonS3DataSource,
            **kwargs,
        )

    async def post_api_version_copy_copy(self, request_body: CopyVersionRequest, **kwargs: Any) -> DraftTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/version-copy/copy",
            request_body=request_body,
            parse_json=True,
            type_=DraftTransport,
            **kwargs,
        )

    async def post_api_v2_data_pools_pool_id_data_jobs_job_id_execute(
        self, pool_id: str, job_id: str, mode: Optional["ExtractionMode"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        return await self.client.request(
            method="POST", url=f"/api/v2/data-pools/{pool_id}/data-jobs/{job_id}/execute", params=params, **kwargs
        )

    async def get_api_v1_data_push_pool_id_jobs_id(self, pool_id: str, id: str, **kwargs: Any) -> DataPushJob:
        return await self.client.request(
            method="GET", url=f"/api/v1/data-push/{pool_id}/jobs/{id}", parse_json=True, type_=DataPushJob, **kwargs
        )

    async def post_api_v1_data_push_pool_id_jobs_id(
        self, pool_id: str, id: str, duplicate_removal_column: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if duplicate_removal_column is not None:
            if isinstance(duplicate_removal_column, PythonCoreBaseModel):
                params.update(duplicate_removal_column.json_dict(by_alias=True))
            elif isinstance(duplicate_removal_column, dict):
                params.update(duplicate_removal_column)
            else:
                params["duplicateRemovalColumn"] = duplicate_removal_column
        return await self.client.request(
            method="POST", url=f"/api/v1/data-push/{pool_id}/jobs/{id}", params=params, **kwargs
        )

    async def delete_api_v1_data_push_pool_id_jobs_id(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/v1/data-push/{pool_id}/jobs/{id}", **kwargs)

    async def post_api_v1_data_push_pool_id_jobs_id_chunks_upserted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/v1/data-push/{pool_id}/jobs/{id}/chunks/upserted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_v1_data_push_pool_id_jobs_id_chunks_deleted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/v1/data-push/{pool_id}/jobs/{id}/chunks/deleted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_v1_data_push_pool_id_jobs_id_cancel(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/v1/data-push/{pool_id}/jobs/{id}/cancel", **kwargs)

    async def get_api_v1_data_push_pool_id_jobs(self, pool_id: str, **kwargs: Any) -> List[Optional[DataPushJob]]:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-push/{pool_id}/jobs/",
            parse_json=True,
            type_=List[Optional[DataPushJob]],
            **kwargs,
        )

    async def post_api_v1_data_push_pool_id_jobs(
        self, pool_id: str, request_body: DataPushJob, **kwargs: Any
    ) -> DataPushJob:
        return await self.client.request(
            method="POST",
            url=f"/api/v1/data-push/{pool_id}/jobs/",
            request_body=request_body,
            parse_json=True,
            type_=DataPushJob,
            **kwargs,
        )

    async def get_api_v1_data_pools_pool_id_direct_data_push_tables(
        self, pool_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[DirectStorageTableTransport]]:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-pools/{pool_id}/direct-data-push/tables",
            params=params,
            parse_json=True,
            type_=List[Optional[DirectStorageTableTransport]],
            **kwargs,
        )

    async def post_api_v1_data_pools_pool_id_direct_data_push_tables(
        self, pool_id: str, request_body: UploadDirectStorageTableChunkRequest, **kwargs: Any
    ) -> DirectStorageTableChunkTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/v1/data-pools/{pool_id}/direct-data-push/tables",
            request_body=request_body,
            parse_json=True,
            type_=DirectStorageTableChunkTransport,
            **kwargs,
        )

    async def delete_api_v1_data_pools_pool_id_direct_data_push_tables(
        self, pool_id: str, data_source_id: Optional["str"] = None, table_name: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="DELETE", url=f"/api/v1/data-pools/{pool_id}/direct-data-push/tables", params=params, **kwargs
        )

    async def post_api_v1_data_pools_pool_id_data_models_data_model_id_load(
        self, pool_id: str, data_model_id: str, full_reload: Optional["bool"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if full_reload is not None:
            if isinstance(full_reload, PythonCoreBaseModel):
                params.update(full_reload.json_dict(by_alias=True))
            elif isinstance(full_reload, dict):
                params.update(full_reload)
            else:
                params["fullReload"] = full_reload
        return await self.client.request(
            method="POST", url=f"/api/v1/data-pools/{pool_id}/data-models/{data_model_id}/load", params=params, **kwargs
        )

    async def post_api_v1_data_pools_pool_id_data_models_data_model_id_load_partial_sync(
        self,
        pool_id: str,
        data_model_id: str,
        request_body: List[Optional[str]],
        full_reload: Optional["bool"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if full_reload is not None:
            if isinstance(full_reload, PythonCoreBaseModel):
                params.update(full_reload.json_dict(by_alias=True))
            elif isinstance(full_reload, dict):
                params.update(full_reload)
            else:
                params["fullReload"] = full_reload
        return await self.client.request(
            method="POST",
            url=f"/api/v1/data-pools/{pool_id}/data-models/{data_model_id}/load/partial-sync",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_v1_data_pools_pool_id_data_jobs_job_id_execute(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/v1/data-pools/{pool_id}/data-jobs/{job_id}/execute", **kwargs
        )

    async def post_api_v1_compute_data_model_id_export_query(
        self, data_model_id: str, request_body: DataExportRequest, **kwargs: Any
    ) -> DataExportStatusResponse:
        return await self.client.request(
            method="POST",
            url=f"/api/v1/compute/{data_model_id}/export/query",
            request_body=request_body,
            parse_json=True,
            type_=DataExportStatusResponse,
            **kwargs,
        )

    async def post_api_uplink(
        self, request_body: UplinkRegistrationTransport, **kwargs: Any
    ) -> UplinkRegistrationTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/uplink",
            request_body=request_body,
            parse_json=True,
            type_=UplinkRegistrationTransport,
            **kwargs,
        )

    async def post_api_team_keys(
        self, request_body: CreateApplicationKeyTransport, **kwargs: Any
    ) -> ApplicationKeyTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/team/keys/",
            request_body=request_body,
            parse_json=True,
            type_=ApplicationKeyTransport,
            **kwargs,
        )

    async def post_api_subscriptions_subscribe(
        self, request_body: CreateSubscriptionTransport, **kwargs: Any
    ) -> SubscriptionTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/subscriptions/subscribe",
            request_body=request_body,
            parse_json=True,
            type_=SubscriptionTransport,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_warn(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/warn",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_success(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/success",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_run(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/run",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_info(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/info",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_fail(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/fail",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_extracted_records(
        self,
        execution_item_id: str,
        request_body: int,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/extracted-records",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_debug(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/debug",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_executionitem_execution_item_id_cancel(
        self,
        execution_item_id: str,
        request_body: ExecutionLogTransport,
        expiry: Optional["int"] = None,
        signature: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        return await self.client.request(
            method="POST",
            url=f"/api/public/executionitem/{execution_item_id}/cancel",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def post_api_public_data_source_data_source_id_log_files(
        self,
        data_source_id: str,
        request_body: Dict[str, Any],
        signature: Optional["str"] = None,
        expiry: Optional["int"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if signature is not None:
            if isinstance(signature, PythonCoreBaseModel):
                params.update(signature.json_dict(by_alias=True))
            elif isinstance(signature, dict):
                params.update(signature)
            else:
                params["signature"] = signature
        if expiry is not None:
            if isinstance(expiry, PythonCoreBaseModel):
                params.update(expiry.json_dict(by_alias=True))
            elif isinstance(expiry, dict):
                params.update(expiry)
            else:
                params["expiry"] = expiry
        return await self.client.request(
            method="POST",
            url=f"/api/public/data-source/{data_source_id}/log-files",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def get_api_pools(
        self, team_domain: Optional["str"] = None, pool_ids: Optional["List[Optional[str]]"] = None, **kwargs: Any
    ) -> List[Optional[DataPoolTransport]]:
        params: Dict[str, Any] = {}
        if team_domain is not None:
            if isinstance(team_domain, PythonCoreBaseModel):
                params.update(team_domain.json_dict(by_alias=True))
            elif isinstance(team_domain, dict):
                params.update(team_domain)
            else:
                params["teamDomain"] = team_domain
        if pool_ids is not None:
            if isinstance(pool_ids, PythonCoreBaseModel):
                params.update(pool_ids.json_dict(by_alias=True))
            elif isinstance(pool_ids, dict):
                params.update(pool_ids)
            else:
                params["poolIds"] = pool_ids
        return await self.client.request(
            method="GET",
            url=f"/api/pools",
            params=params,
            parse_json=True,
            type_=List[Optional[DataPoolTransport]],
            **kwargs,
        )

    async def post_api_pools(self, request_body: DataPoolTransport, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_variables(
        self,
        pool_id: str,
        public_constants: Optional["bool"] = None,
        constant_type: Optional["FilterParserDataType"] = None,
        **kwargs: Any,
    ) -> List[Optional[PoolVariableTransport]]:
        params: Dict[str, Any] = {}
        if public_constants is not None:
            if isinstance(public_constants, PythonCoreBaseModel):
                params.update(public_constants.json_dict(by_alias=True))
            elif isinstance(public_constants, dict):
                params.update(public_constants)
            else:
                params["publicConstants"] = public_constants
        if constant_type is not None:
            if isinstance(constant_type, PythonCoreBaseModel):
                params.update(constant_type.json_dict(by_alias=True))
            elif isinstance(constant_type, dict):
                params.update(constant_type)
            else:
                params["constantType"] = constant_type
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/variables/",
            params=params,
            parse_json=True,
            type_=List[Optional[PoolVariableTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_variables(
        self, pool_id: str, request_body: PoolVariableTransport, **kwargs: Any
    ) -> PoolVariableTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/variables/",
            request_body=request_body,
            parse_json=True,
            type_=PoolVariableTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_templates_task_id_protection(
        self, pool_id: str, task_id: str, request_body: UpdateTaskTemplateStatusTransport, **kwargs: Any
    ) -> TaskTemplateTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/{task_id}/protection",
            request_body=request_body,
            parse_json=True,
            type_=TaskTemplateTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_templates_task_id_duplicate(
        self, pool_id: str, task_id: str, **kwargs: Any
    ) -> TaskTemplateTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/{task_id}/duplicate",
            parse_json=True,
            type_=TaskTemplateTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_templates_task(
        self, pool_id: str, request_body: TaskInstanceTransport, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/task",
            request_body=request_body,
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_templates_bulk_protection(
        self, pool_id: str, request_body: BulkUpdateTaskTemplateStatusRequest, **kwargs: Any
    ) -> List[Optional[TaskTemplateTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/bulk/protection",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[TaskTemplateTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_templates_bulk_affected_job_names(
        self, pool_id: str, request_body: BulkTaskTemplateRequestBase, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/bulk/affected-job-names",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_pools_pool_id_templates(
        self, pool_id: str, include_number_of_instances: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[TaskTemplateTransport]]:
        params: Dict[str, Any] = {}
        if include_number_of_instances is not None:
            if isinstance(include_number_of_instances, PythonCoreBaseModel):
                params.update(include_number_of_instances.json_dict(by_alias=True))
            elif isinstance(include_number_of_instances, dict):
                params.update(include_number_of_instances)
            else:
                params["includeNumberOfInstances"] = include_number_of_instances
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/templates/",
            params=params,
            parse_json=True,
            type_=List[Optional[TaskTemplateTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_templates(
        self, pool_id: str, request_body: NewTaskTemplateTransport, **kwargs: Any
    ) -> TaskTemplateTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/templates/",
            request_body=request_body,
            parse_json=True,
            type_=TaskTemplateTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_template_access_task_id(self, pool_id: str, task_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/template-access/{task_id}", **kwargs)

    async def get_api_pools_pool_id_tasks_task_instance_id_variables(
        self, pool_id: str, task_instance_id: str, **kwargs: Any
    ) -> List[Optional[TaskVariableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/",
            parse_json=True,
            type_=List[Optional[TaskVariableTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_tasks_task_instance_id_variables(
        self, pool_id: str, task_instance_id: str, request_body: TaskVariableTransport, **kwargs: Any
    ) -> TaskVariableTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/",
            request_body=request_body,
            parse_json=True,
            type_=TaskVariableTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_streaming_subscription_id_stop(
        self, pool_id: str, subscription_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> StreamingSubscriptionTransport:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/streaming/{subscription_id}/stop",
            params=params,
            parse_json=True,
            type_=StreamingSubscriptionTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_streaming_subscription_id_start(
        self, pool_id: str, subscription_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> StreamingSubscriptionTransport:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/streaming/{subscription_id}/start",
            params=params,
            parse_json=True,
            type_=StreamingSubscriptionTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_streaming_initialize(
        self, pool_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> StreamingConfigurationTransport:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/streaming/initialize",
            params=params,
            parse_json=True,
            type_=StreamingConfigurationTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_scheduling(
        self, pool_id: str, include_creator_name: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[SchedulingTransport]]:
        params: Dict[str, Any] = {}
        if include_creator_name is not None:
            if isinstance(include_creator_name, PythonCoreBaseModel):
                params.update(include_creator_name.json_dict(by_alias=True))
            elif isinstance(include_creator_name, dict):
                params.update(include_creator_name)
            else:
                params["includeCreatorName"] = include_creator_name
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/scheduling",
            params=params,
            parse_json=True,
            type_=List[Optional[SchedulingTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_scheduling(
        self, pool_id: str, request_body: SchedulingTransport, **kwargs: Any
    ) -> SchedulingTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/scheduling",
            request_body=request_body,
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_scheduling_scheduling_id_scheduling_trigger(
        self, pool_id: str, scheduling_id: str, **kwargs: Any
    ) -> SchedulingTriggersTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/scheduling/{scheduling_id}/scheduling-trigger",
            parse_json=True,
            type_=SchedulingTriggersTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_scheduling_scheduling_id_scheduling_trigger(
        self, pool_id: str, scheduling_id: str, request_body: SchedulingTriggersTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/scheduling/{scheduling_id}/scheduling-trigger",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_scheduling_id_execute(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/scheduling/{id}/execute", **kwargs)

    async def post_api_pools_pool_id_scheduling_id_cancel(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/scheduling/{id}/cancel", **kwargs)

    async def get_api_pools_pool_id_jobs(self, pool_id: str, **kwargs: Any) -> List[Optional[JobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs",
            parse_json=True,
            type_=List[Optional[JobTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs(
        self, pool_id: str, request_body: JobTransport, **kwargs: Any
    ) -> JobTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs",
            request_body=request_body,
            parse_json=True,
            type_=JobTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_workbench_transformation_id_execute(
        self, pool_id: str, job_id: str, transformation_id: str, request_body: WorkbenchReplRequest, **kwargs: Any
    ) -> WorkbenchQueryStatusTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/workbench/{transformation_id}/execute",
            request_body=request_body,
            parse_json=True,
            type_=WorkbenchQueryStatusTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_published(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/published",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_published(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/published",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_enabled(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/enabled",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_enabled(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/enabled",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_duplicate(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/duplicate",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_loads(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[DataModelExecutionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads",
            parse_json=True,
            type_=List[Optional[DataModelExecutionTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_loads(
        self, pool_id: str, job_id: str, request_body: DataModelExecutionTransport, **kwargs: Any
    ) -> DataModelExecutionTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads",
            request_body=request_body,
            parse_json=True,
            type_=DataModelExecutionTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_loads_id_enabled(
        self, pool_id: str, job_id: str, id: str, **kwargs: Any
    ) -> DataModelExecutionTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/{id}/enabled",
            parse_json=True,
            type_=DataModelExecutionTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_loads_id_enabled(
        self, pool_id: str, job_id: str, id: str, **kwargs: Any
    ) -> DataModelExecutionTransport:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/{id}/enabled",
            parse_json=True,
            type_=DataModelExecutionTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables_validate(
        self,
        pool_id: str,
        job_id: str,
        extraction_id: str,
        request_body: List[Optional[TableExtractionTransport]],
        task_id: Optional["str"] = None,
        include_all_tables: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[TableExtractionValidationTransport]]:
        params: Dict[str, Any] = {}
        if task_id is not None:
            if isinstance(task_id, PythonCoreBaseModel):
                params.update(task_id.json_dict(by_alias=True))
            elif isinstance(task_id, dict):
                params.update(task_id)
            else:
                params["taskId"] = task_id
        if include_all_tables is not None:
            if isinstance(include_all_tables, PythonCoreBaseModel):
                params.update(include_all_tables.json_dict(by_alias=True))
            elif isinstance(include_all_tables, dict):
                params.update(include_all_tables)
            else:
                params["includeAllTables"] = include_all_tables
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/validate",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[TableExtractionValidationTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables_get_preview(
        self,
        pool_id: str,
        job_id: str,
        extraction_id: str,
        request_body: TableExtractionTransport,
        is_delta_load: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ExtractionPreviewResponse:
        params: Dict[str, Any] = {}
        if is_delta_load is not None:
            if isinstance(is_delta_load, PythonCoreBaseModel):
                params.update(is_delta_load.json_dict(by_alias=True))
            elif isinstance(is_delta_load, dict):
                params.update(is_delta_load)
            else:
                params["isDeltaLoad"] = is_delta_load
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/getPreview",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=ExtractionPreviewResponse,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_execute(
        self, pool_id: str, job_id: str, request_body: JobExecutionConfiguration, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/jobs/{job_id}/execute", request_body=request_body, **kwargs
        )

    async def post_api_pools_pool_id_jobs_job_id_duplicate(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> JobTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/duplicate",
            parse_json=True,
            type_=JobTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_copy(
        self, pool_id: str, job_id: str, request_body: JobCopyRequestTransport, **kwargs: Any
    ) -> JobTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/copy",
            request_body=request_body,
            parse_json=True,
            type_=JobTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_cancel(self, pool_id: str, job_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/jobs/{job_id}/cancel", **kwargs)

    async def get_api_pools_pool_id_jobs_job_id_auto_cancellation(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> JobAutoCancellationConfigurationTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/auto-cancellation",
            parse_json=True,
            type_=JobAutoCancellationConfigurationTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_auto_cancellation(
        self, pool_id: str, job_id: str, request_body: JobAutoCancellationConfigurationTransport, **kwargs: Any
    ) -> JobAutoCancellationConfigurationTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/auto-cancellation",
            request_body=request_body,
            parse_json=True,
            type_=JobAutoCancellationConfigurationTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_auto_cancellation(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/jobs/{job_id}/auto-cancellation", **kwargs
        )

    async def get_api_pools_pool_id_jobs_job_id_alerts(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> JobAlertConfigurationTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/alerts",
            parse_json=True,
            type_=JobAlertConfigurationTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_job_id_alerts(
        self, pool_id: str, job_id: str, request_body: JobAlertConfigurationTransport, **kwargs: Any
    ) -> JobAlertConfigurationTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/alerts",
            request_body=request_body,
            parse_json=True,
            type_=JobAlertConfigurationTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_alerts(self, pool_id: str, job_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{pool_id}/jobs/{job_id}/alerts", **kwargs)

    async def post_api_pools_pool_id_jobs_id_reload_cached_schemas(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[PoolSchema]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/jobs/{id}/reload-cachedSchemas",
            parse_json=True,
            type_=List[Optional[PoolSchema]],
            **kwargs,
        )

    async def post_api_pools_pool_id_jobs_execute_all(self, pool_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/jobs/execute-all", **kwargs)

    async def post_api_pools_pool_id_jobs_cancel_all(self, pool_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/pools/{pool_id}/jobs/cancel-all", **kwargs)

    async def post_api_pools_pool_id_job_scheduling(
        self, pool_id: str, request_body: List[Optional[JobSchedulingTransport]], **kwargs: Any
    ) -> List[Optional[JobSchedulingTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/job-scheduling",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[JobSchedulingTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_files(self, pool_id: str, **kwargs: Any) -> List[Optional[FileDataTable]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/files",
            parse_json=True,
            type_=List[Optional[FileDataTable]],
            **kwargs,
        )

    async def post_api_pools_pool_id_files(
        self, pool_id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> FileDataTable:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/files",
            request_body=request_body,
            parse_json=True,
            type_=FileDataTable,
            **kwargs,
        )

    async def post_api_pools_pool_id_files_file_id_process(
        self, pool_id: str, file_id: str, **kwargs: Any
    ) -> FileDataTable:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/files/{file_id}/process",
            parse_json=True,
            type_=FileDataTable,
            **kwargs,
        )

    async def post_api_pools_pool_id_files_file_id_preview(
        self,
        pool_id: str,
        file_id: str,
        request_body: FileDataTable,
        sheet_name: Optional["str"] = None,
        has_header_row: Optional["bool"] = None,
        num_of_rows: Optional["int"] = None,
        **kwargs: Any,
    ) -> DataStorePreviewData:
        params: Dict[str, Any] = {}
        if sheet_name is not None:
            if isinstance(sheet_name, PythonCoreBaseModel):
                params.update(sheet_name.json_dict(by_alias=True))
            elif isinstance(sheet_name, dict):
                params.update(sheet_name)
            else:
                params["sheetName"] = sheet_name
        if has_header_row is not None:
            if isinstance(has_header_row, PythonCoreBaseModel):
                params.update(has_header_row.json_dict(by_alias=True))
            elif isinstance(has_header_row, dict):
                params.update(has_header_row)
            else:
                params["hasHeaderRow"] = has_header_row
        if num_of_rows is not None:
            if isinstance(num_of_rows, PythonCoreBaseModel):
                params.update(num_of_rows.json_dict(by_alias=True))
            elif isinstance(num_of_rows, dict):
                params.update(num_of_rows)
            else:
                params["numOfRows"] = num_of_rows
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/files/{file_id}/preview",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=DataStorePreviewData,
            **kwargs,
        )

    async def post_api_pools_pool_id_files_file_id_password(
        self, pool_id: str, file_id: str, request_body: str, **kwargs: Any
    ) -> FileDataTable:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/files/{file_id}/password",
            request_body=request_body,
            parse_json=True,
            type_=FileDataTable,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder(
        self, pool_id: str, request_body: CustomExtractorTransport, **kwargs: Any
    ) -> CustomExtractorTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder",
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_get_response_configuration_from_samples(
        self,
        pool_id: str,
        custom_extractor_id: str,
        request_body: CustomExtractorEndpoint,
        data_source_id: Optional["str"] = None,
        max_number_of_requests: Optional["int"] = None,
        **kwargs: Any,
    ) -> InferFromSampleResponse:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if max_number_of_requests is not None:
            if isinstance(max_number_of_requests, PythonCoreBaseModel):
                params.update(max_number_of_requests.json_dict(by_alias=True))
            elif isinstance(max_number_of_requests, dict):
                params.update(max_number_of_requests)
            else:
                params["maxNumberOfRequests"] = max_number_of_requests
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/getResponseConfigurationFromSamples",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=InferFromSampleResponse,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_export(
        self, pool_id: str, custom_extractor_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/export", **kwargs
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint(
        self, pool_id: str, custom_extractor_id: str, request_body: CustomExtractorEndpoint, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint_endpoint_id_duplicate(
        self, pool_id: str, custom_extractor_id: str, endpoint_id: str, **kwargs: Any
    ) -> CustomExtractorEndpoint:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint/{endpoint_id}/duplicate",
            parse_json=True,
            type_=CustomExtractorEndpoint,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint_endpoint_id_deactivate(
        self, pool_id: str, custom_extractor_id: str, endpoint_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint/{endpoint_id}/deactivate",
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_endpoint_endpoint_id_activate(
        self, pool_id: str, custom_extractor_id: str, endpoint_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/endpoint/{endpoint_id}/activate",
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_duplicate(
        self, pool_id: str, custom_extractor_id: str, **kwargs: Any
    ) -> CustomExtractorTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/duplicate",
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_custom_extractor_id_customize_data_sources(
        self, pool_id: str, custom_extractor_id: str, request_body: List[Optional[str]], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/customizeDataSources",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_validate_request_parameter(
        self, pool_id: str, request_body: CustomExtractorRequestParameter, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/validateRequestParameter",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_validate_error_handling_rule(
        self, pool_id: str, request_body: CustomExtractorErrorHandlingRule, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/validateErrorHandlingRule",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_validate_connection_parameter(
        self, pool_id: str, request_body: CustomExtractorConnectionParameter, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/validateConnectionParameter",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_infer_config_from_sample(
        self, pool_id: str, request_body: InferFromSampleRequest, **kwargs: Any
    ) -> InferFromSampleResponse:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/inferConfigFromSample",
            request_body=request_body,
            parse_json=True,
            type_=InferFromSampleResponse,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_import(
        self,
        pool_id: str,
        request_body: Dict[str, Any],
        name: Optional["str"] = None,
        description: Optional["str"] = None,
        **kwargs: Any,
    ) -> CustomExtractorTransport:
        params: Dict[str, Any] = {}
        if name is not None:
            if isinstance(name, PythonCoreBaseModel):
                params.update(name.json_dict(by_alias=True))
            elif isinstance(name, dict):
                params.update(name)
            else:
                params["name"] = name
        if description is not None:
            if isinstance(description, PythonCoreBaseModel):
                params.update(description.json_dict(by_alias=True))
            elif isinstance(description, dict):
                params.update(description)
            else:
                params["description"] = description
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/import",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_get_json_representation(
        self, pool_id: str, request_body: CustomExtractorEndpoint, **kwargs: Any
    ) -> RepresentationResponse:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/getJsonRepresentation",
            request_body=request_body,
            parse_json=True,
            type_=RepresentationResponse,
            **kwargs,
        )

    async def post_api_pools_pool_id_extractor_builder_customize(
        self,
        pool_id: str,
        request_body: CustomExtractorTransport,
        extractor_to_customize: Optional["str"] = None,
        **kwargs: Any,
    ) -> CustomExtractorTransport:
        params: Dict[str, Any] = {}
        if extractor_to_customize is not None:
            if isinstance(extractor_to_customize, PythonCoreBaseModel):
                params.update(extractor_to_customize.json_dict(by_alias=True))
            elif isinstance(extractor_to_customize, dict):
                params.update(extractor_to_customize)
            else:
                params["extractorToCustomize"] = extractor_to_customize
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/extractor-builder/customize",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_imports(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataTransferImportTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/imports",
            parse_json=True,
            type_=List[Optional[DataTransferImportTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_transfer_imports(
        self, pool_id: str, request_body: DataTransferImportTransport, **kwargs: Any
    ) -> DataTransferImportTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-transfer/imports",
            request_body=request_body,
            parse_json=True,
            type_=DataTransferImportTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_exports(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataTransferExportSlimTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/exports",
            parse_json=True,
            type_=List[Optional[DataTransferExportSlimTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_transfer_exports(
        self, pool_id: str, request_body: DataTransferExportCreateEditTransport, **kwargs: Any
    ) -> DataTransferExportSlimTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-transfer/exports",
            request_body=request_body,
            parse_json=True,
            type_=DataTransferExportSlimTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_synchronize_update(
        self, pool_id: str, data_source_id: str, request_body: ImportedDataSourceTableSyncTransport, **kwargs: Any
    ) -> TableSyncResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/synchronize-update",
            request_body=request_body,
            parse_json=True,
            type_=TableSyncResultTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_synchronize_drop(
        self, pool_id: str, data_source_id: str, request_body: ImportedDataSourceTableSyncTransport, **kwargs: Any
    ) -> TableSyncResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/synchronize-drop",
            request_body=request_body,
            parse_json=True,
            type_=TableSyncResultTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_synchronize_create(
        self, pool_id: str, data_source_id: str, request_body: ImportedDataSourceTableSyncTransport, **kwargs: Any
    ) -> TableSyncResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/synchronize-create",
            request_body=request_body,
            parse_json=True,
            type_=TableSyncResultTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_reset(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> DataSourceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/reset",
            parse_json=True,
            type_=DataSourceTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_invalidate_metadata_cache(
        self, pool_id: str, data_source_id: str, request_body: List[Optional[TableExtractionTransport]], **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/invalidate-metadata-cache",
            request_body=request_body,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_duplicate(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> DataSourceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/duplicate",
            parse_json=True,
            type_=DataSourceTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_sources_data_source_id_copy(
        self, pool_id: str, data_source_id: str, to_data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> DataSourceTransport:
        params: Dict[str, Any] = {}
        if to_data_source_id is not None:
            if isinstance(to_data_source_id, PythonCoreBaseModel):
                params.update(to_data_source_id.json_dict(by_alias=True))
            elif isinstance(to_data_source_id, dict):
                params.update(to_data_source_id)
            else:
                params["toDataSourceId"] = to_data_source_id
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/copy",
            params=params,
            parse_json=True,
            type_=DataSourceTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models(
        self, pool_id: str, limit: Optional["int"] = None, **kwargs: Any
    ) -> List[Optional[DataModelTransport]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models",
            params=params,
            parse_json=True,
            type_=List[Optional[DataModelTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models(
        self, pool_id: str, request_body: DataModelTransport, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_unload(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/unload", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_signal_links(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelSignalLinkTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/signal-links",
            parse_json=True,
            type_=List[Optional[DataModelSignalLinkTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_signal_links(
        self, pool_id: str, data_model_id: str, request_body: DataModelSignalLinkTransport, **kwargs: Any
    ) -> DataModelSignalLinkTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/signal-links",
            request_body=request_body,
            parse_json=True,
            type_=DataModelSignalLinkTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_reload(
        self, pool_id: str, data_model_id: str, force_complete: Optional["bool"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if force_complete is not None:
            if isinstance(force_complete, PythonCoreBaseModel):
                params.update(force_complete.json_dict(by_alias=True))
            elif isinstance(force_complete, dict):
                params.update(force_complete)
            else:
                params["forceComplete"] = force_complete
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/reload", params=params, **kwargs
        )

    async def post_api_pools_pool_id_data_models_data_model_id_name_mapping_pool(
        self, pool_id: str, data_model_id: str, request_body: NameMappingFromPoolConfig, **kwargs: Any
    ) -> NameMappingLoadReport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping/pool",
            request_body=request_body,
            parse_json=True,
            type_=NameMappingLoadReport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_name_mapping_file(
        self, pool_id: str, data_model_id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> NameMappingLoadReport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping/file",
            request_body=request_body,
            parse_json=True,
            type_=NameMappingLoadReport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_foreign_keys(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelForeignKeyTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/foreign-keys",
            parse_json=True,
            type_=List[Optional[DataModelForeignKeyTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_foreign_keys(
        self, pool_id: str, data_model_id: str, request_body: DataModelForeignKeyTransport, **kwargs: Any
    ) -> DataModelForeignKeyTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/foreign-keys",
            request_body=request_body,
            parse_json=True,
            type_=DataModelForeignKeyTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_force_cancel_load(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/force-cancel-load", **kwargs
        )

    async def post_api_pools_pool_id_data_models_data_model_id_duplicate(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/duplicate",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_permission_tables_synchronize(
        self, pool_id: str, data_model_id: str, data_permission_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/permission-tables/synchronize",
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments(
        self, pool_id: str, data_model_id: str, data_permission_id: str, **kwargs: Any
    ) -> List[Optional[DataPermissionAssignmentTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments",
            parse_json=True,
            type_=List[Optional[DataPermissionAssignmentTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        request_body: DataPermissionAssignmentTransport,
        **kwargs: Any,
    ) -> DataPermissionAssignmentTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments",
            request_body=request_body,
            parse_json=True,
            type_=DataPermissionAssignmentTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id_rules(
        self, pool_id: str, data_model_id: str, data_permission_id: str, assignment_id: str, **kwargs: Any
    ) -> List[Optional[DataPermissionAssignmentRuleTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}/rules",
            parse_json=True,
            type_=List[Optional[DataPermissionAssignmentRuleTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_assignment_id_rules(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        assignment_id: str,
        request_body: DataPermissionAssignmentRuleTransport,
        **kwargs: Any,
    ) -> DataPermissionAssignmentRuleTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/{assignment_id}/rules",
            request_body=request_body,
            parse_json=True,
            type_=DataPermissionAssignmentRuleTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_assignments_batch(
        self,
        pool_id: str,
        data_model_id: str,
        data_permission_id: str,
        request_body: List[Optional[DataPermissionAssignmentTransport]],
        **kwargs: Any,
    ) -> List[Optional[DataPermissionAssignmentTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/assignments/batch",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataPermissionAssignmentTransport]],
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_cancel_load(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/cancel-load", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_factory(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelFactoryCalendar:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/factory",
            parse_json=True,
            type_=DataModelFactoryCalendar,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_calendar_factory(
        self, pool_id: str, data_model_id: str, request_body: DataModelFactoryCalendar, **kwargs: Any
    ) -> DataModelFactoryCalendar:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/factory",
            request_body=request_body,
            parse_json=True,
            type_=DataModelFactoryCalendar,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_custom(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelCustomCalendarTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/custom",
            parse_json=True,
            type_=DataModelCustomCalendarTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_data_models_data_model_id_calendar_custom(
        self, pool_id: str, data_model_id: str, request_body: DataModelCustomCalendarTransport, **kwargs: Any
    ) -> DataModelCustomCalendarTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/custom",
            request_body=request_body,
            parse_json=True,
            type_=DataModelCustomCalendarTransport,
            **kwargs,
        )

    async def post_api_pools_pool_id_anonymization_salts(
        self, pool_id: str, request_body: AnonymizationSaltTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/pools/{pool_id}/anonymization-salts", request_body=request_body, **kwargs
        )

    async def post_api_pools_id_versions_draft_id(self, id: str, draft_id: str, **kwargs: Any) -> DataPoolVersion:
        return await self.client.request(
            method="POST", url=f"/api/pools/{id}/versions/{draft_id}", parse_json=True, type_=DataPoolVersion, **kwargs
        )

    async def post_api_pools_id_reset(self, id: str, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="POST", url=f"/api/pools/{id}/reset", parse_json=True, type_=DataPoolTransport, **kwargs
        )

    async def post_api_pools_id_commit(
        self, id: str, request_body: CommitVersionTransport, **kwargs: Any
    ) -> DraftTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/{id}/commit",
            request_body=request_body,
            parse_json=True,
            type_=DraftTransport,
            **kwargs,
        )

    async def post_api_pools_move(self, request_body: MoveDataPoolRequest, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/move",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def get_api_pools_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_pools_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_pools_custom(
        self, request_body: CustomDataPoolConfigurationTransport, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/custom",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def post_api_pools_custom_check(
        self, request_body: CustomDataPoolConfigurationTransport, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/pools/custom/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_pool_import(self, request_body: str, **kwargs: Any) -> DataPoolInstallReport:
        return await self.client.request(
            method="POST",
            url=f"/api/pool-import",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolInstallReport,
            **kwargs,
        )

    async def post_api_package_install_process(
        self, request_body: InstallProcessRequest, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/package-install/process",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def post_api_package_install_process_initialized_pool_id(self, pool_id: str, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/package-install/process/initialized/{pool_id}", **kwargs
        )

    async def post_api_monitoring_setup(self, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="POST", url=f"/api/monitoring-setup", parse_json=True, type_=DataPoolTransport, **kwargs
        )

    async def delete_api_monitoring_setup(self, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/monitoring-setup", **kwargs)

    async def post_api_logging_frontend(self, request_body: FrontendLogTransport, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/logging/frontend", request_body=request_body, **kwargs
        )

    async def post_api_locks_id_cancel(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/locks/{id}/cancel", **kwargs)

    async def post_api_job_dag_migration_tenant_id(self, tenant_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/job-dag-migration/{tenant_id}", **kwargs)

    async def post_api_job_dag_migration_all(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/job-dag-migration/all", **kwargs)

    async def post_api_datasource_zendesk(self, request_body: ZendeskDataSource, **kwargs: Any) -> ZendeskDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/zendesk",
            request_body=request_body,
            parse_json=True,
            type_=ZendeskDataSource,
            **kwargs,
        )

    async def post_api_datasource_zendesk_check(
        self, request_body: ZendeskDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/zendesk/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_workday(self, request_body: WorkdayDataSource, **kwargs: Any) -> WorkdayDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/workday",
            request_body=request_body,
            parse_json=True,
            type_=WorkdayDataSource,
            **kwargs,
        )

    async def post_api_datasource_workday_check(
        self, request_body: WorkdayDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/workday/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_uipath(self, request_body: UiPathDataSource, **kwargs: Any) -> UiPathDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/uipath",
            request_body=request_body,
            parse_json=True,
            type_=UiPathDataSource,
            **kwargs,
        )

    async def post_api_datasource_uipath_check(self, request_body: UiPathDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/uipath/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_success_factors(
        self, request_body: SuccessFactorsDataSource, **kwargs: Any
    ) -> SuccessFactorsDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/success-factors",
            request_body=request_body,
            parse_json=True,
            type_=SuccessFactorsDataSource,
            **kwargs,
        )

    async def post_api_datasource_success_factors_check(
        self, request_body: SuccessFactorsDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/success-factors/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_snowflake_rest(
        self, request_body: SnowflakeRestDataSource, **kwargs: Any
    ) -> SnowflakeRestDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/snowflake-rest",
            request_body=request_body,
            parse_json=True,
            type_=SnowflakeRestDataSource,
            **kwargs,
        )

    async def post_api_datasource_snowflake_rest_id_redirect(
        self, id: str, request_body: SnowflakeRestDataSource, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> SnowflakeRestRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/snowflake-rest/{id}/redirect",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=SnowflakeRestRedirectTransport,
            **kwargs,
        )

    async def post_api_datasource_snowflake_rest_check(
        self, request_body: SnowflakeRestDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/snowflake-rest/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_service_now(
        self, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ServiceNowDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/service-now",
            request_body=request_body,
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def post_api_datasource_service_now_check(
        self, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/service-now/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_service_now_demo(
        self, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ServiceNowDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/service-now-demo",
            request_body=request_body,
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def post_api_datasource_service_now_demo_check(
        self, request_body: ServiceNowDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/service-now-demo/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_sapsns(self, request_body: SapSnsDataSource, **kwargs: Any) -> SapSnsDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sapsns",
            request_body=request_body,
            parse_json=True,
            type_=SapSnsDataSource,
            **kwargs,
        )

    async def post_api_datasource_sapsns_check(self, request_body: SapSnsDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sapsns/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_sap(self, request_body: SapDataSource, **kwargs: Any) -> SapDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sap",
            request_body=request_body,
            parse_json=True,
            type_=SapDataSource,
            **kwargs,
        )

    async def post_api_datasource_sap_check(self, request_body: SapDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sap/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_sap_marketing_cloud(
        self, request_body: SapMarketingCloudDataSource, **kwargs: Any
    ) -> SapMarketingCloudDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sap-marketing-cloud",
            request_body=request_body,
            parse_json=True,
            type_=SapMarketingCloudDataSource,
            **kwargs,
        )

    async def post_api_datasource_sap_marketing_cloud_check(
        self, request_body: SapMarketingCloudDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/sap-marketing-cloud/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_salesforce(
        self, request_body: SalesforceDataSource, **kwargs: Any
    ) -> SalesforceDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/salesforce",
            request_body=request_body,
            parse_json=True,
            type_=SalesforceDataSource,
            **kwargs,
        )

    async def post_api_datasource_salesforce_check(
        self, request_body: SalesforceDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/salesforce/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_rossum_v2(
        self, request_body: RossumV2DataSource, **kwargs: Any
    ) -> RossumV2DataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/rossum-v2",
            request_body=request_body,
            parse_json=True,
            type_=RossumV2DataSource,
            **kwargs,
        )

    async def post_api_datasource_rossum_v2_check(
        self, request_body: RossumV2DataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/rossum-v2/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_python_connector(
        self, request_body: PythonConnectorDataSource, **kwargs: Any
    ) -> PythonConnectorDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/python-connector",
            request_body=request_body,
            parse_json=True,
            type_=PythonConnectorDataSource,
            **kwargs,
        )

    async def post_api_datasource_python_connector_validate_parameter(
        self, request_body: PythonConnectorConnectionConfigurationParameter, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/python-connector/validateParameter",
            request_body=request_body,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def post_api_datasource_python_connector_check(
        self, request_body: PythonConnectorDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/python-connector/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_oracle_cloud(
        self, request_body: OracleCloudDataSource, **kwargs: Any
    ) -> OracleCloudDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/oracle-cloud",
            request_body=request_body,
            parse_json=True,
            type_=OracleCloudDataSource,
            **kwargs,
        )

    async def post_api_datasource_oracle_cloud_check(
        self, request_body: OracleCloudDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/oracle-cloud/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_microsoft_dynamics_365(
        self, request_body: MicrosoftDynamics365DataSource, **kwargs: Any
    ) -> MicrosoftDynamics365DataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/microsoft-dynamics-365",
            request_body=request_body,
            parse_json=True,
            type_=MicrosoftDynamics365DataSource,
            **kwargs,
        )

    async def post_api_datasource_microsoft_dynamics_365_check(
        self, request_body: MicrosoftDynamics365DataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/microsoft-dynamics-365/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_kafka(self, request_body: KafkaDataSource, **kwargs: Any) -> KafkaDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/kafka",
            request_body=request_body,
            parse_json=True,
            type_=KafkaDataSource,
            **kwargs,
        )

    async def post_api_datasource_kafka_validate_topic(
        self, request_body: KafkaTopicConfiguration, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/kafka/validateTopic",
            request_body=request_body,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def post_api_datasource_kafka_check(self, request_body: KafkaDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/kafka/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_jira(self, request_body: JiraDataSource, **kwargs: Any) -> JiraDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/jira",
            request_body=request_body,
            parse_json=True,
            type_=JiraDataSource,
            **kwargs,
        )

    async def post_api_datasource_jira_check(self, request_body: JiraDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/jira/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_happyfox(self, request_body: HappyFoxDataSource, **kwargs: Any) -> HappyFoxDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/happyfox",
            request_body=request_body,
            parse_json=True,
            type_=HappyFoxDataSource,
            **kwargs,
        )

    async def post_api_datasource_happyfox_check(
        self, request_body: HappyFoxDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/happyfox/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_google_sheets(
        self, request_body: GoogleSheetsDataSource, **kwargs: Any
    ) -> GoogleSheetsDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/google-sheets",
            request_body=request_body,
            parse_json=True,
            type_=GoogleSheetsDataSource,
            **kwargs,
        )

    async def post_api_datasource_google_sheets_check(
        self, request_body: GoogleSheetsDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/google-sheets/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_fieldglass(
        self, request_body: FieldglassDataSource, **kwargs: Any
    ) -> FieldglassDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/fieldglass",
            request_body=request_body,
            parse_json=True,
            type_=FieldglassDataSource,
            **kwargs,
        )

    async def post_api_datasource_fieldglass_check(
        self, request_body: FieldglassDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/fieldglass/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_eventhub(self, request_body: EventHubDataSource, **kwargs: Any) -> EventHubDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/eventhub",
            request_body=request_body,
            parse_json=True,
            type_=EventHubDataSource,
            **kwargs,
        )

    async def post_api_datasource_eventhub_validate_subscription(
        self, request_body: EventHubConfiguration, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/eventhub/validateSubscription",
            request_body=request_body,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def post_api_datasource_eventhub_check(
        self, request_body: EventHubDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/eventhub/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_database(self, request_body: DatabaseDataSource, **kwargs: Any) -> DatabaseDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/database",
            request_body=request_body,
            parse_json=True,
            type_=DatabaseDataSource,
            **kwargs,
        )

    async def post_api_datasource_database_id_redirect(
        self, id: str, request_body: DatabaseDataSource, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> DatabaseRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/database/{id}/redirect",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=DatabaseRedirectTransport,
            **kwargs,
        )

    async def post_api_datasource_database_check(
        self, request_body: DatabaseDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/database/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_data_push(
        self, request_body: DataPushDataSourceTransport, **kwargs: Any
    ) -> DataPushDataSourceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/data-push",
            request_body=request_body,
            parse_json=True,
            type_=DataPushDataSourceTransport,
            **kwargs,
        )

    async def post_api_datasource_custom(self, request_body: CustomDataSource, **kwargs: Any) -> CustomDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/custom",
            request_body=request_body,
            parse_json=True,
            type_=CustomDataSource,
            **kwargs,
        )

    async def post_api_datasource_custom_check(self, request_body: CustomDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/custom/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_custom_extractor_check(
        self, request_body: CustomExtractorDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/custom-extractor/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_custom_extractor(
        self, request_body: CustomExtractorDataSource, **kwargs: Any
    ) -> CustomExtractorDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/custom-extractor/",
            request_body=request_body,
            parse_json=True,
            type_=CustomExtractorDataSource,
            **kwargs,
        )

    async def post_api_datasource_coupa(self, request_body: CoupaDataSource, **kwargs: Any) -> CoupaDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/coupa",
            request_body=request_body,
            parse_json=True,
            type_=CoupaDataSource,
            **kwargs,
        )

    async def post_api_datasource_coupa_check(self, request_body: CoupaDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/coupa/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_celonis_action_engine(
        self, request_body: CelonisActionEngineDataSource, **kwargs: Any
    ) -> CelonisActionEngineDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/celonis-action-engine",
            request_body=request_body,
            parse_json=True,
            type_=CelonisActionEngineDataSource,
            **kwargs,
        )

    async def post_api_datasource_celonis_action_engine_check(
        self, request_body: CelonisActionEngineDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/celonis-action-engine/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_bi_publisher(
        self, request_body: BiPublisherDataSource, **kwargs: Any
    ) -> BiPublisherDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/bi-publisher",
            request_body=request_body,
            parse_json=True,
            type_=BiPublisherDataSource,
            **kwargs,
        )

    async def post_api_datasource_bi_publisher_check(
        self, request_body: BiPublisherDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/bi-publisher/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_azure_service_bus_v2(
        self, request_body: AzureServiceBusDataSource, **kwargs: Any
    ) -> AzureServiceBusDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/azure-service-bus-v2",
            request_body=request_body,
            parse_json=True,
            type_=AzureServiceBusDataSource,
            **kwargs,
        )

    async def post_api_datasource_azure_service_bus_v2_validate_subscription(
        self, request_body: AzureServiceBusSubscriptionConfiguration, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/azure-service-bus-v2/validateSubscription",
            request_body=request_body,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def post_api_datasource_azure_service_bus_v2_check(
        self, request_body: AzureServiceBusDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/azure-service-bus-v2/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_automation_anywhere(
        self, request_body: AutomationAnywhereDataSource, **kwargs: Any
    ) -> AutomationAnywhereDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/automation-anywhere",
            request_body=request_body,
            parse_json=True,
            type_=AutomationAnywhereDataSource,
            **kwargs,
        )

    async def post_api_datasource_automation_anywhere_check(
        self, request_body: AutomationAnywhereDataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/automation-anywhere/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_ariba(self, request_body: AribaDataSource, **kwargs: Any) -> AribaDataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/ariba",
            request_body=request_body,
            parse_json=True,
            type_=AribaDataSource,
            **kwargs,
        )

    async def post_api_datasource_ariba_check(self, request_body: AribaDataSource, **kwargs: Any) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/ariba/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_datasource_amazons3(self, request_body: AmazonS3DataSource, **kwargs: Any) -> AmazonS3DataSource:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/amazons3",
            request_body=request_body,
            parse_json=True,
            type_=AmazonS3DataSource,
            **kwargs,
        )

    async def post_api_datasource_amazons3_check(
        self, request_body: AmazonS3DataSource, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="POST",
            url=f"/api/datasource/amazons3/check",
            request_body=request_body,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def post_api_data_models_migrate_tenant_id(self, tenant_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/data-models/migrate/{tenant_id}", **kwargs)

    async def post_api_data_models_migrate_all(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/data-models/migrate/all", **kwargs)

    async def get_api_data_models_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/data-models/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_data_models_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/data-models/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_data_model_import_pool_id(
        self, pool_id: str, request_body: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/data-model-import/{pool_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_contact_us(self, request_body: ContactUsTransport, **kwargs: Any) -> ContactUsTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/contact-us",
            request_body=request_body,
            parse_json=True,
            type_=ContactUsTransport,
            **kwargs,
        )

    async def post_api_clone(
        self, request_body: IntegrationCloneExternalTransport, **kwargs: Any
    ) -> IntegrationCloneResultExternalTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/clone/",
            request_body=request_body,
            parse_json=True,
            type_=IntegrationCloneResultExternalTransport,
            **kwargs,
        )

    async def post_api_admin_queues_stop(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/admin/queues/stop", **kwargs)

    async def post_api_admin_queues_start(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/admin/queues/start", **kwargs)

    async def post_api_admin_queues_on_time_schedule_slo_enqueue(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/admin/queues/on-time-schedule-slo/enqueue", **kwargs)

    async def get_redirect_content_data_model_id(self, data_model_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/redirect-content/{data_model_id}", **kwargs)

    async def get_redirect_content_hybrid_integration(
        self,
        redirect_url: Optional["str"] = None,
        data_pool_id: Optional["str"] = None,
        data_model_id: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if redirect_url is not None:
            if isinstance(redirect_url, PythonCoreBaseModel):
                params.update(redirect_url.json_dict(by_alias=True))
            elif isinstance(redirect_url, dict):
                params.update(redirect_url)
            else:
                params["redirectUrl"] = redirect_url
        if data_pool_id is not None:
            if isinstance(data_pool_id, PythonCoreBaseModel):
                params.update(data_pool_id.json_dict(by_alias=True))
            elif isinstance(data_pool_id, dict):
                params.update(data_pool_id)
            else:
                params["dataPoolId"] = data_pool_id
        if data_model_id is not None:
            if isinstance(data_model_id, PythonCoreBaseModel):
                params.update(data_model_id.json_dict(by_alias=True))
            elif isinstance(data_model_id, dict):
                params.update(data_model_id)
            else:
                params["dataModelId"] = data_model_id
        return await self.client.request(
            method="GET", url=f"/redirect-content/hybrid-integration", params=params, **kwargs
        )

    async def get_favicon_ico(self, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/favicon.ico", **kwargs)

    async def get_api_version_copy_teams(self, **kwargs: Any) -> List[Optional[TeamTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/version-copy/teams", parse_json=True, type_=List[Optional[TeamTransport]], **kwargs
        )

    async def get_api_version_copy_target_team_team_domain_pools_pool_id_versions_version_already_exists(
        self, team_domain: str, pool_id: str, version: str, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="GET",
            url=f"/api/version-copy/target-team/{team_domain}/pools/{pool_id}/versions/{version}/already-exists",
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def get_api_version_copy_target_team_team_domain_pools_pool_id_data_sources(
        self, team_domain: str, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/version-copy/target-team/{team_domain}/pools/{pool_id}/data-sources",
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_version_copy_target_team_team_domain_pools_pool_id_data_models(
        self, team_domain: str, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/version-copy/target-team/{team_domain}/pools/{pool_id}/data-models",
            parse_json=True,
            type_=List[Optional[DataModelTransport]],
            **kwargs,
        )

    async def get_api_version_copy_target_team_team_domain_pools_pool_id_data_jobs(
        self, team_domain: str, pool_id: str, **kwargs: Any
    ) -> List[Optional[JobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/version-copy/target-team/{team_domain}/pools/{pool_id}/data-jobs",
            parse_json=True,
            type_=List[Optional[JobTransport]],
            **kwargs,
        )

    async def get_api_version_copy_target_team_target_team_domain_pools(
        self, target_team_domain: str, **kwargs: Any
    ) -> List[Optional[DataPoolTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/version-copy/target-team/{target_team_domain}/pools",
            parse_json=True,
            type_=List[Optional[DataPoolTransport]],
            **kwargs,
        )

    async def get_api_v2_pools_pool_id_jobs(
        self,
        pool_id: str,
        pageable: Optional["PageableBase"] = None,
        data_source_id: Optional["str"] = None,
        **kwargs: Any,
    ) -> PageTransportJobTransport:
        params: Dict[str, Any] = {}
        if pageable is not None:
            if isinstance(pageable, PythonCoreBaseModel):
                params.update(pageable.json_dict(by_alias=True))
            elif isinstance(pageable, dict):
                params.update(pageable)
            else:
                params["pageable"] = pageable
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/v2/pools/{pool_id}/jobs",
            params=params,
            parse_json=True,
            type_=PageTransportJobTransport,
            **kwargs,
        )

    async def get_api_v1_data_push_pool_id_jobs_id_chunks(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[DataPushChunk]]:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-push/{pool_id}/jobs/{id}/chunks",
            parse_json=True,
            type_=List[Optional[DataPushChunk]],
            **kwargs,
        )

    async def get_api_v1_data_pools_pool_id_direct_data_push_schema(
        self, pool_id: str, data_source_id: Optional["str"] = None, table_name: Optional["str"] = None, **kwargs: Any
    ) -> TableTransport:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-pools/{pool_id}/direct-data-push/schema",
            params=params,
            parse_json=True,
            type_=TableTransport,
            **kwargs,
        )

    async def get_api_v1_data_pools_pool_id_direct_data_push_chunks(
        self, pool_id: str, data_source_id: Optional["str"] = None, table_name: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[DirectStorageTableChunkTransport]]:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-pools/{pool_id}/direct-data-push/chunks",
            params=params,
            parse_json=True,
            type_=List[Optional[DirectStorageTableChunkTransport]],
            **kwargs,
        )

    async def get_api_v1_data_pools_pool_id_data_models_data_model_id_tables(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/data-pools/{pool_id}/data-models/{data_model_id}/tables",
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def get_api_v1_compute_data_model_id_export_export_id(
        self, data_model_id: str, export_id: str, **kwargs: Any
    ) -> DataExportStatusResponse:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/compute/{data_model_id}/export/{export_id}",
            parse_json=True,
            type_=DataExportStatusResponse,
            **kwargs,
        )

    async def get_api_v1_compute_data_model_id_export_export_id_chunk_id_result(
        self, data_model_id: str, export_id: str, chunk_id: str, **kwargs: Any
    ) -> BytesIO:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/compute/{data_model_id}/export/{export_id}/{chunk_id}/result",
            parse_json=True,
            type_=BytesIO,
            **kwargs,
        )

    async def get_api_v1_compute_data_model_id_export_export_id_result(
        self, data_model_id: str, export_id: str, **kwargs: Any
    ) -> BytesIO:
        return await self.client.request(
            method="GET",
            url=f"/api/v1/compute/{data_model_id}/export/{export_id}/result",
            parse_json=True,
            type_=BytesIO,
            **kwargs,
        )

    async def get_api_teams_current(self, include_features: Optional["bool"] = None, **kwargs: Any) -> TeamTransport:
        params: Dict[str, Any] = {}
        if include_features is not None:
            if isinstance(include_features, PythonCoreBaseModel):
                params.update(include_features.json_dict(by_alias=True))
            elif isinstance(include_features, dict):
                params.update(include_features)
            else:
                params["includeFeatures"] = include_features
        return await self.client.request(
            method="GET", url=f"/api/teams/current", params=params, parse_json=True, type_=TeamTransport, **kwargs
        )

    async def get_api_table_partitions(self, **kwargs: Any) -> List[Optional[TablePartitionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/table_partitions",
            parse_json=True,
            type_=List[Optional[TablePartitionTransport]],
            **kwargs,
        )

    async def get_api_table_partitions_id(self, id: str, **kwargs: Any) -> TablePartitionTransport:
        return await self.client.request(
            method="GET", url=f"/api/table_partitions/{id}", parse_json=True, type_=TablePartitionTransport, **kwargs
        )

    async def delete_api_table_partitions_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/table_partitions/{id}", **kwargs)

    async def get_api_subscriptions(
        self, object_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[SubscriptionTransport]]:
        params: Dict[str, Any] = {}
        if object_type is not None:
            if isinstance(object_type, PythonCoreBaseModel):
                params.update(object_type.json_dict(by_alias=True))
            elif isinstance(object_type, dict):
                params.update(object_type)
            else:
                params["objectType"] = object_type
        return await self.client.request(
            method="GET",
            url=f"/api/subscriptions",
            params=params,
            parse_json=True,
            type_=List[Optional[SubscriptionTransport]],
            **kwargs,
        )

    async def get_api_replication_cockpit(self, **kwargs: Any) -> ReplicationCockpitServeDataTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/replication-cockpit",
            parse_json=True,
            type_=ReplicationCockpitServeDataTransport,
            **kwargs,
        )

    async def get_api_replication_cockpit_pools_pool_id_overview(
        self, pool_id: str, **kwargs: Any
    ) -> ReplicationCockpitOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/replication-cockpit/pools/{pool_id}/overview",
            parse_json=True,
            type_=ReplicationCockpitOverviewTransport,
            **kwargs,
        )

    async def get_api_realtime_processes(self, **kwargs: Any) -> List[Optional[ProcessDetailsTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/realtime-processes",
            parse_json=True,
            type_=List[Optional[ProcessDetailsTransport]],
            **kwargs,
        )

    async def get_api_public_features_global(self, **kwargs: Any) -> List[Optional[Feature]]:
        return await self.client.request(
            method="GET", url=f"/api/public/features/global", parse_json=True, type_=List[Optional[Feature]], **kwargs
        )

    async def get_api_public_authentication_status(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/public/authentication/status", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_pool_id_variables_id_tasks(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[TaskByPoolVariable]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/variables/{id}/tasks",
            parse_json=True,
            type_=List[Optional[TaskByPoolVariable]],
            **kwargs,
        )

    async def get_api_pools_pool_id_templates_task_id_instances(
        self, pool_id: str, task_id: str, **kwargs: Any
    ) -> List[Optional[TaskInstanceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/templates/{task_id}/instances",
            parse_json=True,
            type_=List[Optional[TaskInstanceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_templates_task_id_affected_job_names(
        self, pool_id: str, task_id: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/templates/{task_id}/affected-job-names",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_pools_pool_id_tasks_task_instance_id_variables_id_is_transformation_uses_variable(
        self, pool_id: str, task_instance_id: str, id: str, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/{id}/isTransformationUsesVariable",
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def get_api_pools_pool_id_tasks_task_instance_id_variables_id_extractions(
        self, pool_id: str, task_instance_id: str, id: str, **kwargs: Any
    ) -> List[Optional[TableExtractionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/tasks/{task_instance_id}/variables/{id}/extractions",
            parse_json=True,
            type_=List[Optional[TableExtractionTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_streaming_data_source_id_monitoring(
        self,
        pool_id: str,
        data_source_id: str,
        log_level: Optional["LogLevel"] = None,
        execution_type: Optional["StreamingExecutionType"] = None,
        execution_names: Optional["List[Optional[str]]"] = None,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        **kwargs: Any,
    ) -> StreamingMonitoringTransport:
        params: Dict[str, Any] = {}
        if log_level is not None:
            if isinstance(log_level, PythonCoreBaseModel):
                params.update(log_level.json_dict(by_alias=True))
            elif isinstance(log_level, dict):
                params.update(log_level)
            else:
                params["logLevel"] = log_level
        if execution_type is not None:
            if isinstance(execution_type, PythonCoreBaseModel):
                params.update(execution_type.json_dict(by_alias=True))
            elif isinstance(execution_type, dict):
                params.update(execution_type)
            else:
                params["executionType"] = execution_type
        if execution_names is not None:
            if isinstance(execution_names, PythonCoreBaseModel):
                params.update(execution_names.json_dict(by_alias=True))
            elif isinstance(execution_names, dict):
                params.update(execution_names)
            else:
                params["executionNames"] = execution_names
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/streaming/{data_source_id}/monitoring/",
            params=params,
            parse_json=True,
            type_=StreamingMonitoringTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_streaming_data_source_id_metadata(
        self, pool_id: str, data_source_id: str, table_name: Optional["str"] = None, **kwargs: Any
    ) -> DataSourceMetaData:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/streaming/{data_source_id}/metadata",
            params=params,
            parse_json=True,
            type_=DataSourceMetaData,
            **kwargs,
        )

    async def get_api_pools_pool_id_streaming_data_source_id_capabilities(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> ConnectorStreamingCapabilities:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/streaming/{data_source_id}/capabilities",
            parse_json=True,
            type_=ConnectorStreamingCapabilities,
            **kwargs,
        )

    async def get_api_pools_pool_id_streaming_table_table_id(
        self, pool_id: str, table_id: str, **kwargs: Any
    ) -> StreamingTableTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/streaming/table/{table_id}",
            parse_json=True,
            type_=StreamingTableTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_streaming_has_running_subscriptions(
        self, pool_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> bool:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/streaming/has-running-subscriptions",
            params=params,
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def get_api_pools_pool_id_scheduling_id_set_enabled(
        self, pool_id: str, id: str, enabled: Optional["bool"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if enabled is not None:
            if isinstance(enabled, PythonCoreBaseModel):
                params.update(enabled.json_dict(by_alias=True))
            elif isinstance(enabled, dict):
                params.update(enabled)
            else:
                params["enabled"] = enabled
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/scheduling/{id}/set-enabled", params=params, **kwargs
        )

    async def get_api_pools_pool_id_scheduling_availability(self, pool_id: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/scheduling/availability", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_pool_id_logs_job_id_executions(
        self, pool_id: str, job_id: str, limit: Optional["int"] = None, page: Optional["int"] = None, **kwargs: Any
    ) -> ExecutionItemWithPageTransport:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/logs/{job_id}/executions",
            params=params,
            parse_json=True,
            type_=ExecutionItemWithPageTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_logs_status(self, pool_id: str, **kwargs: Any) -> List[Optional[EntityStatus]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/logs/status",
            parse_json=True,
            type_=List[Optional[EntityStatus]],
            **kwargs,
        )

    async def get_api_pools_pool_id_logs_executions(
        self,
        pool_id: str,
        execution_id: Optional["str"] = None,
        type_: Optional["ExecutionType"] = None,
        id: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[ExecutionItemTransport]]:
        params: Dict[str, Any] = {}
        if execution_id is not None:
            if isinstance(execution_id, PythonCoreBaseModel):
                params.update(execution_id.json_dict(by_alias=True))
            elif isinstance(execution_id, dict):
                params.update(execution_id)
            else:
                params["executionId"] = execution_id
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if id is not None:
            if isinstance(id, PythonCoreBaseModel):
                params.update(id.json_dict(by_alias=True))
            elif isinstance(id, dict):
                params.update(id)
            else:
                params["id"] = id
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/logs/executions",
            params=params,
            parse_json=True,
            type_=List[Optional[ExecutionItemTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_logs_executions_detail(
        self,
        pool_id: str,
        execution_id: Optional["str"] = None,
        id: Optional["str"] = None,
        type_: Optional["ExecutionType"] = None,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        log_levels: Optional["List[Optional[LogLevel]]"] = None,
        **kwargs: Any,
    ) -> LogMessageWithPageTransport:
        params: Dict[str, Any] = {}
        if execution_id is not None:
            if isinstance(execution_id, PythonCoreBaseModel):
                params.update(execution_id.json_dict(by_alias=True))
            elif isinstance(execution_id, dict):
                params.update(execution_id)
            else:
                params["executionId"] = execution_id
        if id is not None:
            if isinstance(id, PythonCoreBaseModel):
                params.update(id.json_dict(by_alias=True))
            elif isinstance(id, dict):
                params.update(id)
            else:
                params["id"] = id
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        if log_levels is not None:
            if isinstance(log_levels, PythonCoreBaseModel):
                params.update(log_levels.json_dict(by_alias=True))
            elif isinstance(log_levels, dict):
                params.update(log_levels)
            else:
                params["logLevels"] = log_levels
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/logs/executions/detail",
            params=params,
            parse_json=True,
            type_=LogMessageWithPageTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_logs(
        self,
        pool_id: str,
        type_: Optional["ExecutionType"] = None,
        schedule_id: Optional["str"] = None,
        status: Optional["ExecutionStatus"] = None,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        **kwargs: Any,
    ) -> ExecutionItemWithPageTransport:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if schedule_id is not None:
            if isinstance(schedule_id, PythonCoreBaseModel):
                params.update(schedule_id.json_dict(by_alias=True))
            elif isinstance(schedule_id, dict):
                params.update(schedule_id)
            else:
                params["scheduleId"] = schedule_id
        if status is not None:
            if isinstance(status, PythonCoreBaseModel):
                params.update(status.json_dict(by_alias=True))
            elif isinstance(status, dict):
                params.update(status)
            else:
                params["status"] = status
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/logs/",
            params=params,
            parse_json=True,
            type_=ExecutionItemWithPageTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_workbench_transformation_id_id(
        self,
        pool_id: str,
        job_id: str,
        transformation_id: str,
        id: str,
        full_check: Optional["bool"] = None,
        **kwargs: Any,
    ) -> WorkbenchQueryStatusTransport:
        params: Dict[str, Any] = {}
        if full_check is not None:
            if isinstance(full_check, PythonCoreBaseModel):
                params.update(full_check.json_dict(by_alias=True))
            elif isinstance(full_check, dict):
                params.update(full_check)
            else:
                params["fullCheck"] = full_check
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/workbench/{transformation_id}/{id}",
            params=params,
            parse_json=True,
            type_=WorkbenchQueryStatusTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_workbench_transformation_id_id(
        self, pool_id: str, job_id: str, transformation_id: str, id: str, **kwargs: Any
    ) -> WorkbenchQueryStatusTransport:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/workbench/{transformation_id}/{id}",
            parse_json=True,
            type_=WorkbenchQueryStatusTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_workbench_transformation_id_id_results(
        self, pool_id: str, job_id: str, transformation_id: str, id: str, **kwargs: Any
    ) -> List[Optional[WorkbenchQueryResultTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/workbench/{transformation_id}/{id}/results",
            parse_json=True,
            type_=List[Optional[WorkbenchQueryResultTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_workbench_transformation_id(
        self, pool_id: str, job_id: str, transformation_id: str, **kwargs: Any
    ) -> WorkbenchQueryStatusTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/workbench/{transformation_id}/",
            parse_json=True,
            type_=WorkbenchQueryStatusTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_transformations_transformation_id(
        self, pool_id: str, job_id: str, transformation_id: str, **kwargs: Any
    ) -> TaskInstanceTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/transformations/{transformation_id}",
            parse_json=True,
            type_=TaskInstanceTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_transformations(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[TaskInstanceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/transformations/",
            parse_json=True,
            type_=List[Optional[TaskInstanceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_tasks_task_instance_id_table_configuration(
        self, pool_id: str, job_id: str, task_instance_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/tasks/{task_instance_id}/tableConfiguration",
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_loads_options(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[DataModelExecutionOption]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/options",
            parse_json=True,
            type_=List[Optional[DataModelExecutionOption]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_loads_data_model_data_model_id_table_options(
        self, pool_id: str, job_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelExecutionTableItem]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/data-model/{data_model_id}/table-options",
            parse_json=True,
            type_=List[Optional[DataModelExecutionTableItem]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_extractions_extraction_id(
        self, pool_id: str, job_id: str, extraction_id: str, **kwargs: Any
    ) -> ExtractionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}",
            parse_json=True,
            type_=ExtractionTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables_table_id(
        self, pool_id: str, job_id: str, extraction_id: str, table_id: str, **kwargs: Any
    ) -> TableExtractionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/{table_id}",
            parse_json=True,
            type_=TableExtractionTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_jobs_job_id_extractions_extraction_id_tables_table_id(
        self, pool_id: str, job_id: str, extraction_id: str, table_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/tables/{table_id}",
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_extractions_extraction_id_expanded(
        self, pool_id: str, job_id: str, extraction_id: str, **kwargs: Any
    ) -> ExtractionWithTablesTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/{extraction_id}/expanded",
            parse_json=True,
            type_=ExtractionWithTablesTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_extractions_expanded(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[ExtractionWithTablesTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/expanded",
            parse_json=True,
            type_=List[Optional[ExtractionWithTablesTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_job_id_extractions(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> List[Optional[ExtractionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{job_id}/extractions/",
            parse_json=True,
            type_=List[Optional[ExtractionTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_id_schemas(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[PoolSchema]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{id}/schemas",
            parse_json=True,
            type_=List[Optional[PoolSchema]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_id_schema_status(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> ConnectorStatus:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{id}/schema-status",
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_id_cached_schemas(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[PoolSchema]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/jobs/{id}/cachedSchemas",
            parse_json=True,
            type_=List[Optional[PoolSchema]],
            **kwargs,
        )

    async def get_api_pools_pool_id_jobs_availability(self, pool_id: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/jobs/availability", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_pool_id_job_scheduling_pool_id_schedule_id(
        self, pool_id: str, schedule_id: str, **kwargs: Any
    ) -> List[Optional[JobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/job-scheduling/{pool_id}/{schedule_id}",
            parse_json=True,
            type_=List[Optional[JobTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_files_file_id_sheets(
        self, pool_id: str, file_id: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/files/{file_id}/sheets",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_pools_pool_id_extractor_builder_custom_extractor_id(
        self, pool_id: str, custom_extractor_id: str, **kwargs: Any
    ) -> CustomExtractorTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}",
            parse_json=True,
            type_=CustomExtractorTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_extractor_builder_custom_extractor_id(
        self, pool_id: str, custom_extractor_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}", **kwargs
        )

    async def get_api_pools_pool_id_extractor_builder_custom_extractor_id_customizable_data_sources(
        self, pool_id: str, custom_extractor_id: str, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/extractor-builder/{custom_extractor_id}/customizableDataSources",
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_extractor_builder_get_customizable_extractors(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[ConfiguredConnector]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/extractor-builder/getCustomizableExtractors",
            parse_json=True,
            type_=List[Optional[ConfiguredConnector]],
            **kwargs,
        )

    async def get_api_pools_pool_id_extractor_builder(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[CustomExtractorTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/extractor-builder/",
            parse_json=True,
            type_=List[Optional[CustomExtractorTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_tables(
        self, pool_id: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PoolTable]]:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/tables",
            params=params,
            parse_json=True,
            type_=List[Optional[PoolTable]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_import_options(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataTransferImportOption]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/import-options",
            parse_json=True,
            type_=List[Optional[DataTransferImportOption]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_exports_export_id_imports(
        self, pool_id: str, export_id: str, **kwargs: Any
    ) -> List[Optional[DataTransferImportTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/exports/{export_id}/imports",
            parse_json=True,
            type_=List[Optional[DataTransferImportTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_export_export_id(
        self, pool_id: str, export_id: str, **kwargs: Any
    ) -> DataTransferExportTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/export/{export_id}",
            parse_json=True,
            type_=DataTransferExportTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_export_options(
        self, pool_id: str, **kwargs: Any
    ) -> DataTransferExportOptions:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/export-options",
            parse_json=True,
            type_=DataTransferExportOptions,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_existing_imports_export_id(
        self, pool_id: str, export_id: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/existing-imports/{export_id}",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_transfer_data_source_data_source_id_export(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> DataTransferExportTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-transfer/data-source/{data_source_id}/export",
            parse_json=True,
            type_=DataTransferExportTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> DataSourceTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}",
            parse_json=True,
            type_=DataSourceTransport,
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_sources_data_source_id(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-sources/{data_source_id}", **kwargs
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_search_tables(
        self,
        pool_id: str,
        data_source_id: str,
        extraction_id: Optional["str"] = None,
        search_string: Optional["str"] = None,
        **kwargs: Any,
    ) -> DataSourceAvailableTables:
        params: Dict[str, Any] = {}
        if extraction_id is not None:
            if isinstance(extraction_id, PythonCoreBaseModel):
                params.update(extraction_id.json_dict(by_alias=True))
            elif isinstance(extraction_id, dict):
                params.update(extraction_id)
            else:
                params["extractionId"] = extraction_id
        if search_string is not None:
            if isinstance(search_string, PythonCoreBaseModel):
                params.update(search_string.json_dict(by_alias=True))
            elif isinstance(search_string, dict):
                params.update(search_string)
            else:
                params["searchString"] = search_string
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/search-tables",
            params=params,
            parse_json=True,
            type_=DataSourceAvailableTables,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_meta_data(
        self,
        pool_id: str,
        data_source_id: str,
        table_name: Optional["str"] = None,
        extraction_id: Optional["str"] = None,
        schema_name: Optional["str"] = None,
        parent_table: Optional["str"] = None,
        **kwargs: Any,
    ) -> DataSourceMetaData:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        if extraction_id is not None:
            if isinstance(extraction_id, PythonCoreBaseModel):
                params.update(extraction_id.json_dict(by_alias=True))
            elif isinstance(extraction_id, dict):
                params.update(extraction_id)
            else:
                params["extractionId"] = extraction_id
        if schema_name is not None:
            if isinstance(schema_name, PythonCoreBaseModel):
                params.update(schema_name.json_dict(by_alias=True))
            elif isinstance(schema_name, dict):
                params.update(schema_name)
            else:
                params["schemaName"] = schema_name
        if parent_table is not None:
            if isinstance(parent_table, PythonCoreBaseModel):
                params.update(parent_table.json_dict(by_alias=True))
            elif isinstance(parent_table, dict):
                params.update(parent_table)
            else:
                params["parentTable"] = parent_table
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/meta-data",
            params=params,
            parse_json=True,
            type_=DataSourceMetaData,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_get_connector_information(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> ConnectorInformation:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/getConnectorInformation",
            parse_json=True,
            type_=ConnectorInformation,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_extraction_logs(
        self,
        pool_id: str,
        data_source_id: str,
        start_date: Optional["int"] = None,
        end_date: Optional["int"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if start_date is not None:
            if isinstance(start_date, PythonCoreBaseModel):
                params.update(start_date.json_dict(by_alias=True))
            elif isinstance(start_date, dict):
                params.update(start_date)
            else:
                params["startDate"] = start_date
        if end_date is not None:
            if isinstance(end_date, PythonCoreBaseModel):
                params.update(end_date.json_dict(by_alias=True))
            elif isinstance(end_date, dict):
                params.update(end_date)
            else:
                params["endDate"] = end_date
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/extractionLogs",
            params=params,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_data_source_status(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> DataSourceStatus:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/data-source-status",
            parse_json=True,
            type_=DataSourceStatus,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_check(
        self, pool_id: str, data_source_id: str, full_check: Optional["bool"] = None, **kwargs: Any
    ) -> ConnectorStatus:
        params: Dict[str, Any] = {}
        if full_check is not None:
            if isinstance(full_check, PythonCoreBaseModel):
                params.update(full_check.json_dict(by_alias=True))
            elif isinstance(full_check, dict):
                params.update(full_check)
            else:
                params["fullCheck"] = full_check
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/check",
            params=params,
            parse_json=True,
            type_=ConnectorStatus,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_check_imported(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> ImportedDataSourceChangesTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/check-imported",
            parse_json=True,
            type_=ImportedDataSourceChangesTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_change_log_table_metadata(
        self, pool_id: str, data_source_id: str, table_name: Optional["str"] = None, **kwargs: Any
    ) -> ChangeLogStatus:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/change-log-table-metadata",
            params=params,
            parse_json=True,
            type_=ChangeLogStatus,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_data_source_id_capabilities(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> ConnectorCapabilities:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/{data_source_id}/capabilities",
            parse_json=True,
            type_=ConnectorCapabilities,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_type_job_id(
        self, pool_id: str, job_id: str, **kwargs: Any
    ) -> DataSourceTypeTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/type/{job_id}",
            parse_json=True,
            type_=DataSourceTypeTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_streaming_scopes(
        self,
        pool_id: str,
        exclude_unconfigured: Optional["bool"] = None,
        distinct: Optional["bool"] = None,
        type_: Optional["str"] = None,
        limit: Optional["int"] = None,
        **kwargs: Any,
    ) -> List[Optional[DataSourceTransport]]:
        params: Dict[str, Any] = {}
        if exclude_unconfigured is not None:
            if isinstance(exclude_unconfigured, PythonCoreBaseModel):
                params.update(exclude_unconfigured.json_dict(by_alias=True))
            elif isinstance(exclude_unconfigured, dict):
                params.update(exclude_unconfigured)
            else:
                params["excludeUnconfigured"] = exclude_unconfigured
        if distinct is not None:
            if isinstance(distinct, PythonCoreBaseModel):
                params.update(distinct.json_dict(by_alias=True))
            elif isinstance(distinct, dict):
                params.update(distinct)
            else:
                params["distinct"] = distinct
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/streaming-scopes",
            params=params,
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_overview(
        self, pool_id: str, limit: Optional["int"] = None, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/overview",
            params=params,
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_sources_availability(self, pool_id: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/data-sources/availability", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_pool_id_data_sources(
        self,
        pool_id: str,
        exclude_unconfigured: Optional["bool"] = None,
        distinct: Optional["bool"] = None,
        type_: Optional["str"] = None,
        limit: Optional["int"] = None,
        exclude_only_realtime_connectors: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[DataSourceTransport]]:
        params: Dict[str, Any] = {}
        if exclude_unconfigured is not None:
            if isinstance(exclude_unconfigured, PythonCoreBaseModel):
                params.update(exclude_unconfigured.json_dict(by_alias=True))
            elif isinstance(exclude_unconfigured, dict):
                params.update(exclude_unconfigured)
            else:
                params["excludeUnconfigured"] = exclude_unconfigured
        if distinct is not None:
            if isinstance(distinct, PythonCoreBaseModel):
                params.update(distinct.json_dict(by_alias=True))
            elif isinstance(distinct, dict):
                params.update(distinct)
            else:
                params["distinct"] = distinct
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if exclude_only_realtime_connectors is not None:
            if isinstance(exclude_only_realtime_connectors, PythonCoreBaseModel):
                params.update(exclude_only_realtime_connectors.json_dict(by_alias=True))
            elif isinstance(exclude_only_realtime_connectors, dict):
                params.update(exclude_only_realtime_connectors)
            else:
                params["excludeOnlyRealtimeConnectors"] = exclude_only_realtime_connectors
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-sources/",
            params=params,
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_transport(
        self, pool_id: str, data_model_id: str, include_columns: Optional["bool"] = None, **kwargs: Any
    ) -> DataModelTransport:
        params: Dict[str, Any] = {}
        if include_columns is not None:
            if isinstance(include_columns, PythonCoreBaseModel):
                params.update(include_columns.json_dict(by_alias=True))
            elif isinstance(include_columns, dict):
                params.update(include_columns)
            else:
                params["includeColumns"] = include_columns
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/transport",
            params=params,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_sync_jobs(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[TableSyncJobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/sync-jobs",
            parse_json=True,
            type_=List[Optional[TableSyncJobTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_sync_jobs_table_load_history(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTableLoadingHistoryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/sync-jobs/table-load-history",
            parse_json=True,
            type_=List[Optional[DataModelTableLoadingHistoryTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_sync_jobs_live_data_model_tables(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelLoadTableExtendedTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/sync-jobs/live-data-model-tables",
            parse_json=True,
            type_=List[Optional[DataModelLoadTableExtendedTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_process_configurations_activity_table_activity_table_id(
        self, pool_id: str, data_model_id: str, activity_table_id: str, **kwargs: Any
    ) -> DataModelConfiguration:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/process-configurations/activityTable/{activity_table_id}",
            parse_json=True,
            type_=DataModelConfiguration,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_name_mapping(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[NameMappingTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping",
            parse_json=True,
            type_=List[Optional[NameMappingTransport]],
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_name_mapping(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_name_mapping_template(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping/template", **kwargs
        )

    async def get_api_pools_pool_id_data_models_data_model_id_name_mapping_aggregated(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[NameMappingAggregated]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/name-mapping/aggregated",
            parse_json=True,
            type_=List[Optional[NameMappingAggregated]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_load_history(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataLoadHistoryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/load-history",
            parse_json=True,
            type_=List[Optional[DataLoadHistoryTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_load_history_load_info_sync(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelLoadSyncTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/load-history/load-info-sync",
            parse_json=True,
            type_=DataModelLoadSyncTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_load_history_last(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataLoadHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/load-history/last",
            parse_json=True,
            type_=DataLoadHistoryTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_load_history_last_successful(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataLoadHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/load-history/last-successful",
            parse_json=True,
            type_=DataLoadHistoryTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_load_history_current(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataLoadHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/load-history/current",
            parse_json=True,
            type_=DataLoadHistoryTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_live(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelLoadTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/live",
            parse_json=True,
            type_=DataModelLoadTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_license_for_activity_table(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> ActivityTableCreationRestriction:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/license-for-activity-table",
            parse_json=True,
            type_=ActivityTableCreationRestriction,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataPermission:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission",
            parse_json=True,
            type_=DataPermission,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_type_deprecated_rule(
        self, pool_id: str, data_model_id: str, type_: DataPermissionType, **kwargs: Any
    ) -> List[Optional[DataPermissionAssignmentRuleTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{type_}/deprecated-rule",
            parse_json=True,
            type_=List[Optional[DataPermissionAssignmentRuleTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_permission_tables_check_synchronize_status(
        self, pool_id: str, data_model_id: str, data_permission_id: str, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/permission-tables/checkSynchronizeStatus",
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_factory_proposal(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelFactoryCalendar:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/factory/proposal",
            parse_json=True,
            type_=DataModelFactoryCalendar,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_factory_enable(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/factory/enable",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_disable(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/disable",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_data_model_id_calendar_custom_enable(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/calendar/custom/enable",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_status(
        self, pool_id: str, limit: Optional["int"] = None, **kwargs: Any
    ) -> List[Optional[DataModelWithStatusTransport]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/status",
            params=params,
            parse_json=True,
            type_=List[Optional[DataModelWithStatusTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_overview(
        self, pool_id: str, **kwargs: Any
    ) -> DataPoolDataModelOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/overview",
            parse_json=True,
            type_=DataPoolDataModelOverviewTransport,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_list(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataModelListItemTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-models/list",
            parse_json=True,
            type_=List[Optional[DataModelListItemTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_models_availability(self, pool_id: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/{pool_id}/data-models/availability", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables_table_id_preview(
        self, pool_id: str, data_model_id: str, table_id: str, limit: Optional["int"] = None, **kwargs: Any
    ) -> PoolTablePreview:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{table_id}/preview",
            params=params,
            parse_json=True,
            type_=PoolTablePreview,
            **kwargs,
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables_table_id_data_permission_assignments(
        self, pool_id: str, data_model_id: str, table_id: str, **kwargs: Any
    ) -> List[Optional[DataPermissionAssignmentTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{table_id}/data-permission-assignments",
            parse_json=True,
            type_=List[Optional[DataPermissionAssignmentTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables_table_id_columns(
        self, pool_id: str, data_model_id: str, table_id: str, **kwargs: Any
    ) -> List[Optional[PoolColumn]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{table_id}/columns",
            parse_json=True,
            type_=List[Optional[PoolColumn]],
            **kwargs,
        )

    async def get_api_pools_pool_id_data_model_data_model_id_tables_activity(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/activity",
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def get_api_pools_pool_id_anonymization_salts(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[AnonymizationSaltTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{pool_id}/anonymization-salts/",
            parse_json=True,
            type_=List[Optional[AnonymizationSaltTransport]],
            **kwargs,
        )

    async def get_api_pools_id_versions(self, id: str, **kwargs: Any) -> List[Optional[DraftTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/versions",
            parse_json=True,
            type_=List[Optional[DraftTransport]],
            **kwargs,
        )

    async def delete_api_pools_id_versions(
        self, id: str, request_body: List[Optional[DraftTransport]], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{id}/versions", request_body=request_body, **kwargs
        )

    async def get_api_pools_id_versions_draft_id_serialized_content(
        self, id: str, draft_id: str, **kwargs: Any
    ) -> DataPoolVersionSlim:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/versions/{draft_id}/serializedContent",
            parse_json=True,
            type_=DataPoolVersionSlim,
            **kwargs,
        )

    async def get_api_pools_id_tables(self, id: str, **kwargs: Any) -> List[Optional[PoolTable]]:
        return await self.client.request(
            method="GET", url=f"/api/pools/{id}/tables", parse_json=True, type_=List[Optional[PoolTable]], **kwargs
        )

    async def get_api_pools_id_tables_and_columns(self, id: str, **kwargs: Any) -> List[Optional[PoolTable]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/tables-and-columns",
            parse_json=True,
            type_=List[Optional[PoolTable]],
            **kwargs,
        )

    async def get_api_pools_id_processes(self, id: str, **kwargs: Any) -> List[Optional[str]]:
        return await self.client.request(
            method="GET", url=f"/api/pools/{id}/processes", parse_json=True, type_=List[Optional[str]], **kwargs
        )

    async def get_api_pools_id_move_target_domain_license(
        self, id: str, target_domain: str, **kwargs: Any
    ) -> DataModelCreationRestrictionWithSelection:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/move/{target_domain}/license",
            parse_json=True,
            type_=DataModelCreationRestrictionWithSelection,
            **kwargs,
        )

    async def get_api_pools_id_initial_load_status(
        self, id: str, **kwargs: Any
    ) -> List[Optional[ApplicationWizardExecutionSummary]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/initial-load-status",
            parse_json=True,
            type_=List[Optional[ApplicationWizardExecutionSummary]],
            **kwargs,
        )

    async def get_api_pools_id_export(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/api/pools/{id}/export", **kwargs)

    async def get_api_pools_id_current_export(self, id: str, **kwargs: Any) -> DataPoolVersionSlim:
        return await self.client.request(
            method="GET", url=f"/api/pools/{id}/currentExport", parse_json=True, type_=DataPoolVersionSlim, **kwargs
        )

    async def get_api_pools_id_columns(
        self, id: str, table_name: Optional["str"] = None, schema_name: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PoolColumn]]:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        if schema_name is not None:
            if isinstance(schema_name, PythonCoreBaseModel):
                params.update(schema_name.json_dict(by_alias=True))
            elif isinstance(schema_name, dict):
                params.update(schema_name)
            else:
                params["schemaName"] = schema_name
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{id}/columns",
            params=params,
            parse_json=True,
            type_=List[Optional[PoolColumn]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_tables_preview(
        self,
        data_pool_id: str,
        table_name: Optional["str"] = None,
        data_source_id: Optional["str"] = None,
        limit: Optional["int"] = None,
        **kwargs: Any,
    ) -> PoolTablePreview:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/tables/preview",
            params=params,
            parse_json=True,
            type_=PoolTablePreview,
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_studio_packages(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[StudioPackageOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/studio-packages",
            parse_json=True,
            type_=List[Optional[StudioPackageOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_schedules(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[SchedulingOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/schedules",
            parse_json=True,
            type_=List[Optional[SchedulingOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_replication_cockpit(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[ReplicationCockpitTableOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/replication-cockpit",
            parse_json=True,
            type_=List[Optional[ReplicationCockpitTableOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_data_sources(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[DataSourceOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/data-sources",
            parse_json=True,
            type_=List[Optional[DataSourceOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_data_models(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[DataModelOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/data-models",
            parse_json=True,
            type_=List[Optional[DataModelOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overviews_data_jobs(
        self, data_pool_id: str, **kwargs: Any
    ) -> List[Optional[DataJobOverviewTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overviews/data-jobs",
            parse_json=True,
            type_=List[Optional[DataJobOverviewTransport]],
            **kwargs,
        )

    async def get_api_pools_data_pool_id_overview(self, data_pool_id: str, **kwargs: Any) -> DataPoolOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/{data_pool_id}/overview",
            parse_json=True,
            type_=DataPoolOverviewTransport,
            **kwargs,
        )

    async def get_api_pools_type(self, **kwargs: Any) -> PoolProviderType:
        return await self.client.request(
            method="GET", url=f"/api/pools/type", parse_json=True, type_=PoolProviderType, **kwargs
        )

    async def get_api_pools_status(
        self, data_pool_ids: Optional["List[Optional[str]]"] = None, **kwargs: Any
    ) -> List[Optional[EntityStatus]]:
        params: Dict[str, Any] = {}
        if data_pool_ids is not None:
            if isinstance(data_pool_ids, PythonCoreBaseModel):
                params.update(data_pool_ids.json_dict(by_alias=True))
            elif isinstance(data_pool_ids, dict):
                params.update(data_pool_ids)
            else:
                params["dataPoolIds"] = data_pool_ids
        return await self.client.request(
            method="GET",
            url=f"/api/pools/status",
            params=params,
            parse_json=True,
            type_=List[Optional[EntityStatus]],
            **kwargs,
        )

    async def get_api_pools_pools_extended_content(
        self, team_domain: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[DataPoolWithExtendedContentTransport]]:
        params: Dict[str, Any] = {}
        if team_domain is not None:
            if isinstance(team_domain, PythonCoreBaseModel):
                params.update(team_domain.json_dict(by_alias=True))
            elif isinstance(team_domain, dict):
                params.update(team_domain)
            else:
                params["teamDomain"] = team_domain
        return await self.client.request(
            method="GET",
            url=f"/api/pools/pools-extended-content",
            params=params,
            parse_json=True,
            type_=List[Optional[DataPoolWithExtendedContentTransport]],
            **kwargs,
        )

    async def get_api_pools_paged(
        self,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        sort: Optional["str"] = None,
        ascending: Optional["bool"] = None,
        search: Optional["str"] = None,
        **kwargs: Any,
    ) -> DataPoolPageTransport:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        if sort is not None:
            if isinstance(sort, PythonCoreBaseModel):
                params.update(sort.json_dict(by_alias=True))
            elif isinstance(sort, dict):
                params.update(sort)
            else:
                params["sort"] = sort
        if ascending is not None:
            if isinstance(ascending, PythonCoreBaseModel):
                params.update(ascending.json_dict(by_alias=True))
            elif isinstance(ascending, dict):
                params.update(ascending)
            else:
                params["ascending"] = ascending
        if search is not None:
            if isinstance(search, PythonCoreBaseModel):
                params.update(search.json_dict(by_alias=True))
            elif isinstance(search, dict):
                params.update(search)
            else:
                params["search"] = search
        return await self.client.request(
            method="GET", url=f"/api/pools/paged", params=params, parse_json=True, type_=DataPoolPageTransport, **kwargs
        )

    async def get_api_pools_old_monitoring_exists(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/old-monitoring-exists", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_pools_move_target_domain_version(
        self, target_domain: str, **kwargs: Any
    ) -> DataPoolMoveHybridVersionCheck:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/move/{target_domain}/version",
            parse_json=True,
            type_=DataPoolMoveHybridVersionCheck,
            **kwargs,
        )

    async def get_api_pools_monitoring(
        self,
        status: Optional["ExecutionStatus"] = None,
        type_: Optional["ExecutionType"] = None,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        **kwargs: Any,
    ) -> ExecutionItemWithPageTransport:
        params: Dict[str, Any] = {}
        if status is not None:
            if isinstance(status, PythonCoreBaseModel):
                params.update(status.json_dict(by_alias=True))
            elif isinstance(status, dict):
                params.update(status)
            else:
                params["status"] = status
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        return await self.client.request(
            method="GET",
            url=f"/api/pools/monitoring/",
            params=params,
            parse_json=True,
            type_=ExecutionItemWithPageTransport,
            **kwargs,
        )

    async def get_api_pools_manage_permissions_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/manage-permissions/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_pools_hybrid(self, **kwargs: Any) -> bool:
        return await self.client.request(method="GET", url=f"/api/pools/hybrid", parse_json=True, type_=bool, **kwargs)

    async def get_api_pools_data_consumption_team(self, **kwargs: Any) -> TeamConsumptionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/pools/data-consumption/team",
            parse_json=True,
            type_=TeamConsumptionTransport,
            **kwargs,
        )

    async def get_api_pools_data_consumption(
        self,
        limit: Optional["int"] = None,
        page: Optional["int"] = None,
        sort: Optional["str"] = None,
        search: Optional["str"] = None,
        **kwargs: Any,
    ) -> ExtendedTableConsumptionPageTransport:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if page is not None:
            if isinstance(page, PythonCoreBaseModel):
                params.update(page.json_dict(by_alias=True))
            elif isinstance(page, dict):
                params.update(page)
            else:
                params["page"] = page
        if sort is not None:
            if isinstance(sort, PythonCoreBaseModel):
                params.update(sort.json_dict(by_alias=True))
            elif isinstance(sort, dict):
                params.update(sort)
            else:
                params["sort"] = sort
        if search is not None:
            if isinstance(search, PythonCoreBaseModel):
                params.update(search.json_dict(by_alias=True))
            elif isinstance(search, dict):
                params.update(search)
            else:
                params["search"] = search
        return await self.client.request(
            method="GET",
            url=f"/api/pools/data-consumption/",
            params=params,
            parse_json=True,
            type_=ExtendedTableConsumptionPageTransport,
            **kwargs,
        )

    async def get_api_pools_custom_pool_id(
        self, pool_id: str, create: Optional["bool"] = None, **kwargs: Any
    ) -> CustomDataPoolConfigurationTransport:
        params: Dict[str, Any] = {}
        if create is not None:
            if isinstance(create, PythonCoreBaseModel):
                params.update(create.json_dict(by_alias=True))
            elif isinstance(create, dict):
                params.update(create)
            else:
                params["create"] = create
        return await self.client.request(
            method="GET",
            url=f"/api/pools/custom/{pool_id}",
            params=params,
            parse_json=True,
            type_=CustomDataPoolConfigurationTransport,
            **kwargs,
        )

    async def get_api_pools_custom_monitoring_exists(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/pools/custom-monitoring-exists", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_package_install_realtime_processes(
        self, **kwargs: Any
    ) -> List[Optional[ProcessDetailsTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-install/realtime-processes",
            parse_json=True,
            type_=List[Optional[ProcessDetailsTransport]],
            **kwargs,
        )

    async def get_api_package_install_process_content_store_id(
        self, content_store_id: str, **kwargs: Any
    ) -> PackageInformation:
        return await self.client.request(
            method="GET",
            url=f"/api/package-install/process/{content_store_id}",
            parse_json=True,
            type_=PackageInformation,
            **kwargs,
        )

    async def get_api_package_install_process_content_store_id_check_available(
        self, content_store_id: str, type_: Optional["HybridPoolProviderType"] = None, **kwargs: Any
    ) -> List[Optional[PackageDataConnectionInformation]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        return await self.client.request(
            method="GET",
            url=f"/api/package-install/process/{content_store_id}/check-available",
            params=params,
            parse_json=True,
            type_=List[Optional[PackageDataConnectionInformation]],
            **kwargs,
        )

    async def get_api_locks(self, **kwargs: Any) -> List[Optional[JobFutureTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/locks", parse_json=True, type_=List[Optional[JobFutureTransport]], **kwargs
        )

    async def get_api_locks_id(self, id: str, **kwargs: Any) -> JobFutureTransport:
        return await self.client.request(
            method="GET", url=f"/api/locks/{id}", parse_json=True, type_=JobFutureTransport, **kwargs
        )

    async def delete_api_locks_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/locks/{id}", **kwargs)

    async def get_api_features(self, **kwargs: Any) -> FeaturesTransport:
        return await self.client.request(
            method="GET", url=f"/api/features", parse_json=True, type_=FeaturesTransport, **kwargs
        )

    async def get_api_datasource_zendesk_id_redirect(
        self, id: str, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> ZendeskRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/zendesk/{id}/redirect",
            params=params,
            parse_json=True,
            type_=ZendeskRedirectTransport,
            **kwargs,
        )

    async def get_api_datasource_zendesk_redirect_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/zendesk-redirect/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_snowflake_rest_redirect_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/snowflake-rest-redirect/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_service_now_id_redirect(
        self, id: str, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> ServiceNowRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/service-now/{id}/redirect",
            params=params,
            parse_json=True,
            type_=ServiceNowRedirectTransport,
            **kwargs,
        )

    async def get_api_datasource_service_now_default_config(self, **kwargs: Any) -> ServiceNowDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/service-now/defaultConfig",
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def get_api_datasource_service_now_redirect_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/service-now-redirect/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_service_now_demo_default_config(self, **kwargs: Any) -> ServiceNowDataSource:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/service-now-demo/defaultConfig",
            parse_json=True,
            type_=ServiceNowDataSource,
            **kwargs,
        )

    async def get_api_datasource_sap_demo_configuration(self, **kwargs: Any) -> DemoSapConnectionConfiguration:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/sap/demo-configuration",
            parse_json=True,
            type_=DemoSapConnectionConfiguration,
            **kwargs,
        )

    async def get_api_datasource_salesforce_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/salesforce/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_salesforce_id_redirect(
        self, id: str, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> SalesforceRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/salesforce/{id}/redirect",
            params=params,
            parse_json=True,
            type_=SalesforceRedirectTransport,
            **kwargs,
        )

    async def get_api_datasource_google_sheets_id_redirect(
        self, id: str, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> GoogleSheetsRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/google-sheets/{id}/redirect",
            params=params,
            parse_json=True,
            type_=GoogleSheetsRedirectTransport,
            **kwargs,
        )

    async def get_api_datasource_google_sheets_redirect_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/google-sheets-redirect/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_database_redirect_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/database-redirect/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_custom_extractor_id_redirect_next(
        self, id: str, code: Optional["str"] = None, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if code is not None:
            if isinstance(code, PythonCoreBaseModel):
                params.update(code.json_dict(by_alias=True))
            elif isinstance(code, dict):
                params.update(code)
            else:
                params["code"] = code
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET", url=f"/api/datasource/custom-extractor/{id}/redirect_next", params=params, **kwargs
        )

    async def get_api_datasource_custom_extractor_id_redirect(
        self, id: str, ui_path: Optional["str"] = None, **kwargs: Any
    ) -> CustomExtractorRedirectTransport:
        params: Dict[str, Any] = {}
        if ui_path is not None:
            if isinstance(ui_path, PythonCoreBaseModel):
                params.update(ui_path.json_dict(by_alias=True))
            elif isinstance(ui_path, dict):
                params.update(ui_path)
            else:
                params["uiPath"] = ui_path
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/custom-extractor/{id}/redirect",
            params=params,
            parse_json=True,
            type_=CustomExtractorRedirectTransport,
            **kwargs,
        )

    async def get_api_database_connection_templates(self, **kwargs: Any) -> List[Optional[DatabaseConnectionTemplate]]:
        return await self.client.request(
            method="GET",
            url=f"/api/database-connection-templates",
            parse_json=True,
            type_=List[Optional[DatabaseConnectionTemplate]],
            **kwargs,
        )

    async def get_api_database_connection_templates_connection_type(
        self, connection_type: str, **kwargs: Any
    ) -> List[Optional[DatabaseConnectionTemplate]]:
        return await self.client.request(
            method="GET",
            url=f"/api/database-connection-templates/{connection_type}",
            parse_json=True,
            type_=List[Optional[DatabaseConnectionTemplate]],
            **kwargs,
        )

    async def get_api_database_connection_templates_pool(
        self, **kwargs: Any
    ) -> List[Optional[DatabaseConnectionTemplate]]:
        return await self.client.request(
            method="GET",
            url=f"/api/database-connection-templates/pool",
            parse_json=True,
            type_=List[Optional[DatabaseConnectionTemplate]],
            **kwargs,
        )

    async def get_api_database_connection_templates_pool_connection_type(
        self, connection_type: str, **kwargs: Any
    ) -> List[Optional[DatabaseConnectionTemplate]]:
        return await self.client.request(
            method="GET",
            url=f"/api/database-connection-templates/pool/{connection_type}",
            parse_json=True,
            type_=List[Optional[DatabaseConnectionTemplate]],
            **kwargs,
        )

    async def get_api_data_uploader(self, **kwargs: Any) -> DataUploaderServeDataTransport:
        return await self.client.request(
            method="GET", url=f"/api/data-uploader", parse_json=True, type_=DataUploaderServeDataTransport, **kwargs
        )

    async def get_api_data_pipeline_orchestrator(self, **kwargs: Any) -> DataPipelineOrchestratorServeDataTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/data-pipeline-orchestrator",
            parse_json=True,
            type_=DataPipelineOrchestratorServeDataTransport,
            **kwargs,
        )

    async def get_api_data_pipeline_history(self, **kwargs: Any) -> DataPipelineHistoryServeDataTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/data-pipeline-history",
            parse_json=True,
            type_=DataPipelineHistoryServeDataTransport,
            **kwargs,
        )

    async def get_api_data_models_manage_permissions_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/data-models/manage-permissions/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_data_models_license(
        self, data_pool_id: Optional["str"] = None, **kwargs: Any
    ) -> DataModelCreationRestriction:
        params: Dict[str, Any] = {}
        if data_pool_id is not None:
            if isinstance(data_pool_id, PythonCoreBaseModel):
                params.update(data_pool_id.json_dict(by_alias=True))
            elif isinstance(data_pool_id, dict):
                params.update(data_pool_id)
            else:
                params["dataPoolId"] = data_pool_id
        return await self.client.request(
            method="GET",
            url=f"/api/data-models/license",
            params=params,
            parse_json=True,
            type_=DataModelCreationRestriction,
            **kwargs,
        )

    async def get_api_configured_connectors(self, pool_id: Optional["str"] = None, **kwargs: Any) -> ConnectorList:
        params: Dict[str, Any] = {}
        if pool_id is not None:
            if isinstance(pool_id, PythonCoreBaseModel):
                params.update(pool_id.json_dict(by_alias=True))
            elif isinstance(pool_id, dict):
                params.update(pool_id)
            else:
                params["poolId"] = pool_id
        return await self.client.request(
            method="GET",
            url=f"/api/configured-connectors",
            params=params,
            parse_json=True,
            type_=ConnectorList,
            **kwargs,
        )

    async def get_api_configured_connectors_type(
        self, type_: str, streaming_connector: Optional["bool"] = None, **kwargs: Any
    ) -> ConnectorTransport:
        params: Dict[str, Any] = {}
        if streaming_connector is not None:
            if isinstance(streaming_connector, PythonCoreBaseModel):
                params.update(streaming_connector.json_dict(by_alias=True))
            elif isinstance(streaming_connector, dict):
                params.update(streaming_connector)
            else:
                params["streamingConnector"] = streaming_connector
        return await self.client.request(
            method="GET",
            url=f"/api/configured-connectors/{type_}",
            params=params,
            parse_json=True,
            type_=ConnectorTransport,
            **kwargs,
        )

    async def get_api_compute_monitoring_data_model_id_manage_data_state_action(
        self, data_model_id: str, action: str, **kwargs: Any
    ) -> bool:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-monitoring/{data_model_id}/manage_data_state/{action}",
            parse_json=True,
            type_=bool,
            **kwargs,
        )

    async def get_api_compute_monitoring_data_model_id_data_state(
        self, data_model_id: str, **kwargs: Any
    ) -> DataStateTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-monitoring/{data_model_id}/data_state",
            parse_json=True,
            type_=DataStateTransport,
            **kwargs,
        )

    async def delete_api_v1_data_pools_pool_id_direct_data_push_chunks_chunk_id(
        self,
        pool_id: str,
        chunk_id: str,
        data_source_id: Optional["str"] = None,
        table_name: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="DELETE",
            url=f"/api/v1/data-pools/{pool_id}/direct-data-push/chunks/{chunk_id}",
            params=params,
            **kwargs,
        )

    async def delete_api_pools_pool_id_templates_bulk(
        self, pool_id: str, request_body: BulkTaskTemplateRequestBase, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/templates/bulk", request_body=request_body, **kwargs
        )

    async def delete_api_pools_pool_id_jobs_job_id(self, pool_id: str, job_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/pools/{pool_id}/jobs/{job_id}", **kwargs)

    async def delete_api_pools_pool_id_jobs_job_id_loads_id(
        self, pool_id: str, job_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/jobs/{job_id}/loads/{id}", **kwargs
        )

    async def delete_api_pools_pool_id_job_scheduling_job_schedule_id(
        self, pool_id: str, job_schedule_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/job-scheduling/{job_schedule_id}", **kwargs
        )

    async def delete_api_pools_pool_id_data_transfer_imports_import_id(
        self, pool_id: str, import_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-transfer/imports/{import_id}", **kwargs
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_process_configurations_process_configuration_id(
        self, pool_id: str, data_model_id: str, process_configuration_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/process-configurations/{process_configuration_id}",
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_models_data_model_id_data_permission_data_permission_id_permission_tables_permission_table_id(
        self, pool_id: str, data_model_id: str, data_permission_id: str, permission_table_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/pools/{pool_id}/data-models/{data_model_id}/data-permission/{data_permission_id}/permission-tables/{permission_table_id}",
            **kwargs,
        )

    async def delete_api_pools_pool_id_data_model_data_model_id_tables_table_id(
        self, pool_id: str, data_model_id: str, table_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/pools/{pool_id}/data-model/{data_model_id}/tables/{table_id}", **kwargs
        )

    async def delete_api_datasource_custom_extractor_authentication_method_delete(
        self,
        request_body: CustomExtractorAuthenticationTransport,
        pool_id: Optional["str"] = None,
        id: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if pool_id is not None:
            if isinstance(pool_id, PythonCoreBaseModel):
                params.update(pool_id.json_dict(by_alias=True))
            elif isinstance(pool_id, dict):
                params.update(pool_id)
            else:
                params["poolId"] = pool_id
        if id is not None:
            if isinstance(id, PythonCoreBaseModel):
                params.update(id.json_dict(by_alias=True))
            elif isinstance(id, dict):
                params.update(id)
            else:
                params["id"] = id
        return await self.client.request(
            method="DELETE",
            url=f"/api/datasource/custom-extractor/authenticationMethod/delete",
            params=params,
            request_body=request_body,
            **kwargs,
        )

    async def get_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="GET", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def put_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="PUT", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def post_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="POST", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def delete_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="DELETE", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def options_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="OPTIONS",
            url=f"/swagger-resources",
            parse_json=True,
            type_=List[Optional[SwaggerResource]],
            **kwargs,
        )

    async def head_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="HEAD", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def patch_swagger_resources(self, **kwargs: Any) -> List[Optional[SwaggerResource]]:
        return await self.client.request(
            method="PATCH", url=f"/swagger-resources", parse_json=True, type_=List[Optional[SwaggerResource]], **kwargs
        )

    async def get_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="GET", url=f"/swagger-resources/configuration/ui", parse_json=True, type_=UiConfiguration, **kwargs
        )

    async def put_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="PUT", url=f"/swagger-resources/configuration/ui", parse_json=True, type_=UiConfiguration, **kwargs
        )

    async def post_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="POST", url=f"/swagger-resources/configuration/ui", parse_json=True, type_=UiConfiguration, **kwargs
        )

    async def delete_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="DELETE",
            url=f"/swagger-resources/configuration/ui",
            parse_json=True,
            type_=UiConfiguration,
            **kwargs,
        )

    async def options_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="OPTIONS",
            url=f"/swagger-resources/configuration/ui",
            parse_json=True,
            type_=UiConfiguration,
            **kwargs,
        )

    async def head_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="HEAD", url=f"/swagger-resources/configuration/ui", parse_json=True, type_=UiConfiguration, **kwargs
        )

    async def patch_swagger_resources_configuration_ui(self, **kwargs: Any) -> UiConfiguration:
        return await self.client.request(
            method="PATCH", url=f"/swagger-resources/configuration/ui", parse_json=True, type_=UiConfiguration, **kwargs
        )

    async def get_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="GET",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def put_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="PUT",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def post_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="POST",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def delete_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="DELETE",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def options_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="OPTIONS",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def head_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="HEAD",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def patch_swagger_resources_configuration_security(self, **kwargs: Any) -> SecurityConfiguration:
        return await self.client.request(
            method="PATCH",
            url=f"/swagger-resources/configuration/security",
            parse_json=True,
            type_=SecurityConfiguration,
            **kwargs,
        )

    async def get_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="GET", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def put_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="PUT", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def post_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="POST", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def delete_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="DELETE", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def options_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="OPTIONS", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def head_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="HEAD", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def patch_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="PATCH", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )


class IntegrationClient(IntegrationClientBase):
    async def put_api_internal_secured_v1_migration_pools_pool_id_data_models_data_model_id(
        self, pool_id: str, data_model_id: str, request_body: DataModelTransport, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models/{data_model_id}",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_internal_pool_provider_configurations_id(
        self, id: str, **kwargs: Any
    ) -> Union[CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/configurations/{id}",
            parse_json=True,
            type_=Union[
                CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None
            ],
            **kwargs,
        )

    async def put_api_internal_pool_provider_configurations_id(
        self,
        id: str,
        request_body: Union[
            CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None
        ],
        **kwargs: Any,
    ) -> None:
        return await self.client.request(
            method="PUT", url=f"/api/internal/pool-provider/configurations/{id}", request_body=request_body, **kwargs
        )

    async def delete_api_internal_pool_provider_configurations_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/internal/pool-provider/configurations/{id}", **kwargs
        )

    async def get_api_internal_object_storage_buckets_id(self, id: str, **kwargs: Any) -> ObjectStorageBucketTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/object-storage-buckets/{id}",
            parse_json=True,
            type_=ObjectStorageBucketTransport,
            **kwargs,
        )

    async def put_api_internal_object_storage_buckets_id(
        self, id: str, request_body: ObjectStorageBucketTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="PUT", url=f"/api/internal/object-storage-buckets/{id}", request_body=request_body, **kwargs
        )

    async def delete_api_internal_object_storage_buckets_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/object-storage-buckets/{id}", **kwargs)

    async def post_api_internal_v2_clone(
        self, request_body: CloneRequestTransport, **kwargs: Any
    ) -> CloneResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/v2/clone",
            request_body=request_body,
            parse_json=True,
            type_=CloneResultTransport,
            **kwargs,
        )

    async def post_api_internal_teams_team_id_erase(
        self, team_id: str, **kwargs: Any
    ) -> List[Optional[EraserLogMessageTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/teams/{team_id}/erase",
            parse_json=True,
            type_=List[Optional[EraserLogMessageTransport]],
            **kwargs,
        )

    async def post_api_internal_streaming_stop_subscription_execution(
        self, request_body: StreamingSubscriptionTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/streaming/stop_subscription_execution",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_streaming_service_started(
        self, type_: Optional["StreamingType"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        return await self.client.request(
            method="POST", url=f"/api/internal/streaming/service_started", params=params, **kwargs
        )

    async def post_api_internal_streaming_logs(
        self, request_body: StreamingExecutionLogTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/streaming/logs", request_body=request_body, **kwargs
        )

    async def get_api_internal_service_permissions(self, **kwargs: Any) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_service_permissions(
        self, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/service-permissions/",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_secured_v1_migration_pools_pool_id_data_models(
        self, pool_id: str, request_body: DataModelTransport, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_internal_secured_v1_migration_pools_pool_id_data_models_data_model_id_tables(
        self, pool_id: str, data_model_id: str, request_body: List[Optional[DataModelTableTransport]], **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models/{data_model_id}/tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def post_api_internal_secured_v1_migration_pools_pool_id_data_models_data_model_id_name_mapping(
        self, pool_id: str, data_model_id: str, request_body: CpmNameMappings, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models/{data_model_id}/name-mapping",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_secured_v1_migration_pools_pool_id_data_models_data_model_id_foreign_keys(
        self, pool_id: str, data_model_id: str, request_body: DataModelForeignKeyTransport, **kwargs: Any
    ) -> DataModelForeignKeyTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models/{data_model_id}/foreign-keys",
            request_body=request_body,
            parse_json=True,
            type_=DataModelForeignKeyTransport,
            **kwargs,
        )

    async def post_api_internal_secured_v1_migration_pools_pool_id_data_models_data_model_id_calendar_custom(
        self, pool_id: str, data_model_id: str, request_body: DataModelCustomCalendarTransport, **kwargs: Any
    ) -> DataModelCustomCalendarTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/secured/v1/migration/pools/{pool_id}/data-models/{data_model_id}/calendar/custom",
            request_body=request_body,
            parse_json=True,
            type_=DataModelCustomCalendarTransport,
            **kwargs,
        )

    async def post_api_internal_sanitize_sanitize_accelerator(
        self, request_body: SanitizeComputeNodesRequestTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/sanitize/sanitize-accelerator", request_body=request_body, **kwargs
        )

    async def get_api_internal_pools_pool_id_data_models_data_model_id_tables(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/tables",
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def post_api_internal_pools_pool_id_data_models_data_model_id_tables(
        self, pool_id: str, data_model_id: str, request_body: List[Optional[DataModelTableTransport]], **kwargs: Any
    ) -> List[Optional[DataModelTableTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/tables",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[DataModelTableTransport]],
            **kwargs,
        )

    async def get_api_internal_pools_pool_id_data_models_data_model_id_foreign_keys(
        self, pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelForeignKeyTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/foreign-keys",
            parse_json=True,
            type_=List[Optional[DataModelForeignKeyTransport]],
            **kwargs,
        )

    async def post_api_internal_pools_pool_id_data_models_data_model_id_foreign_keys(
        self, pool_id: str, data_model_id: str, request_body: DataModelForeignKeyTransport, **kwargs: Any
    ) -> DataModelForeignKeyTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/foreign-keys",
            request_body=request_body,
            parse_json=True,
            type_=DataModelForeignKeyTransport,
            **kwargs,
        )

    async def post_api_internal_pools_import(
        self, request_body: DataPoolImportRequest, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pools/import",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def post_api_internal_pool_move_target_domain(
        self, target_domain: str, request_body: DataPoolImportRequest, **kwargs: Any
    ) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pool/move/{target_domain}",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def post_api_internal_pool_provider_query(
        self,
        request_body: Union[
            PoolProviderCopyTableQuery, PoolProviderCreateTableQuery, PoolProviderSelectTableQuery, None
        ],
        **kwargs: Any,
    ) -> PoolProviderQueryResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pool-provider/query",
            request_body=request_body,
            parse_json=True,
            type_=PoolProviderQueryResultTransport,
            **kwargs,
        )

    async def post_api_internal_pool_provider_credentials(
        self, request_body: PoolProviderCredentialsTransport, **kwargs: Any
    ) -> PoolProviderCredentialsTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pool-provider/credentials",
            request_body=request_body,
            parse_json=True,
            type_=PoolProviderCredentialsTransport,
            **kwargs,
        )

    async def get_api_internal_pool_provider_configurations(
        self, name_pattern: Optional["str"] = None, **kwargs: Any
    ) -> List[
        Optional[
            Union[CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None]
        ]
    ]:
        params: Dict[str, Any] = {}
        if name_pattern is not None:
            if isinstance(name_pattern, PythonCoreBaseModel):
                params.update(name_pattern.json_dict(by_alias=True))
            elif isinstance(name_pattern, dict):
                params.update(name_pattern)
            else:
                params["namePattern"] = name_pattern
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/configurations",
            params=params,
            parse_json=True,
            type_=List[
                Optional[
                    Union[
                        CustomConfigurationTransport,
                        DatabaseConfigurationTransport,
                        VerticaConfigurationTransport,
                        None,
                    ]
                ]
            ],
            **kwargs,
        )

    async def post_api_internal_pool_provider_configurations(
        self,
        request_body: Union[
            CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None
        ],
        **kwargs: Any,
    ) -> Union[CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pool-provider/configurations",
            request_body=request_body,
            parse_json=True,
            type_=Union[
                CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None
            ],
            **kwargs,
        )

    async def get_api_internal_pool_provider_assignments(
        self, **kwargs: Any
    ) -> List[Optional[PoolProviderAssignmentTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/assignments",
            parse_json=True,
            type_=List[Optional[PoolProviderAssignmentTransport]],
            **kwargs,
        )

    async def post_api_internal_pool_provider_assignments(
        self, request_body: List[Optional[PoolProviderAssignmentTransport]], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/pool-provider/assignments", request_body=request_body, **kwargs
        )

    async def post_api_internal_pool_provider_tenants(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/internal/pool-provider-tenants", **kwargs)

    async def post_api_internal_pool_provider_tenants_reset(self, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/internal/pool-provider-tenants/reset", **kwargs)

    async def post_api_internal_pool_import(self, request_body: str, **kwargs: Any) -> DataPoolImportReportTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/pool-import",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolImportReportTransport,
            **kwargs,
        )

    async def get_api_internal_object_storage_buckets(
        self, name_pattern: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ObjectStorageBucketTransport]]:
        params: Dict[str, Any] = {}
        if name_pattern is not None:
            if isinstance(name_pattern, PythonCoreBaseModel):
                params.update(name_pattern.json_dict(by_alias=True))
            elif isinstance(name_pattern, dict):
                params.update(name_pattern)
            else:
                params["namePattern"] = name_pattern
        return await self.client.request(
            method="GET",
            url=f"/api/internal/object-storage-buckets",
            params=params,
            parse_json=True,
            type_=List[Optional[ObjectStorageBucketTransport]],
            **kwargs,
        )

    async def post_api_internal_object_storage_buckets(
        self, request_body: ObjectStorageBucketTransport, **kwargs: Any
    ) -> ObjectStorageBucketTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/object-storage-buckets",
            request_body=request_body,
            parse_json=True,
            type_=ObjectStorageBucketTransport,
            **kwargs,
        )

    async def get_api_internal_object_storage_buckets_assignments(
        self, **kwargs: Any
    ) -> ObjectStorageBucketAssignmentTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/object-storage-buckets/assignments",
            parse_json=True,
            type_=ObjectStorageBucketAssignmentTransport,
            **kwargs,
        )

    async def post_api_internal_object_storage_buckets_assignments(
        self, request_body: ObjectStorageBucketAssignmentTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/object-storage-buckets/assignments", request_body=request_body, **kwargs
        )

    async def post_api_internal_info_version(
        self, request_body: ComputeVersionRequest, **kwargs: Any
    ) -> AcceleratorVersion:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/info/version",
            request_body=request_body,
            parse_json=True,
            type_=AcceleratorVersion,
            **kwargs,
        )

    async def post_api_internal_datamodel_data_model_id_executionitem_execution_item_id(
        self, data_model_id: str, execution_item_id: str, request_body: DataModelLoadStatusUpdateMessage, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/datamodel/{data_model_id}/executionitem/{execution_item_id}",
            request_body=request_body,
            **kwargs,
        )

    async def get_api_internal_data_push_pool_id_jobs(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataPushJobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push/{pool_id}/jobs",
            parse_json=True,
            type_=List[Optional[DataPushJobTransport]],
            **kwargs,
        )

    async def post_api_internal_data_push_pool_id_jobs(
        self, pool_id: str, request_body: DataPushJobTransport, **kwargs: Any
    ) -> DataPushJobTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push/{pool_id}/jobs",
            request_body=request_body,
            parse_json=True,
            type_=DataPushJobTransport,
            **kwargs,
        )

    async def get_api_internal_data_push_pool_id_jobs_id(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> DataPushJobTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push/{pool_id}/jobs/{id}",
            parse_json=True,
            type_=DataPushJobTransport,
            **kwargs,
        )

    async def post_api_internal_data_push_pool_id_jobs_id(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/internal/data-push/{pool_id}/jobs/{id}", **kwargs)

    async def delete_api_internal_data_push_pool_id_jobs_id(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/data-push/{pool_id}/jobs/{id}", **kwargs)

    async def post_api_internal_data_push_pool_id_jobs_id_chunks_upserted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push/{pool_id}/jobs/{id}/chunks/upserted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_data_push_pool_id_jobs_id_chunks_deleted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push/{pool_id}/jobs/{id}/chunks/deleted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_data_push_pool_id_jobs_id_cancel(self, pool_id: str, id: str, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/data-push/{pool_id}/jobs/{id}/cancel", **kwargs
        )

    async def get_api_internal_data_push_for_system_pool_id_jobs(
        self, pool_id: str, **kwargs: Any
    ) -> List[Optional[DataPushJobTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs",
            parse_json=True,
            type_=List[Optional[DataPushJobTransport]],
            **kwargs,
        )

    async def post_api_internal_data_push_for_system_pool_id_jobs(
        self, pool_id: str, request_body: DataPushJobTransport, **kwargs: Any
    ) -> DataPushJobTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs",
            request_body=request_body,
            parse_json=True,
            type_=DataPushJobTransport,
            **kwargs,
        )

    async def get_api_internal_data_push_for_system_pool_id_jobs_id(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> DataPushJobTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}",
            parse_json=True,
            type_=DataPushJobTransport,
            **kwargs,
        )

    async def post_api_internal_data_push_for_system_pool_id_jobs_id(
        self,
        pool_id: str,
        id: str,
        duplicate_removal_options: Optional["DuplicateRemovalOptions"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if duplicate_removal_options is not None:
            if isinstance(duplicate_removal_options, PythonCoreBaseModel):
                params.update(duplicate_removal_options.json_dict(by_alias=True))
            elif isinstance(duplicate_removal_options, dict):
                params.update(duplicate_removal_options)
            else:
                params["duplicateRemovalOptions"] = duplicate_removal_options
        return await self.client.request(
            method="POST", url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}", params=params, **kwargs
        )

    async def delete_api_internal_data_push_for_system_pool_id_jobs_id(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}", **kwargs
        )

    async def post_api_internal_data_push_for_system_pool_id_jobs_id_chunks_upserted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}/chunks/upserted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_data_push_for_system_pool_id_jobs_id_chunks_deleted(
        self, pool_id: str, id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}/chunks/deleted",
            request_body=request_body,
            **kwargs,
        )

    async def post_api_internal_data_push_for_system_pool_id_jobs_id_cancel(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}/cancel", **kwargs
        )

    async def get_api_internal_data_pools(
        self, having_data_models: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[DataPoolTransport]]:
        params: Dict[str, Any] = {}
        if having_data_models is not None:
            if isinstance(having_data_models, PythonCoreBaseModel):
                params.update(having_data_models.json_dict(by_alias=True))
            elif isinstance(having_data_models, dict):
                params.update(having_data_models)
            else:
                params["havingDataModels"] = having_data_models
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools",
            params=params,
            parse_json=True,
            type_=List[Optional[DataPoolTransport]],
            **kwargs,
        )

    async def post_api_internal_data_pools(self, request_body: DataPoolTransport, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools",
            request_body=request_body,
            parse_json=True,
            type_=DataPoolTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_id_api_internal_data_pools_pool_id_data_sources_data_source_id_resolve_pool_parameters(
        self, pool_id: str, data_source_id: str, **kwargs: Any
    ) -> FilterVariableValueMap:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/id/api/internal/data-pools/{pool_id}/data-sources/{data_source_id}/resolve-pool-parameters",
            parse_json=True,
            type_=FilterVariableValueMap,
            **kwargs,
        )

    async def post_api_internal_data_pools_id_api_internal_data_pools_pool_id_data_sources_data_source_id_resolve_pool_parameters(
        self, pool_id: str, data_source_id: str, request_body: ResolveParameterRequestBody, **kwargs: Any
    ) -> FilterVariableValueMap:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/id/api/internal/data-pools/{pool_id}/data-sources/{data_source_id}/resolve-pool-parameters",
            request_body=request_body,
            parse_json=True,
            type_=FilterVariableValueMap,
            **kwargs,
        )

    async def post_api_internal_data_pools_pool_id_data_sources_data_source_id_resolve_dynamic_parameters(
        self,
        pool_id: str,
        data_source_id: str,
        request_body: List[Optional[DynamicDataPoolParameterTransport]],
        table_name: Optional["str"] = None,
        **kwargs: Any,
    ) -> FilterVariableValueMap:
        params: Dict[str, Any] = {}
        if table_name is not None:
            if isinstance(table_name, PythonCoreBaseModel):
                params.update(table_name.json_dict(by_alias=True))
            elif isinstance(table_name, dict):
                params.update(table_name)
            else:
                params["tableName"] = table_name
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/{pool_id}/data-sources/{data_source_id}/resolve-dynamic-parameters",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=FilterVariableValueMap,
            **kwargs,
        )

    async def post_api_internal_data_pools_pool_id_data_models(
        self, pool_id: str, request_body: DataModelTransport, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/{pool_id}/data-models",
            request_body=request_body,
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_internal_data_pools_data_pool_id_data_source_data_source_id_data_query(
        self,
        data_pool_id: str,
        data_source_id: str,
        request_body: str,
        fetch_result_rows: Optional["int"] = None,
        **kwargs: Any,
    ) -> DataQueryTransport:
        params: Dict[str, Any] = {}
        if fetch_result_rows is not None:
            if isinstance(fetch_result_rows, PythonCoreBaseModel):
                params.update(fetch_result_rows.json_dict(by_alias=True))
            elif isinstance(fetch_result_rows, dict):
                params.update(fetch_result_rows)
            else:
                params["fetchResultRows"] = fetch_result_rows
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/{data_pool_id}/data-source/{data_source_id}/data-query",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=DataQueryTransport,
            **kwargs,
        )

    async def post_api_internal_data_pools_data_pool_id_data_source_data_source_id_data_query_transformation(
        self, data_pool_id: str, data_source_id: str, request_body: TransformationRequestTransport, **kwargs: Any
    ) -> DataQueryTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/{data_pool_id}/data-source/{data_source_id}/data-query/transformation",
            request_body=request_body,
            parse_json=True,
            type_=DataQueryTransport,
            **kwargs,
        )

    async def post_api_internal_data_pools_data_pool_id_data_query(
        self, data_pool_id: str, request_body: str, **kwargs: Any
    ) -> DataQueryTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/{data_pool_id}/data-query",
            request_body=request_body,
            parse_json=True,
            type_=DataQueryTransport,
            **kwargs,
        )

    async def post_api_internal_data_pools_data_models_data_model_id_send_email_data_model_email_type(
        self, data_model_id: str, data_model_email_type: DataModelEmailType, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/send-email/{data_model_email_type}",
            **kwargs,
        )

    async def post_api_internal_data_pools_data_models_data_model_id_reload(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/reload",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def post_api_internal_data_pools_data_models_data_model_id_full_reload(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/full-reload",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_internal_data_pool_permission_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pool-permission/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_data_pool_permission_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-pool-permission/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_api_internal_data_model_permission_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-model-permission/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_data_model_permission_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/data-model-permission/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_compute_schemas(
        self, request_body: LiveDataModelsRequestTransport, **kwargs: Any
    ) -> LiveDataModelsResponseTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/schemas",
            request_body=request_body,
            parse_json=True,
            type_=LiveDataModelsResponseTransport,
            **kwargs,
        )

    async def post_api_internal_compute_multi_query(
        self, request_body: PostMultiQueryTransport, **kwargs: Any
    ) -> PqlMultiResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/multi-query",
            request_body=request_body,
            parse_json=True,
            type_=PqlMultiResultTransport,
            **kwargs,
        )

    async def post_api_internal_compute_multi_query_chunked(
        self, request_body: PostMultiQueryChunkedTransport, **kwargs: Any
    ) -> PqlMultiResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/multi-query-chunked",
            request_body=request_body,
            parse_json=True,
            type_=PqlMultiResultTransport,
            **kwargs,
        )

    async def post_api_internal_compute_export_jobs_query(
        self, request_body: DataExportRequest, **kwargs: Any
    ) -> DataExportStatusResponse:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/export_jobs/query",
            request_body=request_body,
            parse_json=True,
            type_=DataExportStatusResponse,
            **kwargs,
        )

    async def post_api_internal_compute_expand_multi_query_batch(
        self, request_body: PostBatchQueryTransport, **kwargs: Any
    ) -> PqlBatchExpansionResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/expand/multi-query-batch",
            request_body=request_body,
            parse_json=True,
            type_=PqlBatchExpansionResultTransport,
            **kwargs,
        )

    async def post_api_internal_compute_batch_query(
        self, request_body: PostBatchQueryTransport, **kwargs: Any
    ) -> QueryBatchResult:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/compute/batch-query",
            request_body=request_body,
            parse_json=True,
            type_=QueryBatchResult,
            **kwargs,
        )

    async def post_api_internal_clone(
        self, request_body: IntegrationCloneInternalTransport, **kwargs: Any
    ) -> IntegrationCloneResultInternalTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/clone",
            request_body=request_body,
            parse_json=True,
            type_=IntegrationCloneResultInternalTransport,
            **kwargs,
        )

    async def post_api_internal_caching_cluster_suspend_distributed_caching(self, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/caching/cluster/suspendDistributedCaching", **kwargs
        )

    async def get_api_internal_id_tables_with_columns(self, id: str, **kwargs: Any) -> List[Optional[PoolTable]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/{id}/tables-with-columns",
            parse_json=True,
            type_=List[Optional[PoolTable]],
            **kwargs,
        )

    async def get_api_internal_data_model_id_load_history(
        self, data_model_id: str, limit: Optional["int"] = None, **kwargs: Any
    ) -> List[Optional[DataLoadHistoryTransport]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/internal/{data_model_id}/load-history",
            params=params,
            parse_json=True,
            type_=List[Optional[DataLoadHistoryTransport]],
            **kwargs,
        )

    async def get_api_internal_data_model_id_load_history_last_successful(
        self, data_model_id: str, **kwargs: Any
    ) -> DataLoadHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/{data_model_id}/load-history/last-successful",
            parse_json=True,
            type_=DataLoadHistoryTransport,
            **kwargs,
        )

    async def get_api_internal_transformation_scheduler_transformations_id(
        self, id: str, **kwargs: Any
    ) -> TransformationExecutionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/transformation-scheduler/transformations/{id}",
            parse_json=True,
            type_=TransformationExecutionTransport,
            **kwargs,
        )

    async def get_api_internal_transformation_scheduler_transformations_item_item_id(
        self, item_id: str, **kwargs: Any
    ) -> TransformationExecutionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/transformation-scheduler/transformations/item/{item_id}",
            parse_json=True,
            type_=TransformationExecutionTransport,
            **kwargs,
        )

    async def get_api_internal_tasks_task_instance_id_table_configuration_from_extraction(
        self, task_instance_id: str, job_id: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if job_id is not None:
            if isinstance(job_id, PythonCoreBaseModel):
                params.update(job_id.json_dict(by_alias=True))
            elif isinstance(job_id, dict):
                params.update(job_id)
            else:
                params["jobId"] = job_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/tasks/{task_instance_id}/tableConfigurationFromExtraction",
            params=params,
            **kwargs,
        )

    async def get_api_internal_tags(self, **kwargs: Any) -> List[Optional[Tag]]:
        return await self.client.request(
            method="GET", url=f"/api/internal/tags", parse_json=True, type_=List[Optional[Tag]], **kwargs
        )

    async def get_api_internal_service_permissions_overview(self, **kwargs: Any) -> PermissionsOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/overview",
            parse_json=True,
            type_=PermissionsOverviewTransport,
            **kwargs,
        )

    async def get_api_internal_service_permissions_model(self, **kwargs: Any) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_service_permissions_all(
        self, subject_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        params: Dict[str, Any] = {}
        if subject_id is not None:
            if isinstance(subject_id, PythonCoreBaseModel):
                params.update(subject_id.json_dict(by_alias=True))
            elif isinstance(subject_id, dict):
                params.update(subject_id)
            else:
                params["subjectId"] = subject_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/all",
            params=params,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_acl(
        self, **kwargs: Any
    ) -> List[Optional[AccessControlListTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/acl",
            parse_json=True,
            type_=List[Optional[AccessControlListTransport]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_evaluated_current_user(self, **kwargs: Any) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions-evaluated/current-user",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_evaluated_current_user_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions-evaluated/current-user/{team_domain}",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_internal_search(self, text: Optional["str"] = None, **kwargs: Any) -> List[Optional[SearchItem]]:
        params: Dict[str, Any] = {}
        if text is not None:
            if isinstance(text, PythonCoreBaseModel):
                params.update(text.json_dict(by_alias=True))
            elif isinstance(text, dict):
                params.update(text)
            else:
                params["text"] = text
        return await self.client.request(
            method="GET",
            url=f"/api/internal/search",
            params=params,
            parse_json=True,
            type_=List[Optional[SearchItem]],
            **kwargs,
        )

    async def get_api_internal_salt_salt_id(self, salt_id: str, **kwargs: Any) -> AnonymizationSaltTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/salt/{salt_id}",
            parse_json=True,
            type_=AnonymizationSaltTransport,
            **kwargs,
        )

    async def get_api_internal_process_configuration(self, **kwargs: Any) -> ProcessConfigurationTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/process-configuration",
            parse_json=True,
            type_=ProcessConfigurationTransport,
            **kwargs,
        )

    async def get_api_internal_pools_pool_id_datasources_replication_scopes(
        self,
        pool_id: str,
        exclude_unconfigured: Optional["bool"] = None,
        distinct: Optional["bool"] = None,
        type_: Optional["str"] = None,
        limit: Optional["int"] = None,
        **kwargs: Any,
    ) -> List[Optional[DataSourceTransport]]:
        params: Dict[str, Any] = {}
        if exclude_unconfigured is not None:
            if isinstance(exclude_unconfigured, PythonCoreBaseModel):
                params.update(exclude_unconfigured.json_dict(by_alias=True))
            elif isinstance(exclude_unconfigured, dict):
                params.update(exclude_unconfigured)
            else:
                params["excludeUnconfigured"] = exclude_unconfigured
        if distinct is not None:
            if isinstance(distinct, PythonCoreBaseModel):
                params.update(distinct.json_dict(by_alias=True))
            elif isinstance(distinct, dict):
                params.update(distinct)
            else:
                params["distinct"] = distinct
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pools/{pool_id}/datasources/replication-scopes",
            params=params,
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_internal_pools_import_version(self, **kwargs: Any) -> int:
        return await self.client.request(
            method="GET", url=f"/api/internal/pools/import/version", parse_json=True, type_=int, **kwargs
        )

    async def get_api_internal_pool_pool_id_move_target_domain_license(
        self, pool_id: str, target_domain: str, **kwargs: Any
    ) -> DataModelCreationRestrictionWithSelectionV1:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool/{pool_id}/move/{target_domain}/license",
            parse_json=True,
            type_=DataModelCreationRestrictionWithSelectionV1,
            **kwargs,
        )

    async def get_api_internal_pool_pool_id_move_target_domain_license_v2(
        self, pool_id: str, target_domain: str, **kwargs: Any
    ) -> DataModelCreationRestrictionWithSelection:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool/{pool_id}/move/{target_domain}/license/v2",
            parse_json=True,
            type_=DataModelCreationRestrictionWithSelection,
            **kwargs,
        )

    async def get_api_internal_pool_move_target_domain_version(self, target_domain: str, **kwargs: Any) -> int:
        return await self.client.request(
            method="GET", url=f"/api/internal/pool/move/{target_domain}/version", parse_json=True, type_=int, **kwargs
        )

    async def get_api_internal_pool_provider_datapool_data_pool_id(
        self, data_pool_id: str, **kwargs: Any
    ) -> PoolProviderDetailTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/datapool/{data_pool_id}",
            parse_json=True,
            type_=PoolProviderDetailTransport,
            **kwargs,
        )

    async def get_api_internal_pool_provider_current_team(self, **kwargs: Any) -> PoolProviderDetailTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/current-team",
            parse_json=True,
            type_=PoolProviderDetailTransport,
            **kwargs,
        )

    async def get_api_internal_pool_provider_current_team_credentials(
        self, **kwargs: Any
    ) -> PoolProviderCredentialsTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/current-team/credentials",
            parse_json=True,
            type_=PoolProviderCredentialsTransport,
            **kwargs,
        )

    async def get_api_internal_pool_provider_configurations_current_team(
        self, **kwargs: Any
    ) -> Union[CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/pool-provider/configurations/current-team",
            parse_json=True,
            type_=Union[
                CustomConfigurationTransport, DatabaseConfigurationTransport, VerticaConfigurationTransport, None
            ],
            **kwargs,
        )

    async def get_api_internal_permission_team_domain(self, team_domain: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/internal/permission/{team_domain}", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_internal_parameters(
        self, pool_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PoolVariableTransport]]:
        params: Dict[str, Any] = {}
        if pool_id is not None:
            if isinstance(pool_id, PythonCoreBaseModel):
                params.update(pool_id.json_dict(by_alias=True))
            elif isinstance(pool_id, dict):
                params.update(pool_id)
            else:
                params["poolId"] = pool_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/parameters",
            params=params,
            parse_json=True,
            type_=List[Optional[PoolVariableTransport]],
            **kwargs,
        )

    async def get_api_internal_object_storage_buckets_tenant_bucket_details(
        self, **kwargs: Any
    ) -> ObjectStorageBucketTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/object-storage-buckets/tenant-bucket-details",
            parse_json=True,
            type_=ObjectStorageBucketTransport,
            **kwargs,
        )

    async def get_api_internal_logs_main(self, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/api/internal/logs/main", **kwargs)

    async def get_api_internal_logs_engine(self, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/api/internal/logs/engine", **kwargs)

    async def get_api_internal_job_scheduler_data_push_jobs_id(self, id: str, **kwargs: Any) -> DataPushJobTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/job-scheduler/data-push-jobs/{id}",
            parse_json=True,
            type_=DataPushJobTransport,
            **kwargs,
        )

    async def get_api_internal_hdfs_configuration(self, **kwargs: Any) -> KerberosConfiguration:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/hdfs-configuration",
            parse_json=True,
            type_=KerberosConfiguration,
            **kwargs,
        )

    async def get_api_internal_datasources(
        self, data_source_ids: Optional["List[Optional[str]]"] = None, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        params: Dict[str, Any] = {}
        if data_source_ids is not None:
            if isinstance(data_source_ids, PythonCoreBaseModel):
                params.update(data_source_ids.json_dict(by_alias=True))
            elif isinstance(data_source_ids, dict):
                params.update(data_source_ids)
            else:
                params["dataSourceIds"] = data_source_ids
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources",
            params=params,
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_internal_datasources_data_source_id(
        self, data_source_id: str, **kwargs: Any
    ) -> DataSourceTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources/{data_source_id}",
            parse_json=True,
            type_=DataSourceTransport,
            **kwargs,
        )

    async def get_api_internal_datasources_data_source_id_configuration(
        self, data_source_id: str, **kwargs: Any
    ) -> Union[
        AmazonS3ConnectionConfiguration,
        AribaConnectionConfiguration,
        AribaConnectionConfigurationV2,
        AutomationAnywhereConnectionConfiguration,
        AzureServiceBusConnectionConfiguration,
        BiPublisherConnectionConfiguration,
        CelonisActionEngineConnectionConfiguration,
        CoupaConnectionConfiguration,
        CustomConnectionConfiguration,
        CustomExtractorConnectionConfiguration,
        DatabaseConnectionConfiguration,
        DemoSapConnectionConfiguration,
        DemoServiceNowConnectionConfiguration,
        EventHubConnectionConfiguration,
        FieldglassConnectionConfiguration,
        GoogleSheetsConnectionConfiguration,
        HappyFoxConnectionConfiguration,
        ImportedConnectionConfiguration,
        JiraConnectionConfiguration,
        KafkaConnectionConfiguration,
        MicrosoftDynamics365ConnectionConfiguration,
        OracleCloudConnectionConfiguration,
        PardotConnectionConfiguration,
        PythonConnectorConnectionConfiguration,
        RossumConnectionConfiguration,
        SalesforceConnectionConfiguration,
        SapConnectionConfiguration,
        SapMarketingCloudConnectionConfiguration,
        SapSnsConnectionConfiguration,
        ServiceNowConnectionConfiguration,
        SnowflakeRestConnectionConfiguration,
        SuccessFactorsConnectionConfiguration,
        UiPathConnectionConfiguration,
        WorkdayConnectionConfiguration,
        ZendeskConnectionConfiguration,
        None,
    ]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources/{data_source_id}/configuration",
            parse_json=True,
            type_=Union[
                AmazonS3ConnectionConfiguration,
                AribaConnectionConfiguration,
                AribaConnectionConfigurationV2,
                AutomationAnywhereConnectionConfiguration,
                AzureServiceBusConnectionConfiguration,
                BiPublisherConnectionConfiguration,
                CelonisActionEngineConnectionConfiguration,
                CoupaConnectionConfiguration,
                CustomConnectionConfiguration,
                CustomExtractorConnectionConfiguration,
                DatabaseConnectionConfiguration,
                DemoSapConnectionConfiguration,
                DemoServiceNowConnectionConfiguration,
                EventHubConnectionConfiguration,
                FieldglassConnectionConfiguration,
                GoogleSheetsConnectionConfiguration,
                HappyFoxConnectionConfiguration,
                ImportedConnectionConfiguration,
                JiraConnectionConfiguration,
                KafkaConnectionConfiguration,
                MicrosoftDynamics365ConnectionConfiguration,
                OracleCloudConnectionConfiguration,
                PardotConnectionConfiguration,
                PythonConnectorConnectionConfiguration,
                RossumConnectionConfiguration,
                SalesforceConnectionConfiguration,
                SapConnectionConfiguration,
                SapMarketingCloudConnectionConfiguration,
                SapSnsConnectionConfiguration,
                ServiceNowConnectionConfiguration,
                SnowflakeRestConnectionConfiguration,
                SuccessFactorsConnectionConfiguration,
                UiPathConnectionConfiguration,
                WorkdayConnectionConfiguration,
                ZendeskConnectionConfiguration,
                None,
            ],
            **kwargs,
        )

    async def get_api_internal_datasources_uplinks_id(
        self, id: str, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources/uplinks/{id}",
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_internal_datasources_pools_id(
        self, id: str, **kwargs: Any
    ) -> List[Optional[DataSourceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources/pools/{id}",
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_internal_datasources_all(self, **kwargs: Any) -> List[Optional[DataSourceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/datasources/all",
            parse_json=True,
            type_=List[Optional[DataSourceTransport]],
            **kwargs,
        )

    async def get_api_internal_data_push_pool_id_jobs_id_chunks(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[DataPushChunkTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push/{pool_id}/jobs/{id}/chunks",
            parse_json=True,
            type_=List[Optional[DataPushChunkTransport]],
            **kwargs,
        )

    async def get_api_internal_data_push_for_system_pool_id_jobs_id_chunks(
        self, pool_id: str, id: str, **kwargs: Any
    ) -> List[Optional[DataPushChunkTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-push-for-system/{pool_id}/jobs/{id}/chunks",
            parse_json=True,
            type_=List[Optional[DataPushChunkTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_id(self, id: str, **kwargs: Any) -> DataPoolTransport:
        return await self.client.request(
            method="GET", url=f"/api/internal/data-pools/{id}", parse_json=True, type_=DataPoolTransport, **kwargs
        )

    async def get_api_internal_data_pools_id_tables_table_name(
        self, id: str, table_name: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PoolColumn]]:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{id}/tables/{table_name}",
            params=params,
            parse_json=True,
            type_=List[Optional[PoolColumn]],
            **kwargs,
        )

    async def get_api_internal_data_pools_id_tables_table_name_status(
        self, id: str, table_name: str, data_source_id: Optional["str"] = None, **kwargs: Any
    ) -> DataPoolTableStatus:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{id}/tables/{table_name}/status",
            params=params,
            parse_json=True,
            type_=DataPoolTableStatus,
            **kwargs,
        )

    async def get_api_internal_data_pools_id_permissions(self, id: str, **kwargs: Any) -> DataPoolPermissionSummary:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{id}/permissions",
            parse_json=True,
            type_=DataPoolPermissionSummary,
            **kwargs,
        )

    async def get_api_internal_data_pools_id_data_models(
        self, id: str, **kwargs: Any
    ) -> List[Optional[DataModelTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{id}/data-models",
            parse_json=True,
            type_=List[Optional[DataModelTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_data_pool_id_tables_table_name_preview(
        self,
        data_pool_id: str,
        table_name: str,
        data_source_id: Optional["str"] = None,
        limit: Optional["int"] = None,
        **kwargs: Any,
    ) -> PoolTablePreview:
        params: Dict[str, Any] = {}
        if data_source_id is not None:
            if isinstance(data_source_id, PythonCoreBaseModel):
                params.update(data_source_id.json_dict(by_alias=True))
            elif isinstance(data_source_id, dict):
                params.update(data_source_id)
            else:
                params["dataSourceId"] = data_source_id
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{data_pool_id}/tables/{table_name}/preview",
            params=params,
            parse_json=True,
            type_=PoolTablePreview,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_pool_id_data_source_data_source_id_data_query_id(
        self, data_pool_id: str, data_source_id: str, id: str, **kwargs: Any
    ) -> DataQueryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{data_pool_id}/data-source/{data_source_id}/data-query/{id}",
            parse_json=True,
            type_=DataQueryTransport,
            **kwargs,
        )

    async def delete_api_internal_data_pools_data_pool_id_data_source_data_source_id_data_query_id(
        self, data_pool_id: str, data_source_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/internal/data-pools/{data_pool_id}/data-source/{data_source_id}/data-query/{id}",
            **kwargs,
        )

    async def get_api_internal_data_pools_data_pool_id_data_query_id(
        self, data_pool_id: str, id: str, **kwargs: Any
    ) -> DataQueryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{data_pool_id}/data-query/{id}",
            parse_json=True,
            type_=DataQueryTransport,
            **kwargs,
        )

    async def delete_api_internal_data_pools_data_pool_id_data_query_id(
        self, data_pool_id: str, id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/internal/data-pools/{data_pool_id}/data-query/{id}", **kwargs
        )

    async def get_api_internal_data_pools_data_pool_id_data_models_data_model_id_signal_links(
        self, data_pool_id: str, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataModelSignalLinkTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/{data_pool_id}/data-models/{data_model_id}/signal-links",
            parse_json=True,
            type_=List[Optional[DataModelSignalLinkTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_type(self, **kwargs: Any) -> PoolProviderType:
        return await self.client.request(
            method="GET", url=f"/api/internal/data-pools/type", parse_json=True, type_=PoolProviderType, **kwargs
        )

    async def get_api_internal_data_pools_monitoring_target_pool(self, **kwargs: Any) -> str:
        return await self.client.request(
            method="GET", url=f"/api/internal/data-pools/monitoring-target-pool", parse_json=True, type_=str, **kwargs
        )

    async def get_api_internal_data_pools_installations_id(
        self, id: str, **kwargs: Any
    ) -> List[Optional[DataPoolSummary]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/installations/{id}",
            parse_json=True,
            type_=List[Optional[DataPoolSummary]],
            **kwargs,
        )

    async def get_api_internal_data_pools_filtered_by_permissions(
        self, permissions: Optional["List[Optional[str]]"] = None, **kwargs: Any
    ) -> List[Optional[DataPoolTransport]]:
        params: Dict[str, Any] = {}
        if permissions is not None:
            if isinstance(permissions, PythonCoreBaseModel):
                params.update(permissions.json_dict(by_alias=True))
            elif isinstance(permissions, dict):
                params.update(permissions)
            else:
                params["permissions"] = permissions
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/filtered-by-permissions",
            params=params,
            parse_json=True,
            type_=List[Optional[DataPoolTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models(self, **kwargs: Any) -> List[Optional[DataModelTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models",
            parse_json=True,
            type_=List[Optional[DataModelTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_v2_load_info_sync(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelLoadSyncTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/v2/load-info-sync",
            parse_json=True,
            type_=DataModelLoadSyncTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_name_mappings(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelNameMappingTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/name-mappings",
            parse_json=True,
            type_=DataModelNameMappingTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_load_info_sync(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelLoadSyncTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/load-info-sync",
            parse_json=True,
            type_=DataModelLoadSyncTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_graph_positioning(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelGraphPositioningTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/graph-positioning",
            parse_json=True,
            type_=DataModelGraphPositioningTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_for_load(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/for-load",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_factory_calendar(
        self, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DataLoadFactoryCalendarTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/factory-calendar",
            parse_json=True,
            type_=List[Optional[DataLoadFactoryCalendarTransport]],
            **kwargs,
        )

    async def get_api_internal_data_pools_data_models_data_model_id_configuration(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pools/data-models/{data_model_id}/configuration",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_internal_data_pool_versions_data_pool_id(
        self, data_pool_id: str, **kwargs: Any
    ) -> DataPoolVersionInfo:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pool-versions/{data_pool_id}",
            parse_json=True,
            type_=DataPoolVersionInfo,
            **kwargs,
        )

    async def get_api_internal_data_pool_permission_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-pool-permission/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_data_model_permission_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/data-model-permission/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_compute_data_model_id_version(self, data_model_id: str, **kwargs: Any) -> int:
        return await self.client.request(
            method="GET", url=f"/api/internal/compute/{data_model_id}/version", parse_json=True, type_=int, **kwargs
        )

    async def get_api_internal_compute_data_model_id_schema(
        self, data_model_id: str, **kwargs: Any
    ) -> ProcessDataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/{data_model_id}/schema",
            parse_json=True,
            type_=ProcessDataModelTransport,
            **kwargs,
        )

    async def get_api_internal_compute_data_model_id_pql_reference(
        self, data_model_id: str, **kwargs: Any
    ) -> PqlReferenceTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/{data_model_id}/pql-reference",
            parse_json=True,
            type_=PqlReferenceTransport,
            **kwargs,
        )

    async def get_api_internal_compute_data_model_id_full_version(
        self, data_model_id: str, **kwargs: Any
    ) -> ComputeAcceleratorVersionTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/{data_model_id}/full-version",
            parse_json=True,
            type_=ComputeAcceleratorVersionTransport,
            **kwargs,
        )

    async def get_api_internal_compute_data_model_id_data_state(
        self, data_model_id: str, **kwargs: Any
    ) -> DataStateTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/{data_model_id}/data_state",
            parse_json=True,
            type_=DataStateTransport,
            **kwargs,
        )

    async def get_api_internal_compute_export_jobs_data_model_id_export_id(
        self, data_model_id: str, export_id: str, **kwargs: Any
    ) -> DataExportStatusResponse:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/export_jobs/{data_model_id}/{export_id}",
            parse_json=True,
            type_=DataExportStatusResponse,
            **kwargs,
        )

    async def get_api_internal_compute_export_jobs_data_model_id_export_id_result(
        self, data_model_id: str, export_id: str, **kwargs: Any
    ) -> BytesIO:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/compute/export_jobs/{data_model_id}/{export_id}/result",
            parse_json=True,
            type_=BytesIO,
            **kwargs,
        )

    async def get_api_internal_capabilities(self, **kwargs: Any) -> HybridCapabilities:
        return await self.client.request(
            method="GET", url=f"/api/internal/capabilities", parse_json=True, type_=HybridCapabilities, **kwargs
        )

    async def get_api_internal_caching_cluster(self, **kwargs: Any) -> ClusterMemberState:
        return await self.client.request(
            method="GET", url=f"/api/internal/caching/cluster", parse_json=True, type_=ClusterMemberState, **kwargs
        )

    async def get_api_internal_build_info(self, **kwargs: Any) -> HybridStatusInfoResponse:
        return await self.client.request(
            method="GET", url=f"/api/internal/build-info", parse_json=True, type_=HybridStatusInfoResponse, **kwargs
        )

    async def get_api_datasource_sap_internal_systems(self, **kwargs: Any) -> List[Optional[InternalSystemTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/datasource/sap/internal-systems",
            parse_json=True,
            type_=List[Optional[InternalSystemTransport]],
            **kwargs,
        )

    async def delete_api_internal_pools_pool_id_data_models_data_model_id_tables_table_id(
        self, pool_id: str, data_model_id: str, table_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/tables/{table_id}",
            **kwargs,
        )

    async def delete_api_internal_pools_pool_id_data_models_data_model_id_foreign_keys_foreign_key_id(
        self, pool_id: str, data_model_id: str, foreign_key_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE",
            url=f"/api/internal/pools/{pool_id}/data-models/{data_model_id}/foreign-keys/{foreign_key_id}",
            **kwargs,
        )

    async def delete_api_internal_pool_provider_tenants_tenant_id(self, tenant_id: str, **kwargs: Any) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/internal/pool-provider-tenants/{tenant_id}", **kwargs
        )

    async def delete_api_internal_data_permission_group_id(self, group_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/data-permission/{group_id}", **kwargs)

    pass


class IntegrationExternalClient(IntegrationClientBase):
    pass
