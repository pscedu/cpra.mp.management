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
            "Authorization": f"Bearer {user_token}",
        }

    def simulation_run_create(self, simulation_run):
        task_name = f"{simulation_run.model_group_id} {simulation_run.scenario_id}"
        list_id = self.settings.list_ids["simulation_runs"]
        task_url = f"{settings.clickup_settings.base_api_url}/list/{list_id}/taskTemplate/{self.settings.simulation_run_type_template_id_mapping[simulation_run.simulation_run_type]}"

        # The data for the task you want to create
        task_data = {"name": task_name}
        response = http_r.post(
            task_url, headers=self.app_request_headers, data=json.dumps(task_data)
        )

        # Check the response status code
        if response.status_code == 200:
            response = response.json()
            task = response.get("task", {})
            self.task_add_tags(
                task,
                [
                    f"model_group_id:{simulation_run.model_group_id}",
                    f"scenario_id:{simulation_run.scenario_id}",
                    "meta_type:simulation_run",
                ],
            )

            # Iterate through subtasks and add tags there as well.
            for subtask in task.get("subtasks", []):
                self.task_add_tags(
                    subtask,
                    [
                        f"model_group_id:{simulation_run.model_group_id}",
                        f"scenario_id:{simulation_run.scenario_id}",
                        "meta_type:subroutine",
                    ],
                )
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
        list_id = self.settings.list_ids["tasks"]
        task_url = f"{settings.clickup_settings.base_api_url}/list/{list_id}/task"
        response = http_r.post(
            task_url, headers=self.user_request_headers, data=json.dumps(task_data)
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
        list_id = self.settings.list_ids["tasks"]
        task_url = f"{settings.clickup_settings.base_api_url}/list/{list_id}/task"
        response = http_r.get(task_url, headers=self.app_request_headers, params=params)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["tasks"]

    def task_update(self, clickup_id, data_to_update: dict):
        task_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}"
        response = http_r.put(
            task_url, headers=self.user_request_headers, data=json.dumps(data_to_update)
        )
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()

    def task_get_comments(self, clickup_id):
        comment_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}/comment"
        response = http_r.get(comment_url, headers=self.app_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["comments"]

    def task_create_comment(self, clickup_id, comment_data):
        comment_url = f"{settings.clickup_settings.base_api_url}/task/{clickup_id}/comment"
        response = http_r.post(comment_url, json=comment_data, headers=self.user_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()

    def comment_update(self, clickup_id, data_to_update: dict):
        comment_url = f"{settings.clickup_settings.base_api_url}/comment/{clickup_id}"
        response = http_r.put(comment_url, json=data_to_update, headers=self.user_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

    def comment_delete(self, clickup_id):
        comment_url = f"{settings.clickup_settings.base_api_url}/comment/{clickup_id}"
        response = http_r.delete(comment_url, headers=self.app_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

    def comment_get_replies(self, clickup_id):
        comment_url = f"{settings.clickup_settings.base_api_url}/comment/{clickup_id}/reply"
        response = http_r.get(comment_url, headers=self.app_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["comments"]

    def comment_create_reply(self, clickup_id, comment_data):
        comment_url = f"{settings.clickup_settings.base_api_url}/comment/{clickup_id}/reply"
        response = http_r.post(comment_url, json=comment_data, headers=self.user_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()

    def status_bulk_get(self):
        statuses = {}
        for list_type, list_id in self.settings.list_ids.items():
            list_url = f"{settings.clickup_settings.base_api_url}/list/{list_id}"
            response = http_r.get(list_url, headers=self.app_request_headers)
            if response.status_code != 200:
                raise Exception(response.json())

            statuses[list_type] = [status.get("status") for status in response.json().get("statuses", [])]

        return statuses
