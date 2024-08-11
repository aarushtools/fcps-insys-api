import json

from fastapi import APIRouter
from starlette.responses import JSONResponse

from ...config import API
from ...utils.main import InsysAPI

courses_router = APIRouter(prefix=API.COURSES.URL)

insys_api = InsysAPI(location_id=API.COURSES.LOCATION_ID)


@courses_router.get("/", status_code=200)
def course_list():
    return JSONResponse(content=insys_api.get_course_list())


@courses_router.get("/course/", status_code=200)
def course_detailed_info(course_id: int):
    return JSONResponse(content=insys_api.get_course_detailed_info(course_id))
