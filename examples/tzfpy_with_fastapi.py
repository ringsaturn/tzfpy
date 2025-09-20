from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from tzfpy import data_version, get_tz, get_tzs, timezonenames

# lazy init
_ = get_tz(0, 0)


class TimezoneResponse(BaseModel):
    timezone: str = Field(..., description="Timezone", examples=["Asia/Tokyo"])


class TimezonesResponse(BaseModel):
    timezones: list[str] = Field(
        ..., description="Timezones", examples=[["Asia/Shanghai", "Asia/Urumqi"]]
    )


class TimezonenamesResponse(BaseModel):
    timezonenames: list[str] = Field(
        ..., description="Timezonenames", examples=[["Etc/GMT+1", "Etc/GMT+2"]]
    )


class DataVersionResponse(BaseModel):
    data_version: str = Field(..., description="Data version", examples=["2025b"])


app = FastAPI(
    title="tzfpy with FastAPI",
    description="tzfpy with FastAPI",
    contact={
        "name": "tzfpy",
        "url": "https://github.com/ringsaturn/tzfpy",
    },
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/timezone", response_model=TimezoneResponse)
def get_timezone(
    longitude: float = Query(
        ...,
        description="Longitude",
        ge=-180,
        le=180,
        examples=[139.767125],
        openapi_examples={"example-Tokyo": {"value": 139.767125}},
    ),
    latitude: float = Query(
        ...,
        description="Latitude",
        ge=-90,
        le=90,
        examples=[35.681236],
        openapi_examples={"example-Tokyo": {"value": 35.681236}},
    ),
):
    return TimezoneResponse(timezone=get_tz(longitude, latitude))


@app.get("/timezones", response_model=TimezonesResponse)
def get_timezones(
    longitude: float = Query(
        ...,
        description="Longitude",
        ge=-180,
        le=180,
        examples=[87.617733],
        openapi_examples={"example-Urumqi": {"value": 87.617733}},
    ),
    latitude: float = Query(
        ...,
        description="Latitude",
        ge=-90,
        le=90,
        examples=[43.792818],
        openapi_examples={"example-Urumqi": {"value": 43.792818}},
    ),
):
    return TimezonesResponse(timezones=get_tzs(longitude, latitude))


@app.get("/timezonenames", response_model=TimezonenamesResponse)
def get_all_timezones():
    return TimezonenamesResponse(timezonenames=timezonenames())


@app.get("/data_version", response_model=DataVersionResponse)
def get_data_version():
    return DataVersionResponse(data_version=data_version())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
