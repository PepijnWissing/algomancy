"""Data management endpoints.

Lists, fetches, deletes, derives, and (re-)ingests datasets within a single
session. The bulk-upload ETL endpoint accepts a multipart form and converts
each uploaded file into the framework's ``File`` wrapper before delegating to
``ScenarioManager.etl_data``.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from algomancy_data import CSVFile, JSONFile, XLSXFile
from algomancy_data.file import File as AlgomancyFile
from algomancy_scenario import ScenarioManager

from ..dependencies import get_scenario_manager
from ..parameter_describer import describe_parameter_set
from ..schemas import DataKeysResponse, DeriveDataRequest, EtlResponse


router = APIRouter(
    prefix="/sessions/{session_id}",
    tags=["data"],
)


_FILE_CLASS_BY_EXTENSION = {
    "csv": CSVFile,
    "json": JSONFile,
    "xlsx": XLSXFile,
}


def _build_algomancy_file(logical_name: str, on_disk_path: str) -> AlgomancyFile:
    """Wrap an on-disk uploaded file into the correct ``File`` subclass.

    The framework's extractors switch on file class (CSV/JSON/XLSX) so the
    upload route has to materialize the right subclass based on the extension.
    Unknown extensions are rejected as 400.
    """
    ext = os.path.splitext(on_disk_path)[1].lstrip(".").lower()
    file_cls = _FILE_CLASS_BY_EXTENSION.get(ext)
    if file_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension '.{ext}' for upload '{logical_name}'. "
                f"Supported: {sorted(_FILE_CLASS_BY_EXTENSION)}"
            ),
        )
    return file_cls(name=logical_name, path=on_disk_path)


@router.get(
    "/data",
    response_model=DataKeysResponse,
    summary="List dataset keys in this session",
)
def list_data(
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> DataKeysResponse:
    return DataKeysResponse(keys=list(sm.get_data_keys()))


@router.get(
    "/data/{data_key}",
    summary="Fetch a dataset's JSON representation",
)
def get_data(
    data_key: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> Dict[str, Any]:
    if data_key not in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{data_key}' not found",
        )
    # ScenarioManager hands back a JSON STRING; parse before returning so the
    # response is a proper JSON object rather than a string-encoded blob.
    return json.loads(sm.get_data_as_json(data_key))


@router.get(
    "/data/{data_key}/parameters",
    summary="Describe the dataset's declared data-parameter shape",
    response_model=dict,
)
def get_data_parameters(
    data_key: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    if data_key not in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{data_key}' not found",
        )
    params = sm.get_data_parameters(data_key)
    return describe_parameter_set(params)


@router.delete(
    "/data/{data_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset",
)
def delete_data(
    data_key: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> None:
    if data_key not in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{data_key}' not found",
        )
    # The manager asserts this dataset isn't referenced by any scenario;
    # AssertionError → 409 via the global handler.
    sm.delete_data(data_key)
    return None


@router.post(
    "/data/{data_key}/derive",
    status_code=status.HTTP_201_CREATED,
    response_model=DataKeysResponse,
    summary="Derive a new dataset from an existing one",
)
def derive_data(
    data_key: str,
    body: DeriveDataRequest,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> DataKeysResponse:
    if data_key not in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{data_key}' not found",
        )
    if body.new_key in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset '{body.new_key}' already exists",
        )
    sm.derive_data(data_key, body.new_key)
    return DataKeysResponse(keys=list(sm.get_data_keys()))


@router.post(
    "/data/from-json",
    status_code=status.HTTP_201_CREATED,
    response_model=DataKeysResponse,
    summary="Add a dataset from a JSON payload produced by DataSource.to_json()",
)
async def add_data_from_json(
    request: Request,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> DataKeysResponse:
    # The framework parses the body as a JSON string via DataSource.from_json,
    # so we forward the raw request body verbatim. This avoids re-encoding and
    # accepts either an object or array root.
    raw = await request.body()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty request body",
        )
    try:
        sm.add_datasource_from_json(raw.decode("utf-8"))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DataKeysResponse(keys=list(sm.get_data_keys()))


@router.post(
    "/etl",
    response_model=EtlResponse,
    summary="Run ETL over uploaded files into a new (or existing) dataset",
)
async def run_etl(
    dataset_name: str = Form(..., min_length=1),
    files: List[UploadFile] = File(
        ...,
        description=(
            "One file per logical name expected by the ETL factory. Each "
            "upload's filename stem becomes the logical name (e.g. "
            "'sku_data.csv' -> 'sku_data'); extension determines the File "
            "subclass (csv/json/xlsx)."
        ),
    ),
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> EtlResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file must be uploaded",
        )

    # Stage all uploads to a temp directory, then build File wrappers that the
    # ETL factory consumes. The temp dir lives only for the duration of this
    # call — the framework reads contents eagerly in the File constructor.
    # ``ignore_cleanup_errors`` covers Windows where pandas/openpyxl may hold
    # the file briefly past close.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        file_map: Dict[str, AlgomancyFile] = {}
        for upload in files:
            if not upload.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each upload must include a filename",
                )
            logical_name = os.path.splitext(upload.filename)[0]
            staged_path = os.path.join(tmpdir, upload.filename)
            with open(staged_path, "wb") as out:
                out.write(await upload.read())
            file_map[logical_name] = _build_algomancy_file(logical_name, staged_path)

        result = sm.etl_data(file_map, dataset_name)

    return EtlResponse(
        dataset_name=dataset_name,
        success=bool(result.is_success),
        keys=list(sm.get_data_keys()),
    )
