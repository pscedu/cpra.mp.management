import requests as http_r
import json
from cpra.mp.management.settings import settings


class ClickUpController:
    def __init__(self, user_token=None):
        self.settings = settings.clickup_settings
        self.app_request_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.settings.api_token
        }

        self.user_request_headers = {
            'Content-Type': 'application/json',
            'Authorization': user_token
        }

    def simulation_run_create(self, simulation_run):
        task_name = f"{simulation_run.model_group} {simulation_run.scenario}"
        task_url = f"{settings.clickup_settings.base_api_url}/list/{self.settings.list_id}/taskTemplate/{self.settings.simulation_run_type_template_id_mapping[simulation_run.simulation_run_type]}"

        # The data for the task you want to create
        task_data = {
            'name': task_name
        }

        # Make the POST request to create the task
        response = http_r.post(task_url, headers=self.app_request_headers, data=json.dumps(task_data))

        # Check the response status code
        if response.status_code == 200:
            response = response.json()
            task = response.get('task', {})
            self.task_add_tags(task, [simulation_run.model_group, simulation_run.scenario])

            # Iterate through subtasks and add tags there as well.
            for subtask in task.get('subtasks', []):
                self.task_add_tags(subtask, [simulation_run.model_group, simulation_run.scenario])
        else:
            # TODO: What do we actually want to raise here?
            raise Exception(response.json())

        return task

    def task_add_tags(self, task, tags: list):
        for tag in tags:
            tags_url = f"{settings.clickup_settings.base_api_url}/task/{task.get('id')}/tag/{tag}"
            response = http_r.post(tags_url, headers=self.app_request_headers, data=json.dumps(task))
            if response.status_code != 200:
                raise Exception(response.json())


    def simulation_run_delete(self, simulation_run):
        # Set an archive tag on the task and its children task?
        # Don't need to set this tag on tasks that aren't part of the template.
        task_url = f"{settings.clickup_settings.base_api_url}/task/{simulation_run.clickup_id}"
        response = http_r.delete(task_url, headers=self.app_request_headers)
        if response.status_code != 204:
            raise Exception(response.content)

    def simulation_run_get(self, simulation_run):
        task_url = f"{settings.clickup_settings.base_api_url}/task/{simulation_run.clickup_id}?include_subtasks=true"
        response = http_r.get(task_url, headers=self.app_request_headers)
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()

    def simulation_run_update(self, simulation_run, status):
        task_url = f"{settings.clickup_settings.base_api_url}/task/{simulation_run.clickup_id}"
        body = {"status": status}
        response = http_r.put(task_url, headers=self.app_request_headers, data=json.dumps(body))
        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()
