import json
import re
import urllib.parse
import urllib.request

from ..config import API

type JSONVal = str | int | JSONArray | JSONObject
type JSONArray = list[JSONVal]
type JSONObject = dict[str, JSONVal]


class InsysAPIException(Exception):
    """Raised when an error occurs trying to access the data provided by the Insys API"""


class InsysAPI:
    """
    The class containing methods for retrieving data from the FCPS Insys API.

    Must be initialized first, unless using the :func:`get_default_endpoint` method
    :param location_id: The location id of the school you want to get available courses for
    """

    DEFAULT_ENDPOINT: str = API.ENDPOINT

    def __init__(self, location_id: int, endpoint: str | None = None):
        self.location_id = location_id
        self.endpoint: str = endpoint or self.DEFAULT_ENDPOINT

    def get_course_detailed_info(self, course_id: int) -> JSONObject:
        """
        Get the detailed information of a course given the course id

        :param self: InsysAPI class instance.
        :param course_id: The course id
        :return: id, number, description, description_bold, header_note, prerequisites, corequisites.

        """
        data = self.Data(json.loads(self.__get_data(course_id=course_id)))
        course_data = self.Data(data.access("TDATA.0"))
        course = {"data": {"course": {}}}

        course["data"]["course"].update(
            {
                "id": course_id,
                "number": course_data.access("CourseNum"),
                "description": course_data.access("CourseDescription"),
                "description_bold": course_data.access("DescriptionBold"),
                "header_note": course_data.access("CourseHeaderNote"),
                "prerequisites": course_data.access("Prerequisite"),
                "corequisites": course_data.access("Corequisite"),
            }
        )

        return course

    @staticmethod
    def convert_requisites_to_id(requisite_text: str, name_to_id_dict: dict[str, int]) -> list[int]:
        """
        .. warning::
            **This is an experimental function that rarely works**

        It attempts to find corequisites or prerequisites from a course's information
        in the form of a string and then convert those requisites to course ids

        :param requisite_text: The string containing the co/prerequisite text (i.e. "Artificial Intelligence 1 & 2").
        :param name_to_id_dict: The simplified dictionary returned from :func:`course_list_to_simple`.
        :return: A list containing the converted course(s) co/prerequisite ids

        """
        remove_parentheses = r"\(.*?\)"
        cleaned_text = re.sub(remove_parentheses, "", requisite_text).replace("-", "").lower()
        index = cleaned_text.find("&")
        if index != -1:
            cleaned_text = cleaned_text[:index]
        ids = []

        for k, v in name_to_id_dict.items():
            if k.lower().find(cleaned_text) != -1:
                ids.append(v)

        return ids

    def course_list_to_simple(self, course_list: JSONObject) -> dict[str, int]:
        """
        Converts a detailed course list (from :func:`get_course_list`) to a simplified
        dictionary where the string is the course name and the int is the course id

        :param self: InsysAPI class instance.
        :param course_list: The course list returned from :func:`get_course_list`.
        :return: A simplified dictionary mapping course names to ids.

        """
        course_cat_len = len(course_list["data"]["categories"])
        simplified_dict = {}

        for i in range(course_cat_len):
            course_list_len = len(course_list["data"]["categories"][i]["courses"])
            course_list_data = self.Data(course_list["data"]["categories"][i])

            for c in range(course_list_len):
                simplified_dict.update(
                    {course_list_data.access(f"courses.{c}.name"): course_list_data.access(f"courses.{c}.id")}
                )

        return simplified_dict  # type: ignore

    def get_course_list(self) -> JSONObject:
        """
        Get a list of courses with category information

        :param self: InsysAPI class instance.

        :return: Python nested dictionary with categories and course information.
            Course properties returned: id, name, credit, weight, is_ib, is_ap, is_de, type, grades_offered

        >>> example_response = {
            {
                "data": {
                    "categories": [
                        {
                            "category_name": "Computer Science",
                            "courses": [
                                {
                                    "id": 19265
                                    ...
        >>> course = InsysAPI(location_id=503).get_course_list()["data"]["categories"][0]["courses"][0]
        >>> if course["weight"] == 1.0 and not (course["is_ap"] or course["is_de"] or course["is_ib"]):
        >>>     print("course is probably post-ap")

        """
        data = self.Data(json.loads(self.__get_data()))
        categories_len = data.access("TDATA.stCourseList.CourseGroups", True)
        courses = {"data": {"categories": []}}

        for i in range(categories_len):
            courses_len = data.access(f"TDATA.stCourseList.CourseGroups.{i}.CourseGroup.0.Courses", True)
            cat_name = data.access(f"TDATA.stCourseList.CourseGroups.{i}.CourseGroup.0.CourseGroupNav")
            courses["data"]["categories"].append(
                {
                    "category_name": cat_name,
                    "courses": [],
                }
            )
            for c in range(courses_len):
                course_data = self.Data(data.access(f"TDATA.stCourseList.CourseGroups.{i}.CourseGroup.0.Courses.{c}"))
                cat_type_code = course_data.access("Catalog_Type_Code")
                courses["data"]["categories"][i]["courses"].append(
                    {
                        "id": course_data.access("Course_ID"),
                        "name": course_data.access("CourseName"),
                        "credit": course_data.access("CourseCreditShort"),
                        "weight": self.__get_weight(str(course_data.access("CourseWeight"))),
                        "is_ib": True if course_data.access("COURSE_FLAG_IB") == "Y" else False,
                        "is_ap": True if course_data.access("COURSE_FLAG_AP") == "Y" else False,
                        "is_de": True if course_data.access("COURSE_FLAG_DE") == "Y" else False,
                        "type": "Online"
                        if cat_type_code == "OL"
                        else "Academy"
                        if cat_type_code == "AC"
                        else cat_type_code,
                        "grades_offered": self.__get_grades(course_data),
                    }
                )

        return courses

    def __get_data(self, course_id: int | None = None) -> str:
        """
        Internal function to get data from the FCPS Insys endpoint

        """
        if course_id is not None:
            payload = {
                "method": "getCourseDetail",
                "courseid": course_id,
                "LocationID": self.location_id,
                "showbus": "0",
                "CachedPOS": "1",
            }
        else:
            payload = {
                "method": "getPanelMenuData",
                "LocationID": self.location_id,
                "GradeA": "0",
                "GradeB": "0",
                "GradeC": "0",
                "pagename": "coursegroup",
                "sourceapp": "",
            }

        data = urllib.parse.urlencode(payload)
        req = urllib.request.Request(
            f"{self.endpoint}?{data}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )

        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()

            if status_code == 200:
                return self.__clean_cfc_data(response.read().decode("utf-8"))
            else:
                raise InsysAPIException(f"Invalid status code: {status_code}")

    @staticmethod
    def __clean_cfc_data(data: str) -> str:
        """
        Internal function to convert a .cfc file to a json readable one

        """
        return data[data.find("{") :]

    @staticmethod
    def __get_grades(data: "InsysAPI.Data") -> list[int]:
        """
        Internal shortcut function to calculate what offered grades a course has

        """
        grades = []
        if data.access("Grade9") == "Y":
            grades.append(9)
        if data.access("Grade10") == "Y":
            grades.append(10)
        if data.access("Grade11") == "Y":
            grades.append(11)
        if data.access("Grade12") == "Y":
            grades.append(12)
        return grades

    @staticmethod
    def __get_weight(weight_str: str) -> float:
        """
        Internal shortcut function to calculate course weighting (i.e. 0.5 for honors)

        """
        if weight_str == "":
            return 0.0
        return float(weight_str[weight_str.find("+") + 1:])

    @classmethod
    def get_default_endpoint(cls) -> str:
        """
        Get the default endpoint used when initializing this class with no endpoint parameter

        :return: The default FCPS Insys endpoint
        """
        return cls.DEFAULT_ENDPOINT

    class Data(dict):  # type: ignore
        """
        Internal class that subclasses a python dictionary, used to make data retrieval easier
        """

        def access(self, to_parse: str, length: bool = False) -> JSONObject | int:
            """
            Internal function that allows you to access python dictionaries easily using strings separated by periods

            """
            parsed = to_parse.split(".")
            keys = [int(key) if key.isnumeric() else key for key in parsed]
            data = self

            for key in keys:
                data = data[key]
            if length:
                return len(data)
            return data
