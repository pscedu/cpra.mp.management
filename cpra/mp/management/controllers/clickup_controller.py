import json

import requests as http_r

from cpra.mp.management.settings import settings


class ClickUpController:
    def __init__(self, user_token=None):
        self.settings = settings.clickup_settings
        self.app_request_headers = {
            "Content-Type": "application/json",
            "Authorization": self.settings.api_token,
        }

        self.user_request_headers = {
            "Content-Type": "application/json",
            "Authorization": user_token,
        }

    def simulation_run_create(self, simulation_run):
        task_name = f"{simulation_run.model_group} {simulation_run.scenario}"
        task_url = f"{settings.clickup_settings.base_api_url}/list/{self.settings.list_id}/taskTemplate/{self.settings.simulation_run_type_template_id_mapping[simulation_run.simulation_run_type]}"

        # The data for the task you want to create
        task_data = {"name": task_name}
        response = http_r.post(
            task_url, headers=self.app_request_headers, data=json.dumps(task_data)
        )

        # Check the response status code
        if response.status_code == 200:
            response = response.json()
            task = response.get("task", {})
            self.task_add_tags(task, [simulation_run.model_group, simulation_run.scenario])

            # Iterate through subtasks and add tags there as well.
            for subtask in task.get("subtasks", []):
                self.task_add_tags(subtask, [simulation_run.model_group, simulation_run.scenario])
        else:
            # TODO: What do we actually want to raise here?
            raise Exception(response.json())

        return task

    def task_add_tags(self, task, tags: list):
        for tag in tags:
            tags_url = f"{settings.clickup_settings.base_api_url}/task/{task.get('id')}/tag/{tag}"
            response = http_r.post(
                tags_url, headers=self.app_request_headers, data=json.dumps(task)
            )
            if response.status_code != 200:
                raise Exception(response.json())

    def task_create(self, task_data: dict):
        # Make the POST request to create the task
        task_url = f"{settings.clickup_settings.base_api_url}/list/{self.settings.list_id}/task"
        response = http_r.post(
            task_url, headers=self.app_request_headers, data=json.dumps(task_data)
        )

        if response.status_code == 200:
            task = response.json()
        else:
            raise Exception(response.json())

        return task

    def task_delete(self, clickup_id):
        # Set an archive tag on the task and its children task?
        # Don't need to set this tag on tasks that aren't part of the template.
        task_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}"
        response = http_r.delete(task_url, headers=self.app_request_headers)
        if response.status_code != 204:
            raise Exception(response.content)

    def task_get(self, clickup_id, include_subtasks=False):
        task_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}?{'include_subtasks=true' if include_subtasks else ''}"
        response = http_r.get(task_url, headers=self.app_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()

    def task_bulk_get(self, params: dict):
        task_url = f"{settings.clickup_settings.base_api_url}/list/{self.settings.list_id}/task"
        response = http_r.get(task_url, headers=self.app_request_headers, params=params)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["tasks"]

    def task_update(self, clickup_id, data_to_update: dict):
        task_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}"
        response = http_r.put(
            task_url, headers=self.app_request_headers, data=json.dumps(data_to_update)
        )
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()
