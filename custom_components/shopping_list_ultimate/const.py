"""Constants for Shopping List Ultimate."""

DOMAIN = "shopping_list_ultimate"
VERSION = "0.1.1"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.products"

CONF_TODO_ENTITY = "todo_entity"
CONF_COUNTRY = "country"
CONF_LANGUAGE = "language"
CONF_USE_IMAGES = "use_images"
CONF_AUTO_ADD = "auto_add"
CONF_STORE_UNKNOWN = "store_unknown"
CONF_MERGE_DUPLICATES = "merge_duplicates"

DEFAULT_COUNTRY = "nl"
DEFAULT_LANGUAGE = "nl"

EVENT_BARCODE_SCANNED = f"{DOMAIN}_barcode_scanned"

SERVICE_LOOKUP_BARCODE = "lookup_barcode"
SERVICE_ADD_BARCODE = "add_barcode"
SERVICE_ADD_PRODUCT = "add_product"
SERVICE_UPDATE_PRODUCT = "update_product"
SERVICE_DELETE_PRODUCT = "delete_product"
SERVICE_REFRESH_PRODUCT = "refresh_product"
