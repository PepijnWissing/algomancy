"""
componentids.py - Component ID Constants

This module defines constants for all component IDs used in the dashboard application.
These IDs are used for callbacks and to reference components in the Dash application.
"""
from jinja2.nodes import Compare

# === Styling ===
GLOBAL_STYLING_STORE = "global-styling"
PAGE_CONTENT = 'page-content'

# === Home IDs ===
HOME_PAGE_CONTENT = "home-page-content"

# === Data IDs ===
DM_LIST_UPDATER_STORE = "dm-list-updater"

DATA_PAGE_CONTENT = "data-page-content"
DATA_SELECTOR_DROPDOWN = "data-selector-dropdown"

DATA_MAN_SUCCESS_ALERT = "data-man-success-alert"
DATA_MAN_ERROR_ALERT = "data-man-error-alert"

DM_DERIVE_OPEN_BTN = "dm-derive-open-btn"
DM_DERIVE_MODAL = "dm-derive-modal"
DM_DERIVE_MODAL_CLOSE_BTN = "dm-derive-modal-close-btn"
DM_DERIVE_MODAL_SUBMIT_BTN = "dm-derive-modal-submit-btn"
DM_DERIVE_SET_SELECTOR = "dm-derive-set-selector"
DM_DERIVE_SET_NAME_INPUT = "dm-derive-set-name-input"

DM_DELETE_OPEN_BUTTON = "dm-delete-open-btn"
DM_DELETE_SUBMIT_BUTTON = "DATA_MAN_DELETE_BTN"
DM_DELETE_SET_SELECTOR= "data-man-delete-selector"
DM_DELETE_CLOSE_BUTTON= "data-man-delete-close-btn"
DM_DELETE_MODAL = "data-man-delete-modal"
DM_DELETE_COLLAPSE = "data-man-delete-collapse"
DM_DELETE_CONFIRM_INPUT = "data-man-delete-confirm-input"

DM_SAVE_MODAL = "dm-save-modal"
DM_SAVE_OPEN_BUTTON = "dm-save-open-btn"
DM_SAVE_SUBMIT_BUTTON = "dm-save-submit-btn"
DM_SAVE_MODAL_CLOSE_BTN = "dm-save-modal-close-btn"
DM_SAVE_SET_SELECTOR = "dm-save-set-selector"

DM_IMPORT_MODAL = "dm-import-modal"
DM_IMPORT_OPEN_BUTTON = "dm-load-open-btn"
DM_IMPORT_UPLOADER = "dm-load-uploader"
DM_IMPORT_SUBMIT_BUTTON = "dm-load-submit-btn"
DM_IMPORT_MODAL_CLOSE_BTN = "dm-load-modal-close-btn"
DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE = "dm-load-modal-fileviewer-collapse"
DM_IMPORT_MODAL_FILEVIEWER_CARD = "dm-load-modal-fileviewer-card"
DM_IMPORT_MODAL_NAME_INPUT = "dm-load-modal-name-input"
DM_IMPORT_MODAL_FILEVIEWER_ALERT = "dm-load-modal-fileviewer-alert"

DM_UPLOAD_OPEN_BUTTON = "dm-upload-open-btn"
DM_UPLOAD_MODAL = "dm-upload-modal"
DM_UPLOAD_UPLOADER = "dm-upload-uploader"
DM_UPLOAD_SUBMIT_BUTTON = "dm-upload-submit-btn"
DM_UPLOAD_MODAL_CLOSE_BTN = "dm-upload-modal-close-btn"
DM_UPLOAD_MODAL_FILEVIEWER_CARD = "dm-upload-modal-fileviewer-card"
DM_UPLOAD_MODAL_FILEVIEWER_COLLAPSE = "dm-upload-modal-fileviewer-collapse"
DM_UPLOAD_MODAL_FILEVIEWER_ALERT = "dm-upload-modal-fileviewer-alert"
DM_UPLOAD_DATA_STORE = "dm-upload-data-store"
DM_UPLOAD_SUCCESS_ALERT = "dm-upload-success-alert"

DM_DOWNLOAD_OPEN_BUTTON = "dm-download-open-btn"
DM_DOWNLOAD_MODAL = "dm-download-modal"
DM_DOWNLOAD_CHECKLIST = "dm-download-checklist"
DM_DOWNLOAD_SUBMIT_BUTTON = "dm-download-submit-btn"
DM_DOWNLOAD_MODAL_CLOSE_BTN = "dm-download-modal-close-btn"

# === Scenario IDs ===
SCENARIO_LIST = "scenario-list"
SCENARIO_DELETE_MODAL = "delete-modal"
SCENARIO_CREATE_STATUS = "create-status"
SCENARIO_TO_DELETE = "scenario-to-delete"
SCENARIO_SELECTED = "selected-scenario"
SCENARIO_SELECTED_ID_STORE = "selected-scenario-id"

SCENARIO_CREATOR_MODAL = "scenario-creator-modal"
SCENARIO_CREATOR_OPEN_BUTTON = "scenario-creator-open-btn"

SCENARIO_NEW_BUTTON = "create-scenario-button"
SCENARIO_PROCESS_BUTTON = "scenario-process-button"
SCENARIO_DELETE_BUTTON = "scenario-delete-button"
SCENARIO_CONFIRM_DELETE_BUTTON = "scenario-confirm-delete-button"
SCENARIO_CANCEL_DELETE_BUTTON = "scenario-cancel-delete-button"

SCENARIO_STATUS_UPDATE_EVENT = "scenario-status-update-event"
SCENARIO_STATUS_BADGE = "scenario-status-badge"

SCENARIO_CARD = "scenario-card"
SCENARIO_TAG_INPUT = "scenario-tag-input"
SCENARIO_DATA_INPUT = "scenario-data-input"
SCENARIO_ALGO_INPUT = "scenario-algo-input"
SCENARIO_PARAMS_INPUT = "scenario-params-input"

SCENARIO_STATUS_SNAPSHOT = "scenario-status-snapshot"
SCENARIO_STATUS_UPDATE = "scenario-status-update"

SCENARIO_ALERT = "scenario-alert"

ALGO_PARAMS_WINDOW_ID = "algo-params-window"
ALGO_PARAMS_ENTRY_TAB = "algo-params-entry"
ALGO_PARAMS_UPLOAD_TAB = "algo-params-upload"
ALGO_PARAMS_ENTRY_CARD = "algo-params-entry-card"
ALGO_PARAM_INPUT = "algo-param-input"

SCENARIO_PROG_INTERVAL = "scenario-progress-polling-interval"
SCENARIO_PROG_BAR = "scenario-progress-bar"
SCENARIO_PROG_TEXT = "scenario-progress-text"
SCENARIO_PROG_COLLAPSE = "scenario-progress-collapse"
SCENARIO_CURRENTLY_RUNNING_STORE = "scenario-currently-running"

SCENARIO_LIST_UPDATE_STORE = "scenario-list-update-store"

# === Component IDs ===
LEFT_SCENARIO_DROPDOWN = "left-scenario-dropdown"
RIGHT_SCENARIO_DROPDOWN = "right-scenario-dropdown"

LEFT_SCENARIO_OVERVIEW = "left-scenario-overview"
RIGHT_SCENARIO_OVERVIEW = "right-scenario-overview"

KPI_IMPROVEMENT_SECTION = "kpi-improvement-section"
PERF_PRIMARY_RESULTS = "perf-primary-results"
PERF_SECONDARY_RESULTS = "perf-secondary-results"

PERF_DETAILS_COLLAPSE = "secondary-results-collapse"
LEFT_SECONDARY_RESULTS = "left-secondary-results"
RIGHT_SECONDARY_RESULTS = "right-secondary-results"

PERF_TOGGLE_CHECKLIST_LEFT = "toggle-checklist-left"
PERF_TOGGLE_CHECKLIST_RIGHT = "toggle-checklist-right"
PERF_SBS_LEFT_COLLAPSE = "perf-sbs-left-collapse"
PERF_SBS_RIGHT_COLLAPSE = "perf-sbs-right-collapse"
PERF_KPI_COLLAPSE = "perf-kpi-collapse"
PERF_COMPARE_COLLAPSE = "perf-compare-collapse"


# === Compare Page IDs ===
COMPARE_DETAIL_VIEW = "compare-detail-view"

# === Overview Page IDs ===
# OVERVIEW_TABLE = "overview-table"
# OVERVIEW_UPDATE_INTERVAL = "overview-update-interval"
OVERVIEW_PAGE_CONTENT = "overview-page-content"

# === Admin Page IDs ===
ADMIN_LOG_WINDOW = "admin-log-window"
ADMIN_LOG_INTERVAL = "admin-log-interval"
ADMIN_LOG_FILTER = "admin-log-filter"

# === Layout IDs ===
SIDEBAR = "sidebar"
SIDEBAR_TOGGLE = "sidebar-toggle"
SIDEBAR_COLLAPSED = "sidebar-collapsed"

# === Notification related ===
SCENARIO_NOTIFICATION = "scenario-notification"
SCENARIO_NOTIFICATION_STORE = "scenario-notification-store"
